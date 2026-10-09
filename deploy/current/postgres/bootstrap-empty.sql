\set ON_ERROR_STOP on
-- Only for a brand-new empty business database. No accounts or passwords.
INSERT INTO public.orgs(id, name)
VALUES ('c0000000-0000-0000-0000-000000000000', 'SmartBrain')
ON CONFLICT (id) DO NOTHING;
