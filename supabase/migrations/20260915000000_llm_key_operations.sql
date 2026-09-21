-- Candidate only: enable no employee rollout by migration. Apply under the
-- release gate; these tables preserve mappings after native key deletion.
CREATE TABLE IF NOT EXISTS public.llm_gateway_instances (
  id uuid PRIMARY KEY, endpoint_ref text NOT NULL, base_url text NOT NULL,
  models jsonb NOT NULL CHECK (jsonb_typeof(models)='array' AND jsonb_array_length(models)>0),
  enabled boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS public.llm_member_rollout (
  user_id uuid PRIMARY KEY REFERENCES public.users(id),
  instance_id uuid NOT NULL REFERENCES public.llm_gateway_instances(id),
  enabled boolean NOT NULL DEFAULT false
);
CREATE TABLE IF NOT EXISTS public.llm_key_operations (
  id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES public.users(id),
  instance_id uuid NOT NULL REFERENCES public.llm_gateway_instances(id),
  idempotency_key uuid NOT NULL, request_hash text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('create','revoke','remove')),
  state text NOT NULL CHECK (state IN ('reserved','submitted','confirmed','reconciling','needs_attention','failed_confirmed')),
  credential_id uuid NOT NULL, key_hash text NOT NULL CHECK (key_hash ~ '^[a-f0-9]{64}$'),
  key_prefix text NOT NULL, label text NOT NULL,
  reserved_slot boolean NOT NULL DEFAULT false CHECK (NOT reserved_slot OR kind='create'),
  error_code text, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(user_id,kind,idempotency_key), UNIQUE(id,user_id,instance_id)
);
CREATE TABLE IF NOT EXISTS public.llm_credential_refs (
  id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES public.users(id),
  instance_id uuid NOT NULL REFERENCES public.llm_gateway_instances(id),
  creation_operation_id uuid NOT NULL UNIQUE,
  key_hash text NOT NULL CHECK (key_hash ~ '^[a-f0-9]{64}$'), key_prefix text NOT NULL, label text NOT NULL,
  state text NOT NULL CHECK (state IN ('active','revoking','revoked','removing','removed','needs_attention')),
  hidden_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), verified_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(instance_id,key_hash),
  FOREIGN KEY(creation_operation_id,user_id,instance_id) REFERENCES public.llm_key_operations(id,user_id,instance_id)
);
CREATE INDEX IF NOT EXISTS llm_key_operations_pending_user_idx ON public.llm_key_operations(user_id) WHERE reserved_slot;
CREATE INDEX IF NOT EXISTS llm_credential_refs_visible_user_idx ON public.llm_credential_refs(user_id,created_at DESC) WHERE hidden_at IS NULL;
ALTER TABLE public.llm_gateway_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.llm_member_rollout ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.llm_key_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.llm_credential_refs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.llm_gateway_instances,public.llm_member_rollout,public.llm_key_operations,public.llm_credential_refs FROM PUBLIC;
DO $$ DECLARE target_role text; BEGIN
  FOREACH target_role IN ARRAY ARRAY['anon','authenticated','service_role'] LOOP
    IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=target_role) THEN
      EXECUTE format('REVOKE ALL ON public.llm_gateway_instances,public.llm_member_rollout,public.llm_key_operations,public.llm_credential_refs FROM %I',target_role);
    END IF;
  END LOOP;
END $$;
