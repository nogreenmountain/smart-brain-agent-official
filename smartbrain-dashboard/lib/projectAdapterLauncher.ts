export interface ProjectAdapterLauncherInput {
  apiBaseUrl: string;
  adapterDownloadUrl?: string;
  projectId: string;
  port: number;
}

function psQuote(value: string): string {
  return `'${value.replaceAll("'", "''")}'`;
}

export function buildProjectAdapterLauncher(input: ProjectAdapterLauncherInput): { ps1: string; cmd: string } {
  const apiBaseUrl = psQuote(input.apiBaseUrl.replace(/\/$/, ''));
  const adapterDownloadUrl = psQuote((input.adapterDownloadUrl ?? `${input.apiBaseUrl.replace(/\/$/, '')}/downloads/smartbrain_codex_adapter.py`));
  const projectId = psQuote(input.projectId);
  const port = String(input.port);
  const ps1 = `# SmartBrain 项目一键启动器（自动生成，请勿提交到仓库）
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
$apiBaseUrl = ${apiBaseUrl}
$adapterDownloadUrl = ${adapterDownloadUrl}
$projectId = ${projectId}
$listenPort = ${port}
$launcherDir = Split-Path -Parent $PSCommandPath

function Select-ProjectDirectory {
  $candidate = $launcherDir
  if (Test-Path (Join-Path $candidate 'AGENTS.md')) { return $candidate }
  Add-Type -AssemblyName System.Windows.Forms
  $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
  $dialog.Description = '请选择包含 AGENTS.md 的项目文件夹'
  if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw '未选择项目文件夹' }
  return $dialog.SelectedPath
}

$projectDir = Select-ProjectDirectory
$agentsPath = Join-Path $projectDir 'AGENTS.md'
if (-not (Test-Path $agentsPath)) { throw '项目文件夹中没有 AGENTS.md，请先从智慧大脑项目页面下载' }
$metadataLine = Select-String -LiteralPath $agentsPath -Pattern 'smartbrain-project-id:' | Select-Object -First 1
if ($metadataLine) {
  $localProjectId = ($metadataLine.Line -replace '.*smartbrain-project-id:', '').Replace('-->', '').Trim()
  if ($localProjectId.ToLowerInvariant() -ne $projectId.ToLowerInvariant()) { throw ('当前 AGENTS.md 属于项目 {0}，不是本启动器对应的项目' -f $localProjectId) }
} else { Write-Host '检测到旧版 AGENTS.md，使用当前项目绑定继续' -ForegroundColor Yellow }

$adapterPath = Join-Path $projectDir 'smartbrain_codex_adapter.py'
if (-not (Test-Path $adapterPath)) {
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

$credentialDir = Join-Path $env:LOCALAPPDATA 'SmartBrain\\CodexAdapter'
$credentialPath = Join-Path $credentialDir 'api-key.dpapi'
if (-not $env:SMARTBRAIN_API_KEY) {
  $secureKey = $null
  if (Test-Path $credentialPath) {
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

$healthUrl = ('http://127.0.0.1:{0}/health' -f $listenPort)
$alreadyRunning = $false
$adapterProcess = $null
$adapterLogBase = Join-Path $env:TEMP ('SmartBrain-Adapter-{0}' -f $listenPort)
$adapterStdoutPath = $adapterLogBase + '.out.log'
$adapterStderrPath = $adapterLogBase + '.err.log'
try {
  $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
  if ($health.project_id -eq $projectId) { $alreadyRunning = $true }
  elseif ($health.project_id) { throw ('端口 {0} 已被其他项目占用' -f $listenPort) }
} catch {
  if ($_.Exception.Message -like '*其他项目占用*') { throw }
}

if (-not $alreadyRunning) {
  $adapterArgs = $pythonPrefix + @($adapterPath, '--api-base-url', $apiBaseUrl, '--project-id', $projectId, '--project-dir', $projectDir, '--listen-port', $listenPort)
  Remove-Item -LiteralPath $adapterStdoutPath,$adapterStderrPath -Force -ErrorAction SilentlyContinue
  $adapterProcess = Start-Process -FilePath $python -ArgumentList $adapterArgs -WorkingDirectory $projectDir -WindowStyle Hidden -RedirectStandardOutput $adapterStdoutPath -RedirectStandardError $adapterStderrPath -PassThru
  for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 250
    try {
      $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
      if ($health.project_id -eq $projectId) { break }
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
if ($health.project_id -ne $projectId) { throw '适配器启动失败或项目目录不匹配' }

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
  '-c', 'model_providers.smartbrain.base_url="http://127.0.0.1:${port}/v1"',
  '-c', 'model_providers.smartbrain.requires_openai_auth=false'
)
Write-Host ('正在打开 SmartBrain 项目：{0}' -f $projectDir)
& $codex @codexArgs
`;
  const encoded = btoa(String.fromCharCode(...new TextEncoder().encode(ps1)));
  // Windows PowerShell 5.1 treats a UTF-8 script without a BOM as the local
  // ANSI code page.  The generated script contains Chinese strings, so write
  // it with a BOM before invoking it from the .cmd wrapper.
  const launcherDownloadUrl = psQuote(`${input.apiBaseUrl.replace(/\/$/, '')}/downloads/Start-SmartBrain-CodexProject.ps1`);
  const cmd = `@echo off\r\nset "SB_TMP=%TEMP%\\SmartBrain-Codex-%RANDOM%.ps1"\r\nset "SB_PROJECT_DIR=%~dp0"\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$url=${launcherDownloadUrl}; Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $env:SB_TMP; & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $env:SB_TMP -ApiBaseUrl ${apiBaseUrl} -ProjectId ${projectId} -ListenPort ${port} -ProjectDir $env:SB_PROJECT_DIR; $rc=$LASTEXITCODE; Remove-Item -LiteralPath $env:SB_TMP -Force; exit $rc"\r\nif not "%ERRORLEVEL%"=="0" pause\r\n`;
  return { ps1, cmd };
}
