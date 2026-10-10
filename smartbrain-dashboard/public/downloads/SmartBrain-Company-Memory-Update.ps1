param(
    [string]$Endpoint = 'https://39.105.79.0/mcp',
    [string]$BundleUrl = 'https://39.105.79.0/downloads/smartbrain-company-memory-codex.zip',
    [string]$Token,
    [string]$BundlePath,
    [string]$CodexPath
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1') -Force
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Archive\Microsoft.PowerShell.Archive.psd1') -Force
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$expectedVersion = '0.2.1+codex.20261008'
$expectedSha = 'b7542ddc8d1e34a78a9836081f75520a5340ad9885eeb3d39c7fdf13138d7182'
foreach ($value in @($Endpoint, $BundleUrl)) {
    $uri = [Uri]$value
    if (!$uri.IsAbsoluteUri -or $uri.Scheme -notin @('http','https') -or $uri.UserInfo) {
        throw 'Only absolute HTTP/HTTPS URLs without embedded credentials are supported.'
    }
}
if ($Token -and $Token -notmatch '^sbmcp_[A-Za-z0-9._~-]+$') { throw 'Invalid MCP token.' }
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
if (!$CodexPath) {
    foreach ($name in @('codex.cmd','codex.exe')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) { $CodexPath = $command.Source; break }
    }
    if (!$CodexPath) {
        $desktopCli = Join-Path $codexHome 'plugins\.plugin-appserver\codex.exe'
        if (Test-Path -LiteralPath $desktopCli -PathType Leaf) { $CodexPath = $desktopCli }
    }
}
if (!$CodexPath -or !(Test-Path -LiteralPath $CodexPath -PathType Leaf)) {
    throw 'No compatible Codex CLI found. Install Codex CLI or open the Codex desktop app once.'
}
function Invoke-CodexJson([string[]]$Arguments) {
    $output = & $CodexPath @Arguments 2>$null
    if ($LASTEXITCODE -ne 0) { throw ('Codex command failed: ' + ($Arguments[0..1] -join ' ')) }
    return (($output -join "`n") | ConvertFrom-Json)
}
$parent = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'SmartBrain'))
$root = [IO.Path]::GetFullPath((Join-Path $parent 'CodexPluginMarketplace'))
if ([IO.Path]::GetDirectoryName($root) -ne $parent) { throw 'Unsafe marketplace path.' }
New-Item -ItemType Directory -Path $parent -Force | Out-Null
$operation = [Guid]::NewGuid().ToString('N')
$stage = Join-Path $parent ('CodexPluginMarketplace-stage-' + $operation)
$backup = Join-Path $parent ('CodexPluginMarketplace-backup-' + $operation)
$failed = Join-Path $parent ('CodexPluginMarketplace-failed-' + $operation)
$download = Join-Path $env:TEMP ('smartbrain-company-memory-' + $operation + '.zip')
$moved = $false
$registered = $false
$oldMarket = $null
$oldPlugin = $null
$userTokenBefore = [Environment]::GetEnvironmentVariable('SMARTBRAIN_WIKI_MCP_TOKEN','User')
$processTokenBefore = $env:SMARTBRAIN_WIKI_MCP_TOKEN
try {
    if (!$BundlePath) {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $BundleUrl -OutFile $download -UseBasicParsing -Headers @{'Cache-Control'='no-cache'}
        $BundlePath = $download
    }
    if ((Get-FileHash -LiteralPath $BundlePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedSha) {
        throw 'Plugin bundle integrity check failed; the installed plugin was not changed.'
    }
    New-Item -ItemType Directory -Path $stage | Out-Null
    Expand-Archive -LiteralPath $BundlePath -DestinationPath $stage
    $manifest = Join-Path $stage 'plugins\company-memory\.codex-plugin\plugin.json'
    $plugin = Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($plugin.name -ne 'company-memory' -or $plugin.version -ne $expectedVersion) { throw 'Unexpected plugin version.' }
    $plugin.mcpServers.'smartbrain-company-memory'.url = $Endpoint
    [IO.File]::WriteAllText($manifest,($plugin | ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
    $markets = Invoke-CodexJson @('plugin','marketplace','list','--json')
    $oldMarket = @($markets.marketplaces | Where-Object { $_.name -eq 'smartbrain' } | Select-Object -First 1)
    $installed = Invoke-CodexJson @('plugin','list','--json')
    $oldPlugin = @($installed.installed | Where-Object { $_.pluginId -eq 'company-memory@smartbrain' } | Select-Object -First 1)
    if (Test-Path -LiteralPath $root) { Move-Item -LiteralPath $root -Destination $backup }
    $moved = $true
    Move-Item -LiteralPath $stage -Destination $root
    if ($oldMarket.Count) { Invoke-CodexJson @('plugin','marketplace','remove','smartbrain','--json') | Out-Null }
    Invoke-CodexJson @('plugin','marketplace','add',$root,'--json') | Out-Null
    $registered = $true
    $result = Invoke-CodexJson @('plugin','add','company-memory@smartbrain','--json')
    if ($result.version -ne $expectedVersion -or !$result.installedPath) { throw 'Installed version verification failed.' }
    $cached = Get-Content -LiteralPath (Join-Path $result.installedPath '.codex-plugin\plugin.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $skill = Get-Content -LiteralPath (Join-Path $result.installedPath 'skills\company-memory\SKILL.md') -Raw -Encoding UTF8
    if ($cached.version -ne $expectedVersion -or $skill -notmatch 'record_project_conversation') { throw 'Installed plugin contents verification failed.' }
    $check = Invoke-CodexJson @('plugin','list','--json')
    $current = @($check.installed | Where-Object { $_.pluginId -eq 'company-memory@smartbrain' })
    if ($current.Count -ne 1 -or $current[0].version -ne $expectedVersion -or !$current[0].enabled) { throw 'Plugin listing verification failed.' }
    if ($Token) {
        [Environment]::SetEnvironmentVariable('SMARTBRAIN_WIKI_MCP_TOKEN',$Token,'User')
        if ([Environment]::GetEnvironmentVariable('SMARTBRAIN_WIKI_MCP_TOKEN','User') -ne $Token) { throw 'Token persistence failed.' }
        $env:SMARTBRAIN_WIKI_MCP_TOKEN = $Token
    } elseif ([Environment]::GetEnvironmentVariable('SMARTBRAIN_WIKI_MCP_TOKEN','User') -ne $userTokenBefore -or $env:SMARTBRAIN_WIKI_MCP_TOKEN -ne $processTokenBefore) {
        throw 'The existing credential unexpectedly changed.'
    }
    [pscustomobject]@{
        status='passed'; installed_version=$current[0].version; plugin_id='company-memory@smartbrain'
        existing_token_preserved=(!$Token); previous_source_retained=(Test-Path -LiteralPath $backup)
    } | ConvertTo-Json -Compress
    Write-Host ('Company Memory ' + $expectedVersion + ' is installed. Start a new Codex chat/session to load the updated skill.') -ForegroundColor Green
} catch {
    $failure = $_.Exception.Message
    if ($Token) {
        [Environment]::SetEnvironmentVariable('SMARTBRAIN_WIKI_MCP_TOKEN',$userTokenBefore,'User')
        $env:SMARTBRAIN_WIKI_MCP_TOKEN = $processTokenBefore
    }
    if ($moved) {
        try {
            if ($registered) { Invoke-CodexJson @('plugin','marketplace','remove','smartbrain','--json') | Out-Null }
            if (Test-Path -LiteralPath $root) { Move-Item -LiteralPath $root -Destination $failed }
            if (Test-Path -LiteralPath $backup) { Move-Item -LiteralPath $backup -Destination $root }
            if ($oldMarket.Count) {
                Invoke-CodexJson @('plugin','marketplace','add',$oldMarket[0].root,'--json') | Out-Null
                if ($oldPlugin.Count) {
                    $restored = Invoke-CodexJson @('plugin','add','company-memory@smartbrain','--json')
                    if ($restored.version -ne $oldPlugin[0].version) { throw 'Previous plugin version did not restore.' }
                }
            } elseif ($registered) {
                Invoke-CodexJson @('plugin','remove','company-memory@smartbrain','--json') | Out-Null
            }
        } catch { throw ('Update failed and automatic restore needs attention. Preserved files: ' + $parent) }
    }
    throw ('Update failed: ' + $failure)
} finally {
    if (Test-Path -LiteralPath $download -PathType Leaf) { Remove-Item -LiteralPath $download -Force }
}
