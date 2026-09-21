"""One quota expression for management, legacy creation and approval views."""
import os


def key_count_sql(owner):
    # These are SQL expressions chosen by our callers, never request input.
    if owner not in (':uid', 'r.user_id'):
        raise ValueError('Unsupported quota owner expression')
    legacy = f'(SELECT count(*) FROM public.ai_gateway_keys k WHERE k.user_id={owner} AND k.is_active)'
    if os.getenv('SB_LLM_GATEWAY_MANAGEMENT_ENABLED') != '1':
        return legacy
    return legacy + f'''
        +(SELECT count(*) FROM public.llm_credential_refs c WHERE c.user_id={owner} AND c.state IN ('active','revoking','needs_attention'))
        +(SELECT count(*) FROM public.llm_key_operations o WHERE o.user_id={owner} AND o.reserved_slot)'''
