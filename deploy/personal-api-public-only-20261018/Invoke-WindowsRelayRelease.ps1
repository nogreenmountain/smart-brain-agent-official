[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('Prepare', 'Apply', 'Rollback')]
    [string]$Action,

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$InstallDir,

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$StateDir,

    [string]$CandidateDir = $PSScriptRoot,
    [string]$ReleaseId = 'personal-api-public-only-20261018-r1',
    [string]$ConfirmReleaseId,
    [ValidateRange(10, 1800)][int]$DrainTimeoutSeconds = 300,
    [ValidateRange(1, 30)][int]$DrainPollSeconds = 2,
    [ValidateRange(10, 60)][int]$WatchdogPollSeconds = 10
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Set-StrictMode -Version Latest

Import-Module (Join-Path $PSScriptRoot 'WindowsRelayRelease.psm1') -Force

$WatchdogTaskName = 'CLIProxyAPI2Services'
$ExpectedCandidateProxySha256 = '8EE401EB7169347F4308A29C3C942121E0F9CE10479EB240E9C0A286607A208C'
$ExpectedCandidateStartSha256 = 'AE95AC240D24BA695F24FEE0105F1E1EC6B5177ECB52D0D74C39E73737E6A2E6'
$StatePath = Join-Path $StateDir 'release-state.json'
$FirewallPath = Join-Path $StateDir 'firewall-before.json'
$TaskXmlPath = Join-Path $StateDir 'watchdog-before.xml'
$BackupDir = Join-Path $StateDir 'backup'

function Get-Sha256 {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-TextSha256 {
    param([Parameter(Mandatory)][string]$Text)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        return (($algorithm.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '').ToUpperInvariant()
    } finally {
        $algorithm.Dispose()
    }
}

function Write-JsonAtomic {
    param([Parameter(Mandatory)]$Value, [Parameter(Mandatory)][string]$Path)
    $temporary = "$Path.new"
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $temporary -Encoding UTF8
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Set-StateValue {
    param([Parameter(Mandatory)]$State, [Parameter(Mandatory)][string]$Name, [AllowNull()]$Value)
    $State | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
    Write-JsonAtomic -Value $State -Path $StatePath
}

function Read-ReleaseState {
    if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) { throw "Release state is missing: $StatePath" }
    $state = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
    if ($state.ReleaseId -cne $ReleaseId) { throw 'Release state identity does not match this release' }
    return $state
}

function Get-ListenerIdentity {
    param([Parameter(Mandatory)][int]$Port)
    $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    if ($listeners.Count -ne 1) { throw "Expected one listener on TCP/$Port; found $($listeners.Count)" }
    $pidValue = [int]$listeners[0].OwningProcess
    $process = Get-Process -Id $pidValue -ErrorAction Stop
    return [pscustomobject]@{
        Pid = $pidValue
        StartTimeUtc = $process.StartTime.ToUniversalTime().ToString('o')
        ProcessName = $process.ProcessName
        LocalAddress = [string]$listeners[0].LocalAddress
    }
}

function Assert-BackendLoopbackOnly {
    $listeners = @(Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue)
    if ($listeners.Count -ne 1 -or [string]$listeners[0].LocalAddress -ne '127.0.0.1') {
        throw 'TCP/3000 must have exactly one listener bound to 127.0.0.1'
    }
    return Get-ListenerIdentity -Port 3000
}

function Get-RelayFirewallRecords {
    $records = [System.Collections.Generic.List[object]]::new()
    $rules = @(Get-NetFirewallRule -PolicyStore ActiveStore -ErrorAction Stop | Where-Object {
        [string]$_.Direction -eq 'Inbound' -and [string]$_.Action -eq 'Allow'
    })
    foreach ($rule in $rules) {
        $port = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $rule -ErrorAction Stop
        $address = Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $rule -ErrorAction Stop
        $application = Get-NetFirewallApplicationFilter -AssociatedNetFirewallRule $rule -ErrorAction Stop
        $records.Add([pscustomobject]@{
            InstanceId = [string]$rule.InstanceID
            Name = [string]$rule.Name
            DisplayName = [string]$rule.DisplayName
            Description = [string]$rule.Description
            Enabled = [string]$rule.Enabled
            Direction = [string]$rule.Direction
            Action = [string]$rule.Action
            Profile = [string]$rule.Profile
            PolicyStoreSource = [string]$rule.PolicyStoreSource
            PolicyStoreSourceType = [string]$rule.PolicyStoreSourceType
            Protocol = (@($port.Protocol) | ForEach-Object { [string]$_ }) -join ','
            LocalPort = (@($port.LocalPort) | ForEach-Object { [string]$_ }) -join ','
            RemoteAddress = (@($address.RemoteAddress) | ForEach-Object { [string]$_ }) -join ','
            Program = (@($application.Program) | ForEach-Object { [string]$_ }) -join ','
        })
    }
    return @($records)
}

function Get-FirewallProfilesSafe {
    return @(Get-NetFirewallProfile -PolicyStore ActiveStore -ErrorAction Stop | ForEach-Object {
        [pscustomobject]@{
            Name = [string]$_.Name
            Enabled = [bool]$_.Enabled
            DefaultInboundAction = [string]$_.DefaultInboundAction
        }
    })
}

function Get-CurrentWatchdogState {
    $task = Get-ScheduledTask -TaskName $WatchdogTaskName -ErrorAction Stop
    return [pscustomobject]@{
        TaskName = $WatchdogTaskName
        Enabled = [bool]$task.Settings.Enabled
        State = [string]$task.State
    }
}

function Stop-WatchdogForRelease {
    Disable-ScheduledTask -TaskName $WatchdogTaskName -ErrorAction Stop | Out-Null
    Stop-ScheduledTask -TaskName $WatchdogTaskName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
    $task = Get-ScheduledTask -TaskName $WatchdogTaskName -ErrorAction Stop
    if ([bool]$task.Settings.Enabled -or [string]$task.State -eq 'Running') {
        throw 'Watchdog did not stop and disable cleanly'
    }
}

function Restore-WatchdogState {
    param([Parameter(Mandatory)]$Original)
    Stop-ScheduledTask -TaskName $WatchdogTaskName -ErrorAction SilentlyContinue
    if ([bool]$Original.Enabled) {
        Enable-ScheduledTask -TaskName $WatchdogTaskName -ErrorAction Stop | Out-Null
        if ([string]$Original.State -eq 'Running') {
            Start-ScheduledTask -TaskName $WatchdogTaskName -ErrorAction Stop
        }
    } else {
        Disable-ScheduledTask -TaskName $WatchdogTaskName -ErrorAction Stop | Out-Null
    }
}

function Wait-RelayConnectionsDrained {
    $script:IdleDrainEvidence = $null
    $deadline = (Get-Date).AddSeconds($DrainTimeoutSeconds)
    $samples = [System.Collections.Generic.List[int]]::new()
    while ((Get-Date) -lt $deadline) {
        $connections = @(Get-NetTCPConnection -LocalPort 9000 -State Established -ErrorAction SilentlyContinue)
        $count = $connections.Count
        $samples.Add($count)
        if (Test-RelayDrainSamples -EstablishedCounts @($samples)) { return }
        if ($count -eq 1 -and $connections[0].RemoteAddress -eq '192.168.10.165' -and
            @(Get-NetTCPConnection -LocalPort 3000 -State Established -ErrorAction SilentlyContinue).Count -eq 0) {
            try {
                $first = Get-IdleRelayProbe
                Start-Sleep -Seconds 10
                $second = Get-IdleRelayProbe
                if (Test-IdleRelayProof -First $first -Second $second -RemotePort $connections[0].RemotePort) {
                    $script:IdleDrainEvidence = [pscustomobject]@{ First=$first; Second=$second; RemotePort=$connections[0].RemotePort; OwningProcess=$connections[0].OwningProcess }
                    Assert-NoRelayConnections
                    return
                }
            } catch { $script:IdleDrainEvidence = $null }
        }
        Start-Sleep -Seconds $DrainPollSeconds
    }
    throw "TCP/9000 connections did not drain within $DrainTimeoutSeconds seconds"
}

function Assert-NoRelayConnections {
    $connections = @(Get-NetTCPConnection -LocalPort 9000 -State Established -ErrorAction SilentlyContinue)
    $count = $connections.Count
    if ($count -eq 1 -and $script:IdleDrainEvidence -and
        $connections[0].RemoteAddress -eq '192.168.10.165' -and
        $connections[0].RemotePort -eq $script:IdleDrainEvidence.RemotePort -and
        $connections[0].OwningProcess -eq $script:IdleDrainEvidence.OwningProcess -and
        @(Get-NetTCPConnection -LocalPort 3000 -State Established -ErrorAction SilentlyContinue).Count -eq 0) {
        $latest = Get-IdleRelayProbe
        if (Test-IdleRelayProof -First $script:IdleDrainEvidence.First -Second $latest -RemotePort $connections[0].RemotePort) { return }
    }
    if ($count -ne 0) { throw "TCP/9000 accepted $count new connection(s) after the drain gate" }
}

function Get-IdleRelayProbe {
    $raw = & 'C:\Users\test\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' (Join-Path $PSScriptRoot 'inspect_idle_relay.py')
    if ($LASTEXITCODE -ne 0) { throw 'Remote idle connection proof unavailable' }
    return ($raw | ConvertFrom-Json)
}

function Stop-ExactRelayOnce {
    param([Parameter(Mandatory)]$Expected)
    $actual = Get-ListenerIdentity -Port 9000
    Confirm-RelayRuntimeIdentity -Expected $Expected -Actual $actual | Out-Null
    Stop-Process -Id ([int]$Expected.Pid) -ErrorAction Stop
    $deadline = (Get-Date).AddSeconds(20)
    while ((Get-Date) -lt $deadline -and (Get-Process -Id ([int]$Expected.Pid) -ErrorAction SilentlyContinue)) {
        Start-Sleep -Milliseconds 250
    }
    if (Get-Process -Id ([int]$Expected.Pid) -ErrorAction SilentlyContinue) {
        throw 'The exact relay PID did not stop; refusing a second stop attempt'
    }
}

function Install-AtomicFile {
    param([Parameter(Mandatory)][string]$Source, [Parameter(Mandatory)][string]$Destination)
    $temporary = "$Destination.$ReleaseId.$([guid]::NewGuid().ToString('N')).new"
    $replaced = "$Destination.$ReleaseId.$([guid]::NewGuid().ToString('N')).replaced"
    try {
        Copy-Item -LiteralPath $Source -Destination $temporary
        if ((Get-Sha256 $Source) -cne (Get-Sha256 $temporary)) { throw "Staged replacement hash mismatch: $Destination" }
        [System.IO.File]::Replace($temporary, $Destination, $replaced)
    } finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) { Remove-Item -LiteralPath $temporary -Force }
        if (Test-Path -LiteralPath $replaced -PathType Leaf) { Remove-Item -LiteralPath $replaced -Force }
    }
}

function Start-RelayOnce {
    param([Parameter(Mandatory)][string]$StartScript)
    foreach ($logName in @('proxy_task_stdout.log','proxy_task_stderr.log')) {
        $logPath = Join-Path $InstallDir $logName
        if (Test-Path -LiteralPath $logPath -PathType Leaf) {
            $savedLog = Join-Path $BackupDir (([guid]::NewGuid().ToString('N')) + '-' + $logName)
            Copy-Item -LiteralPath $logPath -Destination $savedLog -ErrorAction Stop
            if ((Get-Sha256 $logPath) -cne (Get-Sha256 $savedLog)) { throw 'Stopped relay log changed while preserving it' }
        }
    }
    $process = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"{0}"' -f $StartScript)
    ) -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -ne 0) { throw "start-services.ps1 failed with exit code $($process.ExitCode)" }
}

function Assert-ExactAllowRule {
    param([Parameter(Mandatory)]$PlanStep)
    $rule = Get-NetFirewallRule -Name $PlanStep.Name -ErrorAction Stop
    $port = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $rule -ErrorAction Stop
    $address = Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $rule -ErrorAction Stop
    if (
        [string]$rule.Enabled -ne 'True' -or [string]$rule.Direction -ne 'Inbound' -or [string]$rule.Action -ne 'Allow' -or
        [string]$port.Protocol -notin @('TCP', '6') -or [string]$port.LocalPort -ne '9000' -or
        ((@($address.LocalAddress) | ForEach-Object { [string]$_ }) -join ',') -ne '192.168.10.146' -or
        ((@($address.RemoteAddress) | ForEach-Object { [string]$_ }) -join ',') -ne '192.168.10.165'
    ) { throw 'The exact Windows firewall allow rule did not read back as reviewed' }
}

function Apply-FirewallRestriction {
    param([Parameter(Mandatory)]$State)
    $profiles = Get-FirewallProfilesSafe
    $rules = Get-RelayFirewallRecords
    $plan = @(Get-RelayFirewallPlan -Profiles $profiles -Rules $rules -ReleaseId $ReleaseId)
    $expectedIds = @($State.Firewall.BroadRules | ForEach-Object { [string]$_.InstanceId } | Sort-Object)
    $actualIds = @($plan | Where-Object Operation -eq 'DisableBroadRule' | ForEach-Object { [string]$_.InstanceId } | Sort-Object)
    if (($expectedIds -join '|') -cne ($actualIds -join '|')) { throw 'Reviewed broad firewall rule identities changed after prepare' }
    $currentBroadRules = @($rules | Where-Object { [string]$_.InstanceId -in $actualIds })
    if (@($currentBroadRules | Where-Object { [string]$_.PolicyStoreSourceType -ne 'Local' }).Count -gt 0) {
        throw 'A reviewed broad firewall rule is no longer locally owned'
    }

    $exact = $plan[0]
    if (Get-NetFirewallRule -Name $exact.Name -PolicyStore ActiveStore -ErrorAction SilentlyContinue) {
        throw 'The exact release firewall rule already exists; refusing to adopt it'
    }
    New-NetFirewallRule -Name $exact.Name -DisplayName $exact.DisplayName -Description "Owned by $ReleaseId; rollback removes this exact rule" `
        -Group $exact.Group -Direction Inbound -Action Allow -Enabled True -Profile Any -Protocol TCP `
        -LocalAddress $exact.LocalAddress -LocalPort $exact.LocalPort -RemoteAddress $exact.RemoteAddress | Out-Null
    Set-StateValue -State $State -Name 'ExactFirewallRuleCreated' -Value $true
    Assert-ExactAllowRule -PlanStep $exact

    foreach ($step in @($plan | Where-Object Operation -eq 'DisableBroadRule')) {
        $rule = Get-NetFirewallRule -Name $step.Name -ErrorAction Stop
        if ([string]$rule.InstanceID -cne [string]$step.InstanceId -or [string]$rule.Enabled -ne 'True') {
            throw "Broad firewall rule drifted before disable: $($step.DisplayName)"
        }
        $rule | Disable-NetFirewallRule -ErrorAction Stop | Out-Null
    }
    Assert-ExactAllowRule -PlanStep $exact
}

function Restore-FirewallSnapshot {
    param([Parameter(Mandatory)]$State)
    foreach ($saved in @($State.Firewall.BroadRules)) {
        $rule = Get-NetFirewallRule -Name ([string]$saved.Name) -ErrorAction Stop
        if ([string]$rule.InstanceID -cne [string]$saved.InstanceId) {
            throw "Cannot restore changed firewall rule identity: $($saved.DisplayName)"
        }
        if ([string]$saved.Enabled -eq 'True') {
            $rule | Enable-NetFirewallRule -ErrorAction Stop | Out-Null
        } else {
            $rule | Disable-NetFirewallRule -ErrorAction Stop | Out-Null
        }
    }
    $owned = Get-NetFirewallRule -Name ([string]$State.Firewall.ExactRuleName) -ErrorAction SilentlyContinue
    if ($owned) {
        if ([string]$owned.Group -cne 'SmartBrain Personal API Public Only' -or [string]$owned.Description -cne "Owned by $ReleaseId; rollback removes this exact rule") {
            throw 'Exact firewall rule ownership changed; refusing to remove it'
        }
        $owned | Remove-NetFirewallRule -ErrorAction Stop
    }
}

function Restore-RelayRelease {
    param([Parameter(Mandatory)]$State)
    if ((Get-Sha256 (Join-Path $BackupDir 'proxy-server.js')) -cne [string]$State.Files.ProxyBackupSha256 -or
        (Get-Sha256 (Join-Path $BackupDir 'start-services.ps1')) -cne [string]$State.Files.StartBackupSha256) {
        throw 'Prepared rollback files failed their recorded hash checks'
    }
    Stop-WatchdogForRelease
    $listener = $null
    $listeners = @(Get-NetTCPConnection -LocalPort 9000 -State Listen -ErrorAction SilentlyContinue)
    if ($listeners.Count -gt 0) { $listener = Get-ListenerIdentity -Port 9000 }
    $mustRestart = $false
    if ($listener) {
        $isOriginal = ([int]$listener.Pid -eq [int]$State.RuntimeBefore.Relay.Pid -and
            [string]$listener.StartTimeUtc -ceq [string]$State.RuntimeBefore.Relay.StartTimeUtc)
        if ($isOriginal) {
            Confirm-RelayRuntimeIdentity -Expected $State.RuntimeBefore.Relay -Actual $listener | Out-Null
        } else {
            if (-not $State.PSObject.Properties['RuntimeAfter']) { throw 'Unrecorded relay identity; refusing rollback process stop' }
            Confirm-RelayRuntimeIdentity -Expected $State.RuntimeAfter -Actual $listener | Out-Null
            Wait-RelayConnectionsDrained
            Assert-NoRelayConnections
            Stop-ExactRelayOnce -Expected $State.RuntimeAfter
            $mustRestart = $true
        }
    } elseif (-not $listener) {
        if (Get-Process -Id ([int]$State.RuntimeBefore.Relay.Pid) -ErrorAction SilentlyContinue) { throw 'Original relay process exists without listener; refusing duplicate start' }
        $mustRestart = $true
    }

    if ((Get-Sha256 (Join-Path $InstallDir 'proxy-server.js')) -cne [string]$State.Files.ProxyBeforeSha256) {
        Install-AtomicFile -Source (Join-Path $BackupDir 'proxy-server.js') -Destination (Join-Path $InstallDir 'proxy-server.js')
    }
    if ((Get-Sha256 (Join-Path $InstallDir 'start-services.ps1')) -cne [string]$State.Files.StartBeforeSha256) {
        Install-AtomicFile -Source (Join-Path $BackupDir 'start-services.ps1') -Destination (Join-Path $InstallDir 'start-services.ps1')
    }
    if ((Get-Sha256 (Join-Path $InstallDir 'proxy-server.js')) -cne [string]$State.Files.ProxyBeforeSha256 -or
        (Get-Sha256 (Join-Path $InstallDir 'start-services.ps1')) -cne [string]$State.Files.StartBeforeSha256) {
        throw 'Rollback file hashes do not match the prepared backup'
    }
    Restore-FirewallSnapshot -State $State
    if ($mustRestart) { Start-RelayOnce -StartScript (Join-Path $InstallDir 'start-services.ps1') }
    Restore-WatchdogState -Original $State.WatchdogBefore
    Assert-BackendLoopbackOnly | Out-Null
    Get-ListenerIdentity -Port 9000 | Out-Null
    Set-StateValue -State $State -Name 'Stage' -Value 'Restored'
}

function Invoke-Prepare {
    if (Test-Path -LiteralPath $StateDir) { throw "StateDir already exists; use a new release state directory: $StateDir" }
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

    $installedProxy = Join-Path $InstallDir 'proxy-server.js'
    $installedStart = Join-Path $InstallDir 'start-services.ps1'
    $candidateProxy = Join-Path $CandidateDir 'proxy-server.js'
    $candidateStart = Join-Path $CandidateDir 'start-services.ps1'
    foreach ($path in @($installedProxy, $installedStart, $candidateProxy, $candidateStart)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required file is missing: $path" }
    }
    if ((Get-Sha256 $candidateProxy) -cne $ExpectedCandidateProxySha256 -or (Get-Sha256 $candidateStart) -cne $ExpectedCandidateStartSha256) {
        throw 'Candidate file hash does not match the reviewed public-only package'
    }

    $relay = Get-ListenerIdentity -Port 9000
    if ($relay.ProcessName -cne 'node') { throw 'TCP/9000 is not owned by the reviewed node relay' }
    $backend = Assert-BackendLoopbackOnly
    $watchdog = Get-CurrentWatchdogState
    $profiles = Get-FirewallProfilesSafe
    $rules = Get-RelayFirewallRecords
    $plan = @(Get-RelayFirewallPlan -Profiles $profiles -Rules $rules -ReleaseId $ReleaseId)
    $exact = $plan[0]
    $broadRules = @($rules | Where-Object { [string]$_.InstanceId -in @($plan | Where-Object Operation -eq 'DisableBroadRule' | ForEach-Object InstanceId) })
    $nonLocalRules = @($broadRules | Where-Object { [string]$_.PolicyStoreSourceType -ne 'Local' })
    if ($nonLocalRules.Count -gt 0) { throw 'A reviewed broad firewall rule is not locally owned and cannot be safely restored' }
    if (Get-NetFirewallRule -Name $exact.Name -PolicyStore ActiveStore -ErrorAction SilentlyContinue) {
        throw 'The exact release firewall rule already exists before prepare'
    }

    Copy-Item -LiteralPath $installedProxy -Destination (Join-Path $BackupDir 'proxy-server.js')
    Copy-Item -LiteralPath $installedStart -Destination (Join-Path $BackupDir 'start-services.ps1')
    $taskXml = Export-ScheduledTask -TaskName $WatchdogTaskName -ErrorAction Stop
    $taskXml | Set-Content -LiteralPath $TaskXmlPath -Encoding Unicode
    [pscustomobject]@{ Profiles=$profiles; BroadRules=$broadRules; ExactRuleName=$exact.Name } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $FirewallPath -Encoding UTF8

    $state = [pscustomobject]@{
        Schema = 1
        ReleaseId = $ReleaseId
        Stage = 'Prepared'
        PreparedAt = (Get-Date).ToUniversalTime().ToString('o')
        Privacy = 'No Key, bearer value, request body, response body, environment block, or process command line is read or recorded.'
        InstallDir = (Resolve-Path -LiteralPath $InstallDir).Path
        CandidateDir = (Resolve-Path -LiteralPath $CandidateDir).Path
        Files = [pscustomobject]@{
            ProxyBeforeSha256 = Get-Sha256 $installedProxy
            StartBeforeSha256 = Get-Sha256 $installedStart
            ProxyCandidateSha256 = Get-Sha256 $candidateProxy
            StartCandidateSha256 = Get-Sha256 $candidateStart
            ProxyBackupSha256 = Get-Sha256 (Join-Path $BackupDir 'proxy-server.js')
            StartBackupSha256 = Get-Sha256 (Join-Path $BackupDir 'start-services.ps1')
        }
        RuntimeBefore = [pscustomobject]@{ Relay=$relay; Backend=$backend }
        WatchdogBefore = $watchdog
        WatchdogDefinitionSha256 = Get-TextSha256 $taskXml
        Firewall = [pscustomobject]@{ Profiles=$profiles; BroadRules=$broadRules; ExactRuleName=$exact.Name }
        ExactFirewallRuleCreated = $false
    }
    Write-JsonAtomic -Value $state -Path $StatePath
    Write-Output "Prepared $ReleaseId. Review $StatePath before Apply. No service, process, listener, or firewall state was changed."
}

function Invoke-Apply {
    if ($ConfirmReleaseId -cne $ReleaseId) { throw 'Apply requires -ConfirmReleaseId exactly matching the release identity' }
    $state = Read-ReleaseState
    if ([string]$state.Stage -cne 'Prepared') { throw "Apply requires Prepared state; found $($state.Stage)" }
    if ((Resolve-Path -LiteralPath $InstallDir).Path -cne [string]$state.InstallDir -or (Resolve-Path -LiteralPath $CandidateDir).Path -cne [string]$state.CandidateDir) {
        throw 'InstallDir or CandidateDir changed after prepare'
    }
    $installedProxy = Join-Path $InstallDir 'proxy-server.js'
    $installedStart = Join-Path $InstallDir 'start-services.ps1'
    $candidateProxy = Join-Path $CandidateDir 'proxy-server.js'
    $candidateStart = Join-Path $CandidateDir 'start-services.ps1'
    if ((Get-Sha256 $installedProxy) -cne [string]$state.Files.ProxyBeforeSha256 -or (Get-Sha256 $installedStart) -cne [string]$state.Files.StartBeforeSha256) {
        throw 'Installed scripts changed after prepare'
    }
    if ((Get-Sha256 (Join-Path $BackupDir 'proxy-server.js')) -cne [string]$state.Files.ProxyBackupSha256 -or
        (Get-Sha256 (Join-Path $BackupDir 'start-services.ps1')) -cne [string]$state.Files.StartBackupSha256) {
        throw 'Prepared rollback files changed after prepare'
    }
    if ((Get-Sha256 $candidateProxy) -cne [string]$state.Files.ProxyCandidateSha256 -or (Get-Sha256 $candidateStart) -cne [string]$state.Files.StartCandidateSha256) {
        throw 'Candidate scripts changed after prepare'
    }
    Confirm-RelayRuntimeIdentity -Expected $state.RuntimeBefore.Relay -Actual (Get-ListenerIdentity -Port 9000) | Out-Null
    Confirm-RelayRuntimeIdentity -Expected $state.RuntimeBefore.Backend -Actual (Assert-BackendLoopbackOnly) | Out-Null
    $watchdogNow = Get-CurrentWatchdogState
    if ([bool]$watchdogNow.Enabled -ne [bool]$state.WatchdogBefore.Enabled -or [string]$watchdogNow.State -cne [string]$state.WatchdogBefore.State) {
        throw 'Watchdog state changed after prepare'
    }
    if ((Get-TextSha256 (Export-ScheduledTask -TaskName $WatchdogTaskName -ErrorAction Stop)) -cne [string]$state.WatchdogDefinitionSha256) {
        throw 'Watchdog task definition changed after prepare'
    }

    try {
        Apply-FirewallRestriction -State $state
        Set-StateValue -State $state -Name 'Stage' -Value 'FirewallRestricted'
        Stop-WatchdogForRelease
        Set-StateValue -State $state -Name 'Stage' -Value 'WatchdogStopped'
        Wait-RelayConnectionsDrained
        if ($script:IdleDrainEvidence) { Set-StateValue -State $state -Name 'IdleDrainEvidence' -Value $script:IdleDrainEvidence }
        Confirm-RelayRuntimeIdentity -Expected $state.RuntimeBefore.Relay -Actual (Get-ListenerIdentity -Port 9000) | Out-Null
        Confirm-RelayRuntimeIdentity -Expected $state.RuntimeBefore.Backend -Actual (Assert-BackendLoopbackOnly) | Out-Null

        Install-AtomicFile -Source $candidateProxy -Destination $installedProxy
        Install-AtomicFile -Source $candidateStart -Destination $installedStart
        Set-StateValue -State $state -Name 'Stage' -Value 'FilesInstalled'
        Assert-NoRelayConnections
        Stop-ExactRelayOnce -Expected $state.RuntimeBefore.Relay
        Set-StateValue -State $state -Name 'Stage' -Value 'OldRelayStopped'
        Start-RelayOnce -StartScript $installedStart
        $newRelay = Get-ListenerIdentity -Port 9000
        if ([int]$newRelay.Pid -eq [int]$state.RuntimeBefore.Relay.Pid) { throw 'Relay PID did not change after the single reviewed restart' }
        Set-StateValue -State $state -Name 'RuntimeAfter' -Value $newRelay
        Confirm-RelayRuntimeIdentity -Expected $state.RuntimeBefore.Backend -Actual (Assert-BackendLoopbackOnly) | Out-Null
        if ((Get-Sha256 $installedProxy) -cne [string]$state.Files.ProxyCandidateSha256 -or (Get-Sha256 $installedStart) -cne [string]$state.Files.StartCandidateSha256) {
            throw 'Installed candidate hashes do not match the prepared release'
        }
        Restore-WatchdogState -Original $state.WatchdogBefore
        if ([bool]$state.WatchdogBefore.Enabled -and [string]$state.WatchdogBefore.State -eq 'Running') {
            Start-Sleep -Seconds (($WatchdogPollSeconds * 2) + 2)
            Confirm-RelayRuntimeIdentity -Expected $newRelay -Actual (Get-ListenerIdentity -Port 9000) | Out-Null
        }
        Set-StateValue -State $state -Name 'RuntimeAfter' -Value $newRelay
        Set-StateValue -State $state -Name 'Stage' -Value 'Applied'
        Write-Output "Applied $ReleaseId with one exact relay stop/start. No Key material was read or recorded by this release script."
    } catch {
        $applyError = $_.Exception.Message
        Set-StateValue -State $state -Name 'LastApplyError' -Value $applyError
        $releaseMutationStarted = ([string]$state.Stage -cne 'Prepared' -or [bool]$state.ExactFirewallRuleCreated)
        if (-not $releaseMutationStarted) {
            throw "Apply failed before any release mutation: $applyError"
        }
        try {
            Restore-RelayRelease -State $state
        } catch {
            throw "Apply failed: $applyError. Automatic rollback also failed: $($_.Exception.Message)"
        }
        throw "Apply failed and was rolled back: $applyError"
    }
}

function Invoke-Rollback {
    if ($ConfirmReleaseId -cne $ReleaseId) { throw 'Rollback requires -ConfirmReleaseId exactly matching the release identity' }
    $state = Read-ReleaseState
    if ([string]$state.Stage -eq 'Restored') { throw 'Release state is already Restored and cannot be replayed' }
    if ([string]$state.Stage -eq 'Prepared' -and -not [bool]$state.ExactFirewallRuleCreated) {
        throw 'Prepared state has no release mutation to roll back'
    }
    Restore-RelayRelease -State $state
    Write-Output "Rolled back $ReleaseId to the prepared file, firewall, and watchdog state."
}

switch ($Action) {
    'Prepare' { Invoke-Prepare }
    'Apply' { Invoke-Apply }
    'Rollback' { Invoke-Rollback }
}
