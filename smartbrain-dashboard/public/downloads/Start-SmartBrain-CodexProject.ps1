param(
  [Parameter(Mandatory=$true)][string]$ApiBaseUrl,
  [Parameter(Mandatory=$true)][string]$ProjectId,
  [Parameter(Mandatory=$true)][int]$ListenPort,
  [string]$ProjectDir = ""
)

$ErrorActionPreference = 'Stop'
$logPath = Join-Path $env:TEMP ('SmartBrain-Codex-{0}.log' -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
trap {
  $message = ($_ | Out-String).Trim()
  Write-Host $message -ForegroundColor Red
  try { Set-Content -LiteralPath $logPath -Value $message -Encoding UTF8 } catch { }
  Write-Host ('日志文件：{0}' -f $logPath) -ForegroundColor Yellow
  Read-Host '启动失败，按 Enter 关闭窗口'
  exit 1
}

$ApiBaseUrl = $ApiBaseUrl.TrimEnd('/')
$adapterDownloadUrl = "$ApiBaseUrl/downloads/smartbrain_codex_adapter.py"
$launcherDir = if ($ProjectDir) { $ProjectDir } else { Split-Path -Parent $PSCommandPath }

function Select-ProjectDirectory {
  $candidate = $launcherDir
  if (Test-Path -LiteralPath (Join-Path $candidate 'AGENTS.md')) { return $candidate }
  Add-Type -AssemblyName System.Windows.Forms
  $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
  $dialog.Description = '请选择包含 AGENTS.md 的项目文件夹'
  if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw '未选择项目文件夹' }
  return $dialog.SelectedPath
}

$projectDir = Select-ProjectDirectory
$agentsPath = Join-Path $projectDir 'AGENTS.md'
if (-not (Test-Path -LiteralPath $agentsPath)) { throw '项目文件夹中没有 AGENTS.md，请先从智慧大脑项目页面下载' }
$metadataLine = Select-String -LiteralPath $agentsPath -Pattern 'smartbrain-project-id:' | Select-Object -First 1
if ($metadataLine) {
  $localProjectId = ($metadataLine.Line -replace '.*smartbrain-project-id:', '').Replace('-->', '').Trim()
  if ($localProjectId.ToLowerInvariant() -ne $ProjectId.ToLowerInvariant()) { throw ('当前 AGENTS.md 属于项目 {0}，不是本启动器对应的项目' -f $localProjectId) }
} else { Write-Host '检测到旧版 AGENTS.md，使用当前项目绑定继续' -ForegroundColor Yellow }

$adapterPath = Join-Path $projectDir 'smartbrain_codex_adapter.py'
$adapterReady = $false
if (Test-Path -LiteralPath $adapterPath) {
  $adapterReady = (Get-Content -LiteralPath $adapterPath -Raw) -like '*Adapter marker: 2026-09-24-legacy-agents-compat-r2*'
}
if (-not $adapterReady) {
  Write-Host '正在下载 SmartBrain 桌面适配器…'
  Invoke-WebRequest -Uri $adapterDownloadUrl -OutFile $adapterPath -UseBasicParsing
}

$python = (Get-Command python -ErrorAction SilentlyContinue).Source
$pythonPrefix = @()
if (-not $python) {
  $python = (Get-Command py -ErrorAction SilentlyContinue).Source
  $pythonPrefix = @('-3')
}
if (-not $python) { throw '未找到 Python。请先安装 Python 3 后重新双击启动器' }

$credentialDir = Join-Path $env:LOCALAPPDATA 'SmartBrain/CodexAdapter'
$credentialPath = Join-Path $credentialDir 'api-key.dpapi'
if (-not $env:SMARTBRAIN_API_KEY) {
  $secureKey = $null
  if (Test-Path -LiteralPath $credentialPath) {
    try { $secureKey = Get-Content -LiteralPath $credentialPath -Raw | ConvertTo-SecureString } catch { $secureKey = $null }
  }
  if (-not $secureKey) {
    $secureKey = Read-Host -AsSecureString '请输入 SmartBrain Gateway API Key（首次输入后会加密保存在本机用户目录）'
    New-Item -ItemType Directory -Path $credentialDir -Force | Out-Null
    $secureKey | ConvertFrom-SecureString | Set-Content -LiteralPath $credentialPath -Encoding UTF8
  }
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
  try { $env:SMARTBRAIN_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
if (-not $env:SMARTBRAIN_API_KEY) { throw '没有输入 API Key' }

$healthUrl = ('http://127.0.0.1:{0}/health' -f $ListenPort)
$alreadyRunning = $false
$adapterProcess = $null
$adapterLogBase = Join-Path $env:TEMP ('SmartBrain-Adapter-{0}' -f $ListenPort)
$adapterStdoutPath = $adapterLogBase + '.out.log'
$adapterStderrPath = $adapterLogBase + '.err.log'
try {
  $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
  if ($health.project_id -eq $ProjectId) { $alreadyRunning = $true }
  elseif ($health.project_id) { throw ('端口 {0} 已被其他项目占用' -f $ListenPort) }
} catch {
  if ($_.Exception.Message -like '*其他项目占用*') { throw }
}

if (-not $alreadyRunning) {
  $adapterArgs = $pythonPrefix + @($adapterPath, '--api-base-url', $ApiBaseUrl, '--project-id', $ProjectId, '--project-dir', $projectDir, '--listen-port', $ListenPort)
  Remove-Item -LiteralPath $adapterStdoutPath,$adapterStderrPath -Force -ErrorAction SilentlyContinue
  $adapterProcess = Start-Process -FilePath $python -ArgumentList $adapterArgs -WorkingDirectory $projectDir -WindowStyle Hidden -RedirectStandardOutput $adapterStdoutPath -RedirectStandardError $adapterStderrPath -PassThru
  for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 250
    try {
      $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
      if ($health.project_id -eq $ProjectId) { break }
    } catch { }
  }
}

try {
  $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 3
} catch {
  $adapterError = ''
  if (Test-Path -LiteralPath $adapterStderrPath) { $adapterError = (Get-Content -LiteralPath $adapterStderrPath -Raw).Trim() }
  if (-not $adapterError -and (Test-Path -LiteralPath $adapterStdoutPath)) { $adapterError = (Get-Content -LiteralPath $adapterStdoutPath -Raw).Trim() }
  if ($adapterError) { throw ('适配器启动失败：{0}' -f $adapterError) }
  if ($adapterProcess -and $adapterProcess.HasExited) { throw ('适配器启动失败，进程退出码：{0}' -f $adapterProcess.ExitCode) }
  throw
}
if ($health.project_id -ne $ProjectId) { throw '适配器启动失败或项目目录不匹配' }

$codex = (Get-Command codex -ErrorAction SilentlyContinue).Source
if (-not $codex) {
  $codexBin = Join-Path $env:LOCALAPPDATA 'OpenAI/Codex/bin'
  if (Test-Path -LiteralPath $codexBin) {
    $codex = Get-ChildItem -LiteralPath $codexBin -Filter 'codex.exe' -File -Recurse -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 1 -ExpandProperty FullName
  }
}
if (-not $codex) { throw '未找到 Codex。请先安装桌面版 Codex，或将 codex.exe 加入 PATH' }

$codexArgs = @(
  'app', $projectDir,
  '-c', 'model_provider="smartbrain"',
  '-c', 'model_providers.smartbrain.name="smartbrain"',
  '-c', 'model_providers.smartbrain.wire_api="responses"',
  '-c', ('model_providers.smartbrain.base_url="http://127.0.0.1:{0}/v1"' -f $ListenPort),
  '-c', 'model_providers.smartbrain.requires_openai_auth=false'
)
Write-Host ('正在打开 SmartBrain 项目：{0}' -f $projectDir)
& $codex @codexArgs
