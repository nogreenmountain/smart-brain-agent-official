"""Live UUID authorization for private daily reports and their owner options."""
from dataclasses import dataclass
import uuid
from sqlalchemy import text
try:
    from agentops.workday.identity import derive_employee_identity
except ModuleNotFoundError:
    from agentops_local.workday.identity import derive_employee_identity


class DailyAccessError(Exception):
    def __init__(self,status_code,detail):
        super().__init__(detail)
        self.status_code=status_code
        self.detail=detail


@dataclass(frozen=True)
class DailyOwner:
    user_id: str
    employee_id: str
    name: str
    email: str
    detail_visible_to_admin: bool
    caller_is_admin: bool


MANAGED_PROJECT_SQL="""EXISTS (
    SELECT 1 FROM public.user_orgs caller_org
    JOIN public.projects project ON project.org_id=caller_org.org_id
    JOIN public.project_members caller ON caller.project_id=project.id AND caller.user_id=caller_org.user_id
    JOIN public.project_members target ON target.project_id=project.id
    WHERE caller_org.user_id=viewer.id AND target.user_id=owner_profile.id
      AND caller_org.role::text IN ('owner','admin') AND caller.role::text IN ('owner','admin')
)"""
CALLER_ADMIN_SQL="""(viewer.is_system_admin IS TRUE OR EXISTS (
    SELECT 1 FROM public.user_orgs caller_org
    JOIN public.projects project ON project.org_id=caller_org.org_id
    JOIN public.project_members caller ON caller.project_id=project.id AND caller.user_id=caller_org.user_id
    WHERE caller_org.user_id=viewer.id AND caller_org.role::text IN ('owner','admin')
      AND caller.role::text IN ('owner','admin')
))"""
OWNER_FROM_SQL="""public.users viewer JOIN auth.users va ON va.id=viewer.id
    CROSS JOIN public.users owner_profile JOIN auth.users oa ON oa.id=owner_profile.id"""
OWNER_FILTER_SQL=f"""viewer.id=CAST(:caller AS uuid)
    AND viewer.is_active IS TRUE AND owner_profile.is_active IS TRUE
    AND (owner_profile.id=viewer.id OR (
        owner_profile.ai_detail_visible_to_admin IS TRUE
        AND oa.email IS NOT NULL AND lower(oa.email)<>'admin@agentops.local'
        AND ((viewer.is_system_admin IS TRUE AND EXISTS (
            SELECT 1 FROM public.project_members target WHERE target.user_id=owner_profile.id
        )) OR {MANAGED_PROJECT_SQL})
    ))"""

# Check the entire immutable owner/day input, not only citations selected by the
# model. A summary can disclose uncited context. A newly arrived restricted
# source may conservatively hide the whole report until it is reviewed.
REPORT_PROJECT_FILTER_SQL="""NOT EXISTS (
    SELECT 1 FROM public.ai_gateway_admissions input_source
    WHERE input_source.user_id=r.owner_user_id AND input_source.delivered_at IS NOT NULL
      AND input_source.event_sha256 IS NOT NULL
      AND input_source.event_payload->'content_complete'='true'::jsonb
      AND (input_source.event_payload->>'status_code')::integer>=200
      AND (input_source.event_payload->>'status_code')::integer<400
      AND ((COALESCE((input_source.event_payload->>'completed_at')::timestamptz,
                    (input_source.event_payload->>'started_at')::timestamptz,
                    input_source.delivered_at) AT TIME ZONE 'Asia/Shanghai')::date=r.work_date
           OR r.source_session_ids ? input_source.id::text)
      AND input_source.event_payload->>'project_id' IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM public.projects source_project
        JOIN public.project_members source_owner ON source_owner.project_id=source_project.id
        WHERE source_project.id::text=input_source.event_payload->>'project_id'
          AND source_owner.user_id=r.owner_user_id
          AND (viewer.id=r.owner_user_id OR viewer.is_system_admin IS TRUE OR EXISTS (
            SELECT 1 FROM public.project_members source_admin
            JOIN public.user_orgs source_org ON source_org.user_id=source_admin.user_id
              AND source_org.org_id=source_project.org_id
            WHERE source_admin.project_id=source_project.id AND source_admin.user_id=viewer.id
              AND source_admin.role::text IN ('owner','admin') AND source_org.role::text IN ('owner','admin')
          ))
      )
)"""


def visible_owners(orm, *, caller_user_id):
    caller=str(uuid.UUID(str(caller_user_id)))
    rows=orm.execute(text(f'''SELECT owner_profile.id::text AS user_id,oa.email,
        owner_profile.full_name,owner_profile.nickname,owner_profile.ai_detail_visible_to_admin,
        {CALLER_ADMIN_SQL} AS caller_is_admin
        FROM {OWNER_FROM_SQL} WHERE {OWNER_FILTER_SQL}
        ORDER BY COALESCE(NULLIF(BTRIM(owner_profile.nickname),''),owner_profile.full_name,oa.email),
            oa.email,owner_profile.id'''),{'caller':caller}).all()
    owners=[]
    for row in rows:
        alias,name=derive_employee_identity(user_id=uuid.UUID(row.user_id),email=row.email or '',
            full_name=row.nickname or row.full_name)
        owners.append(DailyOwner(row.user_id,alias,name,row.email or '',
            bool(row.ai_detail_visible_to_admin),bool(row.caller_is_admin)))
    if not any(owner.user_id==caller for owner in owners):
        raise DailyAccessError(403,'An active account is required')
    return owners


def select_owner(owners, *, caller_user_id, requested_owner):
    caller=str(uuid.UUID(str(caller_user_id)))
    requested=str(requested_owner or caller).strip().casefold()
    exact=[owner for owner in owners if owner.user_id.casefold()==requested]
    if len(exact)==1:
        return exact[0]
    matches=[owner for owner in owners if requested in {owner.employee_id.casefold(),owner.email.casefold()}]
    if len({owner.user_id for owner in matches})>1:
        raise DailyAccessError(409,'Ambiguous employee alias; select the user UUID')
    if matches:
        return matches[0]
    raise DailyAccessError(404,'Daily report owner is not available in your current scope')


def resolve_owner(orm, *, caller_user_id, requested_owner):
    return select_owner(visible_owners(orm,caller_user_id=caller_user_id),
        caller_user_id=caller_user_id,requested_owner=requested_owner)


def read_reports(orm, *, caller_user_id, owner_user_id, start_date, end_date):
    params={'caller':str(uuid.UUID(str(caller_user_id))),'owner':str(uuid.UUID(str(owner_user_id))),
            'start_date':start_date,'end_date':end_date}
    # This migration is not yet deployed everywhere. Once present, its stored
    # dependencies remain enforced even while CC consumption is disabled.
    cc_ready=orm.execute(text("SELECT to_regclass('public.cc_daily_report_sources') IS NOT NULL")).scalar_one()
    cc_filter='TRUE'
    if cc_ready:
        cc_filter='''NOT EXISTS (
          SELECT 1 FROM public.cc_daily_report_sources dependency
          JOIN public.cc_input_revisions input ON input.id=dependency.revision_id
          LEFT JOIN public.cc_input_heads head ON head.session_id=dependency.session_id
          WHERE dependency.owner_user_id=r.owner_user_id AND dependency.work_date=r.work_date
            AND (head.revision_id IS DISTINCT FROM dependency.revision_id OR (dependency.included AND NOT EXISTS (
              SELECT 1 FROM public.projects source_project
              JOIN public.project_members source_owner ON source_owner.project_id=source_project.id
              WHERE source_project.id=input.project_id AND source_owner.user_id=r.owner_user_id
                AND (viewer.id=r.owner_user_id OR viewer.is_system_admin IS TRUE OR EXISTS (
                  SELECT 1 FROM public.project_members source_admin
                  JOIN public.user_orgs source_org ON source_org.user_id=source_admin.user_id AND source_org.org_id=source_project.org_id
                  WHERE source_admin.project_id=source_project.id AND source_admin.user_id=viewer.id
                    AND source_admin.role::text IN ('owner','admin') AND source_org.role::text IN ('owner','admin')
                ))
            )))
        )'''
    # This predicate is evaluated with the report rows, not an earlier cached
    # roster. Unowned history has no matching UUID and can never enter the result.
    return orm.execute(text(f'''SELECT r.id,r.owner_user_id,r.work_date,r.employee_id,r.employee_name,
        r.report_markdown,r.work_items,r.source_count,r.model,r.generated_at
        FROM public.ai_daily_work_logs r
        WHERE r.owner_user_id=CAST(:owner AS uuid) AND r.work_date>=:start_date AND r.work_date<=:end_date
          AND r.status='ready' AND EXISTS (
            SELECT 1 FROM {OWNER_FROM_SQL} WHERE owner_profile.id=r.owner_user_id AND {OWNER_FILTER_SQL}
              AND {REPORT_PROJECT_FILTER_SQL}
              AND {cc_filter}
          ) ORDER BY r.work_date DESC,r.id'''),params).all()
