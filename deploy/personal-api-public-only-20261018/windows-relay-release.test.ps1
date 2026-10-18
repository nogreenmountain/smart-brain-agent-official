$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$modulePath = Join-Path $PSScriptRoot 'WindowsRelayRelease.psm1'
$scriptPath = Join-Path $PSScriptRoot 'Invoke-WindowsRelayRelease.ps1'

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-Throws {
    param([scriptblock]$Action, [string]$MessagePattern)
    try {
        & $Action
    } catch {
        if ($_.Exception.Message -notmatch $MessagePattern) {
            throw "Expected error matching '$MessagePattern', got '$($_.Exception.Message)'"
        }
        return
    }
    throw "Expected an error matching '$MessagePattern'"
}

if (-not (Test-Path -LiteralPath $modulePath)) { throw 'WindowsRelayRelease.psm1 is missing' }
if (-not (Test-Path -LiteralPath $scriptPath)) { throw 'Invoke-WindowsRelayRelease.ps1 is missing' }
Import-Module $modulePath -Force

$profiles = @(
    [pscustomobject]@{ Name = 'Domain'; DefaultInboundAction = 'Block' },
    [pscustomobject]@{ Name = 'Private'; DefaultInboundAction = 'Block' },
    [pscustomobject]@{ Name = 'Public'; DefaultInboundAction = 'Block' }
)
$rules = @(
    [pscustomobject]@{ InstanceId='r1'; Name='legacy-9000-a'; DisplayName='Legacy 9000 A'; Enabled='True'; Direction='Inbound'; Action='Allow'; Profile='Any'; Protocol='TCP'; LocalPort='9000'; RemoteAddress='Any'; Program='Any' },
    [pscustomobject]@{ InstanceId='r2'; Name='legacy-9000-b'; DisplayName='Legacy 9000 B'; Enabled='True'; Direction='Inbound'; Action='Allow'; Profile='Any'; Protocol='TCP'; LocalPort='9000'; RemoteAddress='Any'; Program='Any' },
    [pscustomobject]@{ InstanceId='r3'; Name='node-public'; DisplayName='Node.js Public'; Enabled='True'; Direction='Inbound'; Action='Allow'; Profile='Public'; Protocol='TCP'; LocalPort='Any'; RemoteAddress='Any'; Program='C:\Users\test\nodejs\node.exe' }
)

$udp = $rules[2].PSObject.Copy()
$udp.InstanceId = 'udp'; $udp.Name = 'node-udp'; $udp.Protocol = 'UDP'
$withUdp = @(Get-RelayFirewallPlan -Profiles $profiles -Rules @($rules + $udp) -ReleaseId 'fixture')
Assert-True ($withUdp.Count -eq 4) 'UDP rules must not be treated as TCP relay exposure'
$plan = @(Get-RelayFirewallPlan -Profiles $profiles -Rules $rules -ReleaseId 'personal-api-public-only-20261018-r1')
Assert-True ($plan.Count -eq 4) 'Firewall plan must contain one exact allow and three disables'
Assert-True ($plan[0].Operation -eq 'CreateExactAllow') 'Exact allow must be created before broad rules are disabled'
Assert-True ($plan[0].LocalAddress -eq '192.168.10.146') 'Exact allow must bind the Windows relay address'
Assert-True ($plan[0].RemoteAddress -eq '192.168.10.165') 'Exact allow must bind the production gateway source'
Assert-True ($plan[0].LocalPort -eq 9000 -and $plan[0].Protocol -eq 'TCP') 'Exact allow must bind TCP/9000'
Assert-True ((@($plan | Where-Object Operation -eq 'DisableBroadRule')).Count -eq 3) 'All reviewed broad rules must be disabled'
Assert-True ((@($plan | Where-Object Operation -match 'Block')).Count -eq 0) 'No explicit block rule may be created'

Assert-Throws -MessagePattern 'exactly two enabled Any/9000 rules' -Action {
    Get-RelayFirewallPlan -Profiles $profiles -Rules @($rules[0], $rules[2]) -ReleaseId 'personal-api-public-only-20261018-r1' | Out-Null
}
$overlapRules = @(
    [pscustomobject]@{ InstanceId='r1'; Name='legacy-9000-a'; DisplayName='Legacy 9000 A'; Enabled='True'; Direction='Inbound'; Action='Allow'; Profile='Public'; Protocol='TCP'; LocalPort='9000'; RemoteAddress='Any'; Program='C:\Users\test\nodejs\node.exe' },
    $rules[1]
)
Assert-Throws -MessagePattern 'Node Public broad rule' -Action {
    Get-RelayFirewallPlan -Profiles $profiles -Rules $overlapRules -ReleaseId 'personal-api-public-only-20261018-r1' | Out-Null
}
$badProfiles = @($profiles | ForEach-Object { [pscustomobject]@{ Name=$_.Name; DefaultInboundAction=$_.DefaultInboundAction } })
$badProfiles[2].DefaultInboundAction = 'Allow'
Assert-Throws -MessagePattern 'default inbound action must be Block' -Action {
    Get-RelayFirewallPlan -Profiles $badProfiles -Rules $rules -ReleaseId 'personal-api-public-only-20261018-r1' | Out-Null
}

$expectedIdentity = [pscustomobject]@{ Pid=4242; StartTimeUtc='2026-10-18T10:00:00.0000000Z'; ProcessName='node' }
Assert-True (Confirm-RelayRuntimeIdentity -Expected $expectedIdentity -Actual $expectedIdentity) 'Exact PID/StartTime identity must pass'
Assert-Throws -MessagePattern 'runtime identity changed' -Action {
    Confirm-RelayRuntimeIdentity -Expected $expectedIdentity -Actual ([pscustomobject]@{ Pid=4242; StartTimeUtc='2026-10-18T10:00:01.0000000Z'; ProcessName='node' }) | Out-Null
}

Assert-True (Test-RelayDrainSamples -EstablishedCounts @(1, 0, 0)) 'Two consecutive zero samples must prove drain'
Assert-True (-not (Test-RelayDrainSamples -EstablishedCounts @(1, 0))) 'One zero sample must not prove drain'
Assert-True (-not (Test-RelayDrainSamples -EstablishedCounts @(0, 1, 0))) 'A reopened connection must reset drain proof'

$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile($scriptPath, [ref]$tokens, [ref]$errors) | Out-Null
Assert-True ($errors.Count -eq 0) ('Release script has parser errors: ' + (($errors | ForEach-Object Message) -join '; '))
$source = Get-Content -LiteralPath $scriptPath -Raw
$moduleSource = Get-Content -LiteralPath $modulePath -Raw
foreach ($required in @('Prepare', 'Apply', 'Rollback', 'CLIProxyAPI2Services', 'Wait-RelayConnectionsDrained', 'Restore-RelayRelease')) {
    Assert-True ($source.Contains($required)) "Release script is missing required behavior: $required"
}
Assert-True ($source.Contains('Apply failed before any release mutation')) 'Pre-mutation gate failures must not trigger a mutating rollback'
foreach ($forbidden in @('Get-ChildItem Env:', 'config.yaml', 'CPA_UPSTREAM_KEY', 'CPA_MANAGEMENT_KEY', 'CommandLine', '-Action Block')) {
    Assert-True (-not ($source + $moduleSource).Contains($forbidden)) "Release script must not read/log credentials or create block-all rules: $forbidden"
}
foreach ($forbidden in @('Stop-Process -Name', 'taskkill', 'restart-proxy.ps1', 'Remove-NetFirewallRule -All')) {
    Assert-True (-not ($source + $moduleSource).Contains($forbidden)) "Release script contains an imprecise or broad mutation: $forbidden"
}

$createIndex = $source.IndexOf('New-NetFirewallRule')
$disableIndex = $source.IndexOf('Disable-NetFirewallRule')
Assert-True ($createIndex -ge 0 -and $disableIndex -gt $createIndex) 'Exact firewall allow must be created before broad rules are disabled'
Assert-True ($source.Contains('Copy-Item -LiteralPath $installedProxy')) 'Prepare must back up proxy-server.js'
Assert-True ($source.Contains('Copy-Item -LiteralPath $installedStart')) 'Prepare must back up start-services.ps1'
Assert-True ($source.Contains('Get-FileHash')) 'Prepare and apply must bind file hashes'

Write-Output 'PASS: Windows relay release/firewall plan, identity, drain, privacy and rollback static tests'
