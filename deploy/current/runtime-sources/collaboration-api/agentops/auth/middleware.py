from collections.abc import Callable

from fastapi import HTTPException, Request, Response
from fastapi.routing import APIRoute
from redis.exceptions import RedisError
from sqlalchemy import text

from agentops.api.log_config import logger
from agentops.common.orm import session_scope

from .environment import AUTH_COOKIE_NAME, AUTH_EXTEND_SESSIONS
from .exceptions import AuthException
from .session import Session
from .views import SESSION_SERVICE_UNAVAILABLE_DETAIL, _decode_session_cookie


def _require_active_team_member(session: Session) -> None:
    """Reject and expire cached sessions after a team member is disabled."""
    with session_scope() as orm:
        row = orm.execute(
            text("""
                SELECT COALESCE(is_active, true) AS is_active
                FROM public.users
                WHERE id = :user_id
            """),
            {"user_id": str(session.user_id)},
        ).first()
    if row is not None and not bool(row.is_active):
        try:
            session.expire()
        except RedisError as exc:
            logger.warning(
                "Redis session invalidation unavailable for disabled member (%s)",
                type(exc).__name__,
            )
        raise AuthException("Team member account is disabled.")


class AuthenticatedRoute(APIRoute):
    """Authenticated API route with immediate team-member deactivation checks."""

    def _get_session(self, request: Request) -> Session:
        if not (cookie := request.cookies.get(AUTH_COOKIE_NAME)):
            raise AuthException("User is not authenticated.")

        try:
            session = _decode_session_cookie(cookie)
        except RedisError as exc:
            logger.warning("Redis session lookup unavailable (%s)", type(exc).__name__)
            raise HTTPException(
                status_code=503,
                detail=SESSION_SERVICE_UNAVAILABLE_DETAIL,
            ) from exc

        if not session:
            raise AuthException("User's session has expired.")

        _require_active_team_member(session)

        if AUTH_EXTEND_SESSIONS:
            try:
                session.extend()
            except RedisError as exc:
                logger.warning("Redis session extension unavailable (%s)", type(exc).__name__)
                raise HTTPException(
                    status_code=503,
                    detail=SESSION_SERVICE_UNAVAILABLE_DETAIL,
                ) from exc

        return session

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                request.state.session = self._get_session(request)
            except AuthException as exc:
                if not getattr(self.endpoint, "is_public", False):
                    raise exc

            return await original_route_handler(request)

        return custom_route_handler
