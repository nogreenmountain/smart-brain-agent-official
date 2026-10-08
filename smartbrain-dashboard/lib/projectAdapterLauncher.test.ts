import { describe, expect, it } from 'vitest';

import { buildProjectAdapterLauncher } from './projectAdapterLauncher';

describe('project adapter launcher', () => {
  it('embeds only the project binding and opens Codex with a local provider', () => {
    const files = buildProjectAdapterLauncher({
      apiBaseUrl: 'https://brain.example/',
      projectId: '11111111-1111-1111-1111-111111111111',
      port: 30101,
    });
    expect(files.ps1).toContain("$apiBaseUrl = 'https://brain.example'");
    expect(files.ps1).toContain("$projectId = '11111111-1111-1111-1111-111111111111'");
    expect(files.ps1).toContain("'app', $projectDir");
    expect(files.ps1).toContain('127.0.0.1:30101/v1');
    expect(files.ps1).not.toContain('sbk_');
    expect(files.cmd).toContain('ExecutionPolicy Bypass');
    expect(files.cmd).toContain('Start-SmartBrain-CodexProject.ps1');
    expect(files.cmd).toContain('Invoke-WebRequest');
    expect(files.cmd).toContain('SB_PROJECT_DIR');
    expect(files.cmd).toContain('$rc=$LASTEXITCODE');
    expect(files.cmd).toContain('if not "%ERRORLEVEL%"=="0" pause');
    expect(files.ps1).toContain("$logPath = Join-Path $env:TEMP");
    expect(files.ps1).toContain("启动失败，按 Enter 关闭窗口");
    expect(files.ps1).toContain("OpenAI/Codex/bin");
    expect(files.ps1).toContain("未找到 Codex");
    expect(files.ps1).toContain("$metadataLine = Select-String");
    expect(files.ps1).toContain("检测到旧版 AGENTS.md");
    expect(files.ps1).toContain("$adapterStderrPath");
    expect(files.cmd.length).toBeLessThan(4000);
  });
});
