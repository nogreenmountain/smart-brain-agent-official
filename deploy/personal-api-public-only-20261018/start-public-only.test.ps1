$ErrorActionPreference = 'Stop'

$source = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'start-services.ps1') -Raw

if ($source -notmatch '(?m)^\s*\$env:CPA_TRUSTED_PROXY_IPS\s*=\s*''192\.168\.10\.165''\s*$') {
    throw 'The Windows relay must allow only the production gateway host'
}

$assignment = $source.IndexOf("`$env:CPA_TRUSTED_PROXY_IPS")
$start = $source.IndexOf("Start-Process -FilePath `$node")
if ($assignment -lt 0 -or $start -lt 0 -or $assignment -gt $start) {
    throw 'The trusted proxy allowlist must be set before the relay starts'
}

Write-Output 'PASS: Windows relay source allowlist is explicit and startup-bound'
