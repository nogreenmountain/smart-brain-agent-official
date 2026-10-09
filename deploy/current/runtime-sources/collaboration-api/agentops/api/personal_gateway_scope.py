"""Explicit registered-member release scope with current account checks."""
import uuid


def allowed_users(value: str) -> frozenset[str]:
    entries = value.split(',')
    if not value or len(set(entries)) != len(entries):
        raise ValueError('A nonempty list of distinct approved gateway users is required')
    if any(str(uuid.UUID(entry)) != entry for entry in entries):
        raise ValueError('Canonical approved gateway user IDs required')
    return frozenset(entries)


def build_app(route, users):
    from fastapi import Depends, FastAPI, HTTPException, Request
    from sqlalchemy.orm import Session
    from sqlalchemy import text

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
            # Completion receipts remain valid after revocation. The original
            # endpoint binds the receipt, member and immutable event atomically.
            route._trusted_gateway(request)
        else:
            require_user(route._gateway_claims(request, orm).user_id, orm)

    app.include_router(route.router, prefix='/v4', dependencies=[Depends(browser_scope)])
    app.include_router(route.device_router, prefix='/v4', dependencies=[Depends(device_scope)])

    @app.get('/health')
    def health():
        return {'status': 'ok', 'scope': 'personal-api-registered', 'member_count': len(users)}

    return app
