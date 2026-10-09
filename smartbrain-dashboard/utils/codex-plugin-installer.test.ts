import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

import { buildCodexInstaller, buildCodexUpdater } from './codex-plugin-installer';

function decodePowerShell(commandFile: string): string {
  const match = commandFile.match(/-EncodedCommand ([A-Za-z0-9+/=]+)/);
  if (!match) throw new Error('Encoded PowerShell payload is missing');
  return Buffer.from(match[1], 'base64').toString('utf16le');
}

describe('buildCodexInstaller', () => {
  it('offers an updater that needs no new token and keeps the existing credential', () => {
    const commandFile = buildCodexUpdater({
      endpoint: 'https://39.105.79.0/mcp',
      bundleUrl: 'https://39.105.79.0/downloads/smartbrain-company-memory-codex.zip',
      updaterUrl: 'https://39.105.79.0/downloads/SmartBrain-Company-Memory-Update.ps1',
    });
    const script = decodePowerShell(commandFile);
    expect(commandFile.length).toBeLessThan(8000);
    expect(script).toContain('Get-FileHash');
    expect(script).toContain('SmartBrain-Company-Memory-Update.ps1');
    expect(script).not.toContain('sbmcp_');
    expect(script).not.toContain('-Token');
    expect(script).not.toContain('SetEnvironmentVariable');
  });
  it('creates a self-deleting Windows installer for the complete SmartBrain plugin', () => {
    const commandFile = buildCodexInstaller({
      endpoint: 'http://192.168.1.40:8010/mcp',
      token: 'sbmcp_visible_once',
      bundleUrl: 'http://192.168.1.40:3002/downloads/smartbrain-company-memory-codex.zip',
    });

    expect(commandFile).toContain('powershell.exe -NoProfile -ExecutionPolicy Bypass -EncodedCommand');
    expect(commandFile).toContain('del /f /q "%~f0"');
    expect(commandFile.length).toBeLessThan(8000);

    const script = decodePowerShell(commandFile);
    expect(script).toContain('sbmcp_visible_once');
    expect(script).toContain('http://192.168.1.40:8010/mcp');
    expect(script).toContain('smartbrain-company-memory-codex.zip');
    expect(script).toContain('-Token');
    const updater = readFileSync('public/downloads/SmartBrain-Company-Memory-Update.ps1');
    expect(script).toContain(createHash('sha256').update(updater).digest('hex'));
    expect(script).not.toContain('Remove-Item -LiteralPath $root -Recurse');
  });

  it('rejects unsafe endpoints and invalid token values', () => {
    expect(() =>
      buildCodexInstaller({
        endpoint: 'file:///tmp/mcp',
        token: 'sbmcp_visible_once',
        bundleUrl: 'http://192.168.1.40:3002/downloads/plugin.zip',
      }),
    ).toThrow('MCP endpoint');

    expect(() =>
      buildCodexInstaller({
        endpoint: 'http://192.168.1.40:8010/mcp',
        token: 'not-a-wiki-token',
        bundleUrl: 'http://192.168.1.40:3002/downloads/plugin.zip',
      }),
    ).toThrow('MCP token');
  });
});
