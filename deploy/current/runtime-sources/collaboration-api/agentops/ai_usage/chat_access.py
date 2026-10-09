"""UUID and live project/consent authorization for private conversation reads."""
import uuid
from sqlalchemy import text
try:
    from agentops.ai_usage.daily_access import DailyOwner,DailyAccessError,select_owner
    from agentops.workday.identity import derive_employee_identity
except ModuleNotFoundError:
    from agentops_local.ai_usage.daily_access import DailyOwner,DailyAccessError,select_owner
    from agentops_local.workday.identity import derive_employee_identity

FROM_SQL="""public.users viewer CROSS JOIN public.users owner_profile
    JOIN auth.users owner_auth ON owner_auth.id=owner_profile.id
    CROSS JOIN public.projects project"""
MANAGES_SQL="""(viewer.is_system_admin IS TRUE OR EXISTS (
    SELECT 1 FROM public.project_members manager JOIN public.user_orgs manager_org
      ON manager_org.user_id=manager.user_id AND manager_org.org_id=project.org_id
    WHERE manager.user_id=viewer.id AND manager.project_id=project.id
      AND manager.role::text IN ('owner','admin') AND manager_org.role::text IN ('owner','admin')
))"""
READABLE_SQL=f"""viewer.is_active IS TRUE AND owner_profile.is_active IS TRUE
    AND (EXISTS (SELECT 1 FROM public.project_members target
      WHERE target.project_id=project.id AND target.user_id=owner_profile.id)
      OR (viewer.id=owner_profile.id AND viewer.is_system_admin IS TRUE))
    AND (viewer.id=owner_profile.id OR
      (owner_profile.ai_detail_visible_to_admin IS TRUE AND {MANAGES_SQL}))"""


def resolve_project_selection(orm, *, caller_user_id,project_id,requested_owner=None):
    caller=str(uuid.UUID(str(caller_user_id)));project=str(uuid.UUID(str(project_id)))
    rows=orm.execute(text(f'''SELECT owner_profile.id::text AS user_id,owner_auth.email,
        owner_profile.full_name,owner_profile.nickname,owner_profile.ai_detail_visible_to_admin,
        {MANAGES_SQL} AS manages FROM {FROM_SQL}
        WHERE viewer.id=CAST(:caller AS uuid) AND project.id=CAST(:project AS uuid) AND {READABLE_SQL}
        ORDER BY owner_profile.id'''),{'caller':caller,'project':project}).all()
    owners=[]
    for row in rows:
        alias,name=derive_employee_identity(user_id=uuid.UUID(row.user_id),email=row.email or '',
            full_name=row.nickname or row.full_name)
        owners.append(DailyOwner(row.user_id,alias,name,row.email or '',bool(row.ai_detail_visible_to_admin),bool(row.manages)))
    own=next((owner for owner in owners if owner.user_id==caller),None)
    if own is None:raise DailyAccessError(403,'Active project membership is required')
    if requested_owner:
        return select_owner(owners,caller_user_id=caller,requested_owner=requested_owner)
    # Keep the project manager's aggregate view, restricted to the currently
    # consenting owners. Regular members default to their own UUID.
    return None if own.caller_is_admin else own
