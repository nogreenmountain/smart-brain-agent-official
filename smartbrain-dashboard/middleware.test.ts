import {describe,expect,it} from 'vitest';
import {NextRequest} from 'next/server';
import {middleware} from './middleware';

describe('retired adapter downloads',()=>{
  it.each(['smartbrain_codex_adapter.py','Start-SmartBrainCodexAdapter.ps1',
    'Start-SmartBrain-CodexProject.ps1','Start-SmartBrain-Codex-Project.cmd'])('returns 410 without cache for %s',(filename)=>{
    const response=middleware(new NextRequest(`https://brain.example/downloads/${filename}?cache=fresh`));
    expect(response.status).toBe(410);
    expect(response.headers.get('cache-control')).toBe('no-store');
  });
  it.each(['/admin','/downloads/smartbrain-root-ca.crt','/downloads/SmartBrainMonitorRemoval.exe'])('preserves unrelated paths %s',(pathname)=>{
    const response=middleware(new NextRequest(`https://brain.example${pathname}`));
    expect(response.headers.get('x-middleware-next')).toBe('1');
  });
});
