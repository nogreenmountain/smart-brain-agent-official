"""Dedicated registered-member personal gateway entry; no business worker startup."""
import os
from agentops.api.routes.v4 import ai_gateway
from agentops.api.personal_gateway_scope import allowed_users, build_app

app = build_app(ai_gateway, allowed_users(os.environ['SB_GATEWAY_ALLOWED_USER_IDS']))

from agentops.api.routes.v4.project_collaboration import router as collaboration_router
app.include_router(collaboration_router, prefix='/v4')
