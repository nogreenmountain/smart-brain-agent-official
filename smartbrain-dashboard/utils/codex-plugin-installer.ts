export const CODEX_PLUGIN_BUNDLE_PATH = '/downloads/smartbrain-company-memory-codex.zip';
export const CODEX_PLUGIN_VERSION = '0.2.1+codex.20261008';
export const CODEX_UPDATER_PATH = '/downloads/SmartBrain-Company-Memory-Update.ps1';
const CODEX_UPDATER_SHA256 = 'a29dbf9f42c2d87f4fe7e4f5457d02997a9433ab3aa2b1191d81ad166219a2f7';

interface CodexUpdaterOptions {
  endpoint: string;
  bundleUrl: string;
  updaterUrl?: string;
}
interface CodexInstallerOptions extends CodexUpdaterOptions { token: string; }

function requireHttpUrl(value: string, label: string): string {
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error(`${label} is invalid`);
  }
  if ((parsed.protocol !== 'http:' && parsed.protocol !== 'https:') || parsed.username || parsed.password) {
    throw new Error(`${label} must use HTTP or HTTPS`);
  }
  return parsed.toString();
}

function quotePowerShell(value: string): string {
  return `'${value.replaceAll("'", "''")}'`;
}

function encodeUtf16Le(value: string): string {
  let binary = '';
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    binary += String.fromCharCode(code & 0xff, code >> 8);
  }
  return btoa(binary);
}

function buildCommand({ endpoint, bundleUrl, updaterUrl }: CodexUpdaterOptions, token?: string): string {
  const safeEndpoint = requireHttpUrl(endpoint, 'MCP endpoint');
  const safeBundleUrl = requireHttpUrl(bundleUrl, 'Plugin bundle URL');
  const safeUpdaterUrl = requireHttpUrl(updaterUrl || new URL(CODEX_UPDATER_PATH, safeBundleUrl).toString(), 'Updater URL');
  if (token !== undefined && !/^sbmcp_[A-Za-z0-9._~-]+$/.test(token)) {
    throw new Error('MCP token is invalid');
  }

  const script = [
    "$ErrorActionPreference='Stop'",
    'try {',
    "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)",
    "Import-Module (Join-Path $PSHOME 'Modules\\Microsoft.PowerShell.Utility\\Microsoft.PowerShell.Utility.psd1') -Force",
    `$endpoint=${quotePowerShell(safeEndpoint)}`,
    `$bundle=${quotePowerShell(safeBundleUrl)}`,
    `$updater=${quotePowerShell(safeUpdaterUrl)}`,
    "$scriptFile=Join-Path $env:TEMP ('smartbrain-update-'+[Guid]::NewGuid().ToString('N')+'.ps1')",
    '[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12',
    "Invoke-WebRequest -Uri $updater -OutFile $scriptFile -UseBasicParsing -Headers @{'Cache-Control'='no-cache'}",
    `if((Get-FileHash -LiteralPath $scriptFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne '${CODEX_UPDATER_SHA256}'){throw 'Updater integrity check failed.'}`,
    `& $scriptFile -Endpoint $endpoint -BundleUrl $bundle${token === undefined ? '' : ` -Token ${quotePowerShell(token)}`}`,
    'Remove-Item -LiteralPath $scriptFile -Force',
    "Read-Host 'Press Enter to close'|Out-Null",
    'exit 0',
    '} catch {',
    "Write-Host ('Installation failed: '+$_.Exception.Message) -ForegroundColor Red",
    "Read-Host 'Press Enter to close'|Out-Null",
    'exit 1',
    '}',
  ].join(';');

  const payload = encodeUtf16Le(script);
  const commandFile = [
    '@echo off',
    'chcp 65001 >nul',
    `powershell.exe -NoProfile -ExecutionPolicy Bypass -EncodedCommand ${payload}`,
    'set "SMARTBRAIN_INSTALL_EXIT=%ERRORLEVEL%"',
    'if "%SMARTBRAIN_INSTALL_EXIT%"=="0" start "" /b cmd /c ping 127.0.0.1 -n 2 ^>nul ^& del /f /q "%~f0"',
    'exit /b %SMARTBRAIN_INSTALL_EXIT%',
    '',
  ].join('\r\n');

  if (commandFile.length >= 8000) {
    throw new Error('Generated installer exceeds the Windows command length limit');
  }
  return commandFile;
}

export function buildCodexInstaller(options: CodexInstallerOptions): string {
  return buildCommand(options, options.token);
}

export function buildCodexUpdater(options: CodexUpdaterOptions): string {
  return buildCommand(options);
}

function downloadCommand(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'application/x-msdos-program;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export function downloadCodexInstaller(options: CodexInstallerOptions): void {
  downloadCommand(buildCodexInstaller(options), 'SmartBrain-Company-Memory-Setup.cmd');
}

export function downloadCodexUpdater(options: CodexUpdaterOptions): void {
  downloadCommand(buildCodexUpdater(options), 'SmartBrain-Company-Memory-Update.cmd');
}
