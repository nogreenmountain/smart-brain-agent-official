"""Explicit registered-member release scope with current account checks."""
import uuid


def allowed_users(value: str) -> frozenset[str]:
    entries = value.split(',')
    if not value or len(set(entries)) != len(entries):
        raise ValueError('A nonempty list of distinct approved gateway users is required')
    if any(str(uuid.UUID(entry)) != entry for entry in entries):
        raise ValueError('Canonical approved gateway user IDs required')
    return frozenset(entries)


def build_app(route, users, *, usage_route=None):
    from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    app = FastAPI(docs_url=None, openapi_url=None)

    def require_user(user, orm):
        if str(user) not in users:
            raise HTTPException(403, 'Personal API is limited to registered release members',
                                headers={'Cache-Control': 'no-store'})
        current = orm.execute(text('''
            SELECT au.id FROM auth.users au JOIN public.users pu ON pu.id=au.id
            WHERE au.id=:uid AND COALESCE(pu.is_active,true)
              AND au.deleted_at IS NULL AND NOT COALESCE(au.is_anonymous,false)
              AND (au.banned_until IS NULL OR au.banned_until<=now())
        '''), {'uid': str(user)}).first()
        if current is None:
            raise HTTPException(403, 'Registered account is unavailable',
                                headers={'Cache-Control': 'no-store'})

    def browser_scope(request: Request, orm: Session = Depends(route.get_orm_session)):
        require_user(route._session_user(request), orm)

    def device_scope(request: Request, orm: Session = Depends(route.get_orm_session)):
        suffix = request.url.path.rsplit('/', 1)[-1]
        if suffix == 'events':
            raise HTTPException(410, 'Trusted gateway delivery required')
        if suffix == 'trusted-events':
            route._trusted_gateway(request)
        else:
            claim = route._gateway_claims(request, orm)
            request.state.gateway_claim = claim
            require_user(claim.user_id, orm)

    if usage_route is None:
        app.include_router(route.router, prefix='/v4', dependencies=[Depends(browser_scope)])
        app.include_router(route.device_router, prefix='/v4', dependencies=[Depends(device_scope)])
    else:
        paths = {'/ai-usage/options', '/ai-usage/records',
                 '/ai-usage/gateway-requests/{request_id}/content'}
        reads = APIRouter()
        reads.routes = [item for item in usage_route.router.routes
                        if item.path in paths and item.methods == {'GET'}]
        if len(reads.routes) != len(paths) or {item.path for item in reads.routes} != paths:
            raise ValueError('The exact three workday read routes are required')
        app.include_router(reads, prefix='/v4', dependencies=[Depends(browser_scope)])

    if usage_route is None:
        from agentops.api.personal_gateway_proxy import proxy_request
        app.api_route('/v1/{path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
                      dependencies=[Depends(device_scope)])(proxy_request)

    @app.get('/health')
    def health():
        return {'status': 'ok', 'scope': 'workday-gateway-read' if usage_route else 'personal-api-registered',
                'member_count': len(users)}

    return app
