$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$scriptPath = Join-Path $PSScriptRoot 'Invoke-WindowsRelayRelease.ps1'
$releaseId = 'personal-api-public-only-20261018-r1'
$temporaryBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$testRoot = Join-Path $temporaryBase ('smartbrain-relay-release-cycle-' + [guid]::NewGuid().ToString('N'))
$installDir = Join-Path $testRoot 'installed'
$stateDir = Join-Path $testRoot 'state'
$global:operationLog = [System.Collections.Generic.List[string]]::new()
$global:relayPid = 4242
$global:relayStart = [datetime]'2026-10-18T10:00:00Z'
$global:relayExists = $true
$global:startCount = 0
$global:taskEnabled = $true
$global:taskState = 'Running'
$global:defaultInboundAction = 'Block'
$global:establishedSamples = [System.Collections.Generic.Queue[int]]::new()
$global:establishedSamples.Enqueue(0)
$global:establishedSamples.Enqueue(0)

$global:fixtureRules = @(
    [pscustomobject]@{ InstanceID='r1'; Name='legacy-9000-a'; DisplayName='Legacy 9000 A'; Description=''; Group=''; Enabled='True'; Direction='Inbound'; Action='Allow'; Profile='Any'; PolicyStoreSource='PersistentStore'; PolicyStoreSourceType='Local'; TestProtocol='TCP'; TestLocalAddress='Any'; TestLocalPort='9000'; TestRemoteAddress='Any'; TestProgram='Any' },
    [pscustomobject]@{ InstanceID='r2'; Name='legacy-9000-b'; DisplayName='Legacy 9000 B'; Description=''; Group=''; Enabled='True'; Direction='Inbound'; Action='Allow'; Profile='Any'; PolicyStoreSource='PersistentStore'; PolicyStoreSourceType='Local'; TestProtocol='TCP'; TestLocalAddress='Any'; TestLocalPort='9000'; TestRemoteAddress='Any'; TestProgram='Any' },
    [pscustomobject]@{ InstanceID='r3'; Name='node-public'; DisplayName='Node.js Public'; Description=''; Group=''; Enabled='True'; Direction='Inbound'; Action='Allow'; Profile='Public'; PolicyStoreSource='PersistentStore'; PolicyStoreSourceType='Local'; TestProtocol='TCP'; TestLocalAddress='Any'; TestLocalPort='Any'; TestRemoteAddress='Any'; TestProgram='C:\Users\test\nodejs\node.exe' }
)

function Get-NetTCPConnection {
    [CmdletBinding()]
    param([int]$LocalPort, [string]$State)
    if ($State -eq 'Listen' -and $LocalPort -eq 9000 -and $global:relayExists) {
        return [pscustomobject]@{ OwningProcess=$global:relayPid; LocalAddress='0.0.0.0'; LocalPort=9000; State='Listen' }
    }
    if ($State -eq 'Listen' -and $LocalPort -eq 3000) {
        return [pscustomobject]@{ OwningProcess=3000; LocalAddress='127.0.0.1'; LocalPort=3000; State='Listen' }
    }
    if ($State -eq 'Established' -and $LocalPort -eq 9000 -and $global:establishedSamples.Count -gt 0) {
        $count = $global:establishedSamples.Dequeue()
        if ($count -eq 0) { return @() }
        return @(1..$count | ForEach-Object { [pscustomobject]@{ State='Established' } })
    }
    return @()
}

function Get-Process {
    [CmdletBinding()]
    param([int]$Id)
    if ($Id -eq 3000) { return [pscustomobject]@{ Id=3000; ProcessName='cli-proxy-api'; StartTime=[datetime]'2026-10-18T09:00:00Z' } }
    if ($global:relayExists -and $Id -eq $global:relayPid) {
        return [pscustomobject]@{ Id=$global:relayPid; ProcessName='node'; StartTime=$global:relayStart }
    }
    return $null
}

function Stop-Process {
    [CmdletBinding()]
    param([int]$Id)
    if (-not $global:relayExists -or $Id -ne $global:relayPid) { throw "Unexpected process stop: $Id" }
    $global:operationLog.Add("StopRelay:$Id")
    $global:relayExists = $false
}

function Start-Process {
    [CmdletBinding()]
    param([string]$FilePath, [object[]]$ArgumentList, [switch]$Wait, [switch]$PassThru, [string]$WindowStyle)
    if ($FilePath -ne 'powershell.exe') { throw "Unexpected process start: $FilePath" }
    $global:startCount++
    $global:relayPid = if ($global:startCount -eq 1) { 5252 } else { 6262 }
    $global:relayStart = ([datetime]'2026-10-18T11:00:00Z').AddMinutes($global:startCount)
    $global:relayExists = $true
    $global:operationLog.Add("StartRelay:$($global:relayPid)")
    $process = [pscustomobject]@{ ExitCode=0 }
    $process | Add-Member -MemberType ScriptMethod -Name WaitForExit -Value { }
    return $process
}

function Start-Sleep { param([int]$Seconds, [int]$Milliseconds) }

function Get-NetFirewallRule {
    [CmdletBinding()]
    param([string]$PolicyStore, [string]$Name)
    if ($Name) { return @($global:fixtureRules | Where-Object Name -eq $Name) }
    return $global:fixtureRules
}
function Get-NetFirewallPortFilter {
    [CmdletBinding()]
    param([Parameter(Mandatory,ValueFromPipeline)]$AssociatedNetFirewallRule)
    process { [pscustomobject]@{ Protocol=$AssociatedNetFirewallRule.TestProtocol; LocalPort=$AssociatedNetFirewallRule.TestLocalPort } }
}
function Get-NetFirewallAddressFilter {
    [CmdletBinding()]
    param([Parameter(Mandatory,ValueFromPipeline)]$AssociatedNetFirewallRule)
    process { [pscustomobject]@{ LocalAddress=$AssociatedNetFirewallRule.TestLocalAddress; RemoteAddress=$AssociatedNetFirewallRule.TestRemoteAddress } }
}
function Get-NetFirewallApplicationFilter {
    [CmdletBinding()]
    param([Parameter(Mandatory,ValueFromPipeline)]$AssociatedNetFirewallRule)
    process { [pscustomobject]@{ Program=$AssociatedNetFirewallRule.TestProgram } }
}
function Get-NetFirewallProfile {
    [CmdletBinding()]
    param([string]$PolicyStore)
    return @('Domain','Private','Public') | ForEach-Object { [pscustomobject]@{ Name=$_; Enabled=$true; DefaultInboundAction=$global:defaultInboundAction } }
}
function New-NetFirewallRule {
    [CmdletBinding()]
    param([string]$Name,[string]$DisplayName,[string]$Description,[string]$Group,[string]$Direction,[string]$Action,[string]$Enabled,[string]$Profile,[string]$Protocol,[string]$LocalAddress,[int]$LocalPort,[string]$RemoteAddress)
    $global:operationLog.Add('CreateExactAllow')
    $global:fixtureRules += [pscustomobject]@{
        InstanceID='exact-r1'; Name=$Name; DisplayName=$DisplayName; Description=$Description; Group=$Group; Enabled='True'; Direction=$Direction; Action=$Action; Profile=$Profile;
        PolicyStoreSource='PersistentStore'; PolicyStoreSourceType='Local'; TestProtocol=$Protocol; TestLocalAddress=$LocalAddress; TestLocalPort=[string]$LocalPort; TestRemoteAddress=$RemoteAddress; TestProgram='Any'
    }
}
function Disable-NetFirewallRule {
    [CmdletBinding()]
    param([Parameter(Mandatory,ValueFromPipeline)]$InputObject)
    process {
        $InputObject.Enabled = 'False'
        $global:operationLog.Add("DisableRule:$($InputObject.Name)")
        return $InputObject
    }
}
function Enable-NetFirewallRule {
    [CmdletBinding()]
    param([Parameter(Mandatory,ValueFromPipeline)]$InputObject)
    process {
        $InputObject.Enabled = 'True'
        $global:operationLog.Add("EnableRule:$($InputObject.Name)")
        return $InputObject
    }
}
function Remove-NetFirewallRule {
    [CmdletBinding()]
    param([Parameter(Mandatory,ValueFromPipeline)]$InputObject)
    process {
        $global:operationLog.Add("RemoveRule:$($InputObject.Name)")
        $global:fixtureRules = @($global:fixtureRules | Where-Object InstanceID -ne $InputObject.InstanceID)
    }
}

function Get-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    return [pscustomobject]@{ TaskName=$TaskName; State=$global:taskState; Settings=[pscustomobject]@{ Enabled=$global:taskEnabled } }
}
function Export-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    return "<Task><RegistrationInfo><URI>\$TaskName</URI></RegistrationInfo></Task>"
}
function Disable-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    $global:taskEnabled = $false
    if ($global:taskState -ne 'Running') { $global:taskState = 'Disabled' }
    $global:operationLog.Add('DisableWatchdog')
}
function Stop-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    $global:taskState = if ($global:taskEnabled) { 'Ready' } else { 'Disabled' }
    $global:operationLog.Add('StopWatchdog')
}
function Enable-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    $global:taskEnabled = $true
    if ($global:taskState -eq 'Disabled') { $global:taskState = 'Ready' }
    $global:operationLog.Add('EnableWatchdog')
}
function Start-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    if (-not $global:taskEnabled) { throw 'Cannot start a disabled watchdog' }
    $global:taskState = 'Running'
    $global:operationLog.Add('StartWatchdog')
}

try {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $installDir 'proxy-server.js') -Value '// old proxy fixture' -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $installDir 'start-services.ps1') -Value '# old start fixture' -Encoding UTF8
    $oldProxyHash = (Get-FileHash -LiteralPath (Join-Path $installDir 'proxy-server.js') -Algorithm SHA256).Hash
    $oldStartHash = (Get-FileHash -LiteralPath (Join-Path $installDir 'start-services.ps1') -Algorithm SHA256).Hash

    & $scriptPath -Action Prepare -InstallDir $installDir -StateDir $stateDir -CandidateDir $PSScriptRoot -ReleaseId $releaseId | Out-Null
    $global:defaultInboundAction = 'Allow'
    try {
        & $scriptPath -Action Apply -InstallDir $installDir -StateDir $stateDir -CandidateDir $PSScriptRoot -ReleaseId $releaseId -ConfirmReleaseId $releaseId | Out-Null
        throw 'Expected the pre-mutation firewall profile gate to fail'
    } catch {
        if ($_.Exception.Message -notmatch 'Apply failed before any release mutation') { throw }
    }
    if ($global:operationLog.Count -ne 0) { throw 'A pre-mutation Apply failure changed simulated system state' }
    $stillPrepared = Get-Content -LiteralPath (Join-Path $stateDir 'release-state.json') -Raw | ConvertFrom-Json
    if ($stillPrepared.Stage -ne 'Prepared') { throw 'A pre-mutation Apply failure changed the release stage' }
    $global:defaultInboundAction = 'Block'
    & $scriptPath -Action Apply -InstallDir $installDir -StateDir $stateDir -CandidateDir $PSScriptRoot -ReleaseId $releaseId -ConfirmReleaseId $releaseId | Out-Null

    $applied = Get-Content -LiteralPath (Join-Path $stateDir 'release-state.json') -Raw | ConvertFrom-Json
    if ($applied.Stage -ne 'Applied') { throw 'Apply did not reach Applied state' }
    if ($global:startCount -ne 1) { throw 'Apply must invoke start-services exactly once' }
    if (@($global:operationLog | Where-Object { $_ -eq 'StopRelay:4242' }).Count -ne 1) { throw 'Apply must stop the exact old relay PID once' }
    $createAt = $global:operationLog.IndexOf('CreateExactAllow')
    $firstDisableAt = -1
    for ($i=0; $i -lt $global:operationLog.Count; $i++) { if ($global:operationLog[$i] -like 'DisableRule:*') { $firstDisableAt=$i; break } }
    if ($createAt -lt 0 -or $firstDisableAt -le $createAt) { throw 'Exact allow was not created before broad rules were disabled' }
    if (@($global:fixtureRules | Where-Object { $_.InstanceID -in @('r1','r2','r3') -and $_.Enabled -eq 'False' }).Count -ne 3) { throw 'Apply did not disable all three broad rules' }

    & $scriptPath -Action Rollback -InstallDir $installDir -StateDir $stateDir -CandidateDir $PSScriptRoot -ReleaseId $releaseId -ConfirmReleaseId $releaseId | Out-Null
    $restored = Get-Content -LiteralPath (Join-Path $stateDir 'release-state.json') -Raw | ConvertFrom-Json
    if ($restored.Stage -ne 'Restored') { throw 'Rollback did not reach Restored state' }
    if ($global:startCount -ne 2) { throw 'Rollback must invoke the original start-services exactly once' }
    if (@($global:operationLog | Where-Object { $_ -eq 'StopRelay:5252' }).Count -ne 1) { throw 'Rollback must stop the exact new relay PID once' }
    if ((Get-FileHash -LiteralPath (Join-Path $installDir 'proxy-server.js') -Algorithm SHA256).Hash -cne $oldProxyHash) { throw 'Rollback did not restore proxy-server.js' }
    if ((Get-FileHash -LiteralPath (Join-Path $installDir 'start-services.ps1') -Algorithm SHA256).Hash -cne $oldStartHash) { throw 'Rollback did not restore start-services.ps1' }
    if (@($global:fixtureRules | Where-Object { $_.InstanceID -in @('r1','r2','r3') -and $_.Enabled -eq 'True' }).Count -ne 3) { throw 'Rollback did not restore the broad firewall rules' }
    if (@($global:fixtureRules | Where-Object InstanceID -eq 'exact-r1').Count -ne 0) { throw 'Rollback did not remove its exact allow rule' }
    if (-not $global:taskEnabled -or $global:taskState -ne 'Running') { throw 'Rollback did not restore the watchdog enabled/running state' }
    $stateDir = Join-Path $testRoot 'late-connection-state'
    & $scriptPath -Action Prepare -InstallDir $installDir -StateDir $stateDir -CandidateDir $PSScriptRoot -ReleaseId $releaseId | Out-Null
    $stopCountBefore = @($global:operationLog | Where-Object { $_ -like 'StopRelay:*' }).Count
    $global:establishedSamples.Enqueue(0)
    $global:establishedSamples.Enqueue(0)
    $global:establishedSamples.Enqueue(1)
    try {
        & $scriptPath -Action Apply -InstallDir $installDir -StateDir $stateDir -CandidateDir $PSScriptRoot -ReleaseId $releaseId -ConfirmReleaseId $releaseId | Out-Null
        throw 'Expected late connection failure'
    } catch {
        if ($_.Exception.Message -notmatch 'rolled back: TCP/9000 accepted') { throw }
    }
    if (@($global:operationLog | Where-Object { $_ -like 'StopRelay:*' }).Count -ne $stopCountBefore) { throw 'Rollback killed the unchanged old relay with an active late connection' }
    if ((Get-FileHash -LiteralPath (Join-Path $installDir 'proxy-server.js')).Hash -cne $oldProxyHash) { throw 'Late connection rollback did not restore files' }
    Write-Output 'PASS: pre-mutation failure, lifecycle rollback, and late connection rollback preserve exact runtime identity'
} finally {
    $resolved = [System.IO.Path]::GetFullPath($testRoot)
    if (-not $resolved.StartsWith($temporaryBase, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Refusing to remove a test directory outside the system temporary directory'
    }
    if (Test-Path -LiteralPath $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
