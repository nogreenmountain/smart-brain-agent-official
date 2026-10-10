import {NextRequest, NextResponse} from 'next/server';

const retiredPaths = new Set([
  '/downloads/smartbrain_codex_adapter.py',
  '/downloads/Start-SmartBrainCodexAdapter.ps1',
  '/downloads/Start-SmartBrain-CodexProject.ps1',
  '/downloads/Start-SmartBrain-Codex-Project.cmd',
]);

export function middleware(request: NextRequest) {
  if (retiredPaths.has(request.nextUrl.pathname)) {
    return new NextResponse('This project adapter download has been retired.\n', {
      status: 410, headers: {'Cache-Control': 'no-store', 'Content-Type': 'text/plain; charset=utf-8'},
    });
  }
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/downloads/smartbrain_codex_adapter.py',
    '/downloads/Start-SmartBrainCodexAdapter.ps1',
    '/downloads/Start-SmartBrain-CodexProject.ps1',
    '/downloads/Start-SmartBrain-Codex-Project.cmd',
  ],
};
