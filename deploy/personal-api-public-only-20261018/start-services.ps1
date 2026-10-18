$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $dir 'cli-proxy-api.exe'
$proxyScript = Join-Path $dir 'proxy-server.js'
$node = 'C:\Users\test\nodejs\node.exe'

# The persistent task runs as SYSTEM so it cannot be tied to Codex's
# process/job lifetime. Keep the existing user's OAuth store when invoked
# under SYSTEM; interactive launches retain their normal environment.
if ([Security.Principal.WindowsIdentity]::GetCurrent().User.Value -eq 'S-1-5-18') {
  $env:USERPROFILE = 'C:\Users\test'
  $env:HOME = 'C:\Users\test'
}

function Test-Listening([int]$port, [string]$localAddress = '') {
  $parameters = @{ LocalPort = $port; State = 'Listen'; ErrorAction = 'SilentlyContinue' }
  if ($localAddress) { $parameters.LocalAddress = $localAddress }
  return [bool](Get-NetTCPConnection @parameters)
}

function Get-CpaUpstreamKeyFromConfig {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigText
  )

  # The first quoted YAML list in config.yaml is often a model/provider label
  # (currently "Executor").  Only the scalar list under access.api-keys is a
  # valid loopback credential.  Keep this parser dependency-free and fail
  # closed when the expected shape is missing or ambiguous.
  $lines = $ConfigText -split '\r?\n'
  $accessIndent = $null
  $apiKeysIndent = $null
  $keys = [System.Collections.Generic.List[string]]::new()

  foreach ($line in $lines) {
    if ($line -match '^\s*(?:#.*)?$') { continue }
    $trimmed = $line.Trim()
    $indent = $line.Length - $line.TrimStart().Length

    if ($null -eq $accessIndent) {
      if ($trimmed -match '^access:\s*(?:#.*)?$') { $accessIndent = $indent }
      continue
    }

    if ($indent -le $accessIndent) { break }

    if ($null -eq $apiKeysIndent) {
      if ($trimmed -match '^api-keys:\s*(?:#.*)?$') { $apiKeysIndent = $indent }
      continue
    }

    if ($indent -le $apiKeysIndent) { break }
    if ($trimmed -match '^ -') { throw 'Invalid access.api-keys configuration' }
    if ($trimmed -notmatch '^-[ \t]+(.+?)\s*(?:#.*)?$') {
      throw 'Invalid access.api-keys configuration'
    }

    $literal = $Matches[1].Trim()
    if ($literal.Length -lt 2) { throw 'Invalid access.api-keys configuration' }
    if ($literal.StartsWith('"') -and $literal.EndsWith('"')) {
      try { $value = $literal | ConvertFrom-Json }
      catch { throw 'Invalid access.api-keys configuration' }
    } elseif ($literal.StartsWith("'") -and $literal.EndsWith("'")) {
      $value = $literal.Substring(1, $literal.Length - 2).Replace("''", "'")
    } else {
      throw 'Invalid access.api-keys configuration'
    }
    if ([string]::IsNullOrWhiteSpace([string]$value)) {
      throw 'Invalid access.api-keys configuration'
    }
    $keys.Add([string]$value)
  }

  if ($null -eq $accessIndent -or $null -eq $apiKeysIndent -or $keys.Count -ne 1) {
    throw 'Invalid access.api-keys configuration'
  }
  return $keys[0]
}

if (-not (Test-Listening 3000 '127.0.0.1')) {
  Start-Process -FilePath $backend -WorkingDirectory $dir -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $dir 'api_task_stdout.log') `
    -RedirectStandardError (Join-Path $dir 'api_task_stderr.log') | Out-Null
  for ($i = 0; $i -lt 30 -and -not (Test-Listening 3000 '127.0.0.1'); $i++) { Start-Sleep -Seconds 1 }
}

if (-not (Test-Listening 3000 '127.0.0.1')) { throw 'CLIProxyAPI backend did not listen on 127.0.0.1:3000' }

if (-not (Test-Listening 9000)) {
  $cfg = Get-Content -LiteralPath (Join-Path $dir 'config.yaml') -Raw
  $env:CPA_UPSTREAM_KEY = Get-CpaUpstreamKeyFromConfig -ConfigText $cfg
  # 9000 is the personal-key compatibility entry. Every /v1 request is
  # checked against SmartBrain before it reaches the local CPA backend.
  # Read the internal CPA key from config only for the detached proxy's
  # loopback hop; callers never receive or reuse this key.
  $managementKeyFile = Join-Path $dir 'secrets\cpa-management-key'
  if (-not (Test-Path -LiteralPath $managementKeyFile)) { throw 'CPA management key file is missing' }
  $env:CPA_MANAGEMENT_KEY = (Get-Content -LiteralPath $managementKeyFile -Raw).Trim()
  if (-not $env:CPA_MANAGEMENT_KEY) { throw 'CPA management key file is empty' }
  $env:SMARTBRAIN_GATEWAY_URL = 'https://39.105.79.0'
  $env:CPA_API_PORT = '3000'
  $env:CPA_PROXY_PORT = '9000'
  $env:CPA_TRUSTED_PROXY_IPS = '192.168.10.165'
  Start-Process -FilePath $node -ArgumentList 'proxy-server.js' -WorkingDirectory $dir -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $dir 'proxy_task_stdout.log') `
    -RedirectStandardError (Join-Path $dir 'proxy_task_stderr.log') | Out-Null
  for ($i = 0; $i -lt 20 -and -not (Test-Listening 9000); $i++) { Start-Sleep -Seconds 1 }
}

if (-not (Test-Listening 9000)) { throw 'CLIProxyAPI2 compatibility relay did not listen on port 9000' }
