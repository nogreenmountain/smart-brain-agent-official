$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$scriptPath = Join-Path $PSScriptRoot 'Invoke-WindowsRelayRelease.ps1'
$temporaryBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$testRoot = Join-Path $temporaryBase ('smartbrain-relay-release-test-' + [guid]::NewGuid().ToString('N'))
$installDir = Join-Path $testRoot 'installed'
$stateDir = Join-Path $testRoot 'state'

function Get-NetTCPConnection {
    [CmdletBinding()]
    param([int]$LocalPort, [string]$State)
    if ($State -eq 'Listen' -and $LocalPort -eq 9000) {
        return [pscustomobject]@{ OwningProcess=4242; LocalAddress='0.0.0.0'; LocalPort=9000; State='Listen' }
    }
    if ($State -eq 'Listen' -and $LocalPort -eq 3000) {
        return [pscustomobject]@{ OwningProcess=3000; LocalAddress='127.0.0.1'; LocalPort=3000; State='Listen' }
    }
    return @()
}

function Get-Process {
    [CmdletBinding()]
    param([int]$Id)
    if ($Id -eq 4242) { return [pscustomobject]@{ Id=4242; ProcessName='node'; StartTime=[datetime]'2026-10-18T10:00:00Z' } }
    if ($Id -eq 3000) { return [pscustomobject]@{ Id=3000; ProcessName='cli-proxy-api'; StartTime=[datetime]'2026-10-18T09:00:00Z' } }
    throw "Unexpected process id $Id"
}

$global:fixtureRules = @(
    [pscustomobject]@{ InstanceID='r1'; Name='legacy-9000-a'; DisplayName='Legacy 9000 A'; Description=''; Enabled='True'; Direction='Inbound'; Action='Allow'; Profile='Any'; PolicyStoreSource='PersistentStore'; PolicyStoreSourceType='Local'; TestProtocol='TCP'; TestLocalPort='9000'; TestRemoteAddress='Any'; TestProgram='Any' },
    [pscustomobject]@{ InstanceID='r2'; Name='legacy-9000-b'; DisplayName='Legacy 9000 B'; Description=''; Enabled='True'; Direction='Inbound'; Action='Allow'; Profile='Any'; PolicyStoreSource='PersistentStore'; PolicyStoreSourceType='Local'; TestProtocol='TCP'; TestLocalPort='9000'; TestRemoteAddress='Any'; TestProgram='Any' },
    [pscustomobject]@{ InstanceID='r3'; Name='node-public'; DisplayName='Node.js Public'; Description=''; Enabled='True'; Direction='Inbound'; Action='Allow'; Profile='Public'; PolicyStoreSource='PersistentStore'; PolicyStoreSourceType='Local'; TestProtocol='TCP'; TestLocalPort='Any'; TestRemoteAddress='Any'; TestProgram='C:\Users\test\nodejs\node.exe' }
)

function Get-NetFirewallRule {
    [CmdletBinding()]
    param([string]$PolicyStore, [string]$Name)
    if ($Name) { return @($global:fixtureRules | Where-Object Name -eq $Name) }
    return $global:fixtureRules
}
function Get-NetFirewallPortFilter {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$AssociatedNetFirewallRule)
    return [pscustomobject]@{ Protocol=$AssociatedNetFirewallRule.TestProtocol; LocalPort=$AssociatedNetFirewallRule.TestLocalPort }
}
function Get-NetFirewallAddressFilter {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$AssociatedNetFirewallRule)
    return [pscustomobject]@{ LocalAddress='Any'; RemoteAddress=$AssociatedNetFirewallRule.TestRemoteAddress }
}
function Get-NetFirewallApplicationFilter {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$AssociatedNetFirewallRule)
    return [pscustomobject]@{ Program=$AssociatedNetFirewallRule.TestProgram }
}
function Get-NetFirewallProfile {
    [CmdletBinding()]
    param([string]$PolicyStore)
    return @('Domain','Private','Public') | ForEach-Object { [pscustomobject]@{ Name=$_; Enabled=$true; DefaultInboundAction='Block' } }
}
function Get-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    return [pscustomobject]@{ TaskName=$TaskName; State='Running'; Settings=[pscustomobject]@{ Enabled=$true } }
}
function Export-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    return "<Task><RegistrationInfo><URI>\$TaskName</URI></RegistrationInfo></Task>"
}

function New-NetFirewallRule { throw 'Prepare must not create firewall rules' }
function Disable-NetFirewallRule { throw 'Prepare must not disable firewall rules' }
function Enable-NetFirewallRule { throw 'Prepare must not enable firewall rules' }
function Remove-NetFirewallRule { throw 'Prepare must not remove firewall rules' }
function Stop-Process { throw 'Prepare must not stop a process' }
function Disable-ScheduledTask { throw 'Prepare must not disable the watchdog' }
function Stop-ScheduledTask { throw 'Prepare must not stop the watchdog' }

try {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'proxy-server.js') -Destination (Join-Path $installDir 'proxy-server.js')
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'start-services.ps1') -Destination (Join-Path $installDir 'start-services.ps1')

    & $scriptPath -Action Prepare -InstallDir $installDir -StateDir $stateDir -CandidateDir $PSScriptRoot | Out-Null
    $state = Get-Content -LiteralPath (Join-Path $stateDir 'release-state.json') -Raw | ConvertFrom-Json
    if ($state.Stage -ne 'Prepared') { throw 'Prepare did not persist Prepared state' }
    if ($state.Privacy -notmatch 'No Key') { throw 'Prepare did not persist the privacy boundary' }
    if (@($state.Firewall.BroadRules).Count -ne 3) { throw 'Prepare did not bind the three reviewed broad rules' }
    foreach ($name in @('proxy-server.js','start-services.ps1')) {
        $backup = Join-Path (Join-Path $stateDir 'backup') $name
        if (-not (Test-Path -LiteralPath $backup -PathType Leaf)) { throw "Prepare did not back up $name" }
    }
    Write-Output 'PASS: mocked Prepare backs up files and writes a reviewable state without system mutation'
} finally {
    $resolved = [System.IO.Path]::GetFullPath($testRoot)
    if (-not $resolved.StartsWith($temporaryBase, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Refusing to remove a test directory outside the system temporary directory'
    }
    if (Test-Path -LiteralPath $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
