param(
  [Parameter(Mandatory=$true)][string]$ApiBaseUrl,
  [string]$ProjectId = "",
  [string]$ProjectDir = (Get-Location).Path,
  [int]$ListenPort = 8791,
  [string]$AdapterScript = "$PSScriptRoot\smartbrain_codex_adapter.py",
  [string]$ApiKey = ""
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $AdapterScript)) {
  throw "找不到适配器脚本: $AdapterScript"
}
if (-not $ApiKey) { $ApiKey = Read-Host '请输入 SmartBrain Gateway API Key（不会写入项目文件）' }
$env:SMARTBRAIN_API_KEY = $ApiKey
$python = (Get-Command python -ErrorAction Stop).Source
$arguments = @('--api-base-url', $ApiBaseUrl, '--project-dir', $ProjectDir, '--listen-port', $ListenPort)
if ($ProjectId) { $arguments += @('--project-id', $ProjectId) }
& $python $AdapterScript @arguments
