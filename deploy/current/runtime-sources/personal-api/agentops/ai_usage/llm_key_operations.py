"""Durable, server-owned one-user/one-active-key operations."""
import hashlib
import json
import secrets
import uuid
from sqlalchemy import text


class KeyOperationError(RuntimeError):
    def __init__(self, code, status_code=409):
        self.code, self.status_code = code, status_code
        super().__init__(code)


def _summary(row):
    return {'operation_id': str(row['id']), 'credential_id': str(row['credential_id']),
            'status': row['state'], 'error_code': row['error_code']}


class KeyOperations:
    def __init__(self, sessions, gateway, *, instance_id):
        self.sessions, self.gateway, self.instance_id = sessions, gateway, str(instance_id)

    def close(self):
        self.gateway.close()

    def creation_enabled(self, *, user_id):
        with self.sessions() as db:
            rows = db.execute(text('''SELECT r.instance_id,r.enabled AS member_enabled,i.enabled,i.models
                FROM public.llm_member_rollout r JOIN public.llm_gateway_instances i ON i.id=r.instance_id
                WHERE r.user_id=:uid'''), {'uid':str(uuid.UUID(str(user_id)))}).mappings().all()
        if not rows:
            return False
        if (len(rows) != 1 or str(rows[0]['instance_id']) != self.instance_id
                or not rows[0]['member_enabled'] or not rows[0]['enabled'] or rows[0]['models'] != self.gateway.models):
            raise KeyOperationError('gateway_not_enabled',503)
        return True

    def owns_credential(self, *, user_id, credential_id):
        with self.sessions() as db:
            return db.execute(text('''SELECT id FROM public.llm_credential_refs
                WHERE id=:id AND user_id=:uid AND instance_id=:iid'''),
                {'id':str(uuid.UUID(str(credential_id))), 'uid':str(uuid.UUID(str(user_id))), 'iid':self.instance_id}).first() is not None

    def create(self, *, user_id, idempotency_key, label):
        if not isinstance(label,str) or not 1 <= len(label.strip()) <= 100 or any(ord(c)<32 or ord(c)==127 for c in label):
            raise KeyOperationError('invalid_label',422)
        label=label.strip()
        user_id, idempotency_key = str(uuid.UUID(str(user_id))), str(uuid.UUID(str(idempotency_key)))
        request_hash = hashlib.sha256(json.dumps([self.instance_id, label, self.gateway.models], separators=(',', ':')).encode()).hexdigest()
        secret = 'sk-' + secrets.token_urlsafe(32)
        row = {'id': str(uuid.uuid4()), 'credential_id': str(uuid.uuid4()), 'uid': user_id,
               'iid': self.instance_id, 'idem': idempotency_key, 'request_hash': request_hash,
               'key_hash': hashlib.sha256(secret.encode()).hexdigest(), 'prefix': secret[:12], 'label': label}
        with self.sessions.begin() as db:
            member = db.execute(text('''SELECT u.id FROM public.users u JOIN auth.users a ON a.id=u.id
                WHERE u.id=:uid AND COALESCE(u.is_active,true) AND a.deleted_at IS NULL
                  AND (a.banned_until IS NULL OR a.banned_until<=now()) FOR UPDATE OF u'''), {'uid': user_id}).first()
            if member is None:
                raise KeyOperationError('member_unavailable', 403)
            rollout = db.execute(text('''SELECT i.models FROM public.llm_member_rollout r
                JOIN public.llm_gateway_instances i ON i.id=r.instance_id
                WHERE r.user_id=:uid AND r.instance_id=:iid AND r.enabled AND i.enabled'''), row).first()
            if rollout is None or rollout.models != self.gateway.models:
                raise KeyOperationError('gateway_not_enabled', 503)
            previous = db.execute(text("SELECT * FROM public.llm_key_operations WHERE user_id=:uid AND kind='create' AND idempotency_key=:idem"), row).mappings().first()
            if previous:
                if previous['request_hash'] != request_hash:
                    raise KeyOperationError('idempotency_conflict')
                return _summary(previous)
            count = db.execute(text('''SELECT
                COALESCE((SELECT max_active_keys FROM public.ai_gateway_key_allowances WHERE user_id=:uid),1) AS allowed,
                (SELECT count(*) FROM public.ai_gateway_keys WHERE user_id=:uid AND is_active)
                +(SELECT count(*) FROM public.llm_credential_refs WHERE user_id=:uid AND state IN ('active','revoking','needs_attention'))
                +(SELECT count(*) FROM public.llm_key_operations WHERE user_id=:uid AND reserved_slot) AS used'''), row).first()
            if count.used >= count.allowed:
                raise KeyOperationError('key_allowance_exhausted')
            db.execute(text('''INSERT INTO public.llm_key_operations
                (id,user_id,instance_id,idempotency_key,request_hash,kind,state,credential_id,key_hash,key_prefix,label,reserved_slot)
                VALUES(:id,:uid,:iid,:idem,:request_hash,'create','submitted',:credential_id,:key_hash,:prefix,:label,true)'''), row)
        # A committed submitted row is the only permission to issue this call.
        # Duplicate requests only return its summary, never reach the gateway.
        try:
            native_ref = self.gateway.create_key(secret=secret, user_id=user_id, operation_id=row['id'], label=label)
            info = self.gateway.lookup_key(row['key_hash'], user_id=user_id, operation_id=row['id'])
            if native_ref != row['key_hash'] or info is None or info['blocked']:
                raise KeyOperationError('gateway_key_unconfirmed', 503)
        except Exception:
            return self._pending(user_id, row['id'])
        response = self._confirm(user_id, row['id'], recovered=False)
        return {**response, 'key': secret}

    def _operation(self, user_id, operation_id):
        with self.sessions() as db:
            row = db.execute(text('''SELECT * FROM public.llm_key_operations
                WHERE id=:id AND user_id=:uid AND instance_id=:iid'''),
                {'id':str(uuid.UUID(str(operation_id))), 'uid':str(uuid.UUID(str(user_id))), 'iid':self.instance_id}).mappings().first()
            if row is None:
                raise KeyOperationError('operation_not_found',404)
            active=db.execute(text('''SELECT u.id FROM public.users u JOIN auth.users a ON a.id=u.id
                WHERE u.id=:uid AND COALESCE(u.is_active,true) AND a.deleted_at IS NULL
                  AND (a.banned_until IS NULL OR a.banned_until<=now())'''),{'uid':str(user_id)}).first()
            if active is None:raise KeyOperationError('member_unavailable',403)
            return dict(row)

    def _pending(self, user_id, operation_id):
        with self.sessions.begin() as db:
            db.execute(text("""UPDATE public.llm_key_operations SET state='reconciling',error_code='gateway_result_unconfirmed',updated_at=now()
                WHERE id=:id AND user_id=:uid AND instance_id=:iid AND state='submitted'"""),
                {'id':operation_id,'uid':user_id,'iid':self.instance_id})
        return _summary(self._operation(user_id,operation_id))

    def _confirm(self, user_id, operation_id, *, recovered):
        with self.sessions.begin() as db:
            op = db.execute(text('''SELECT * FROM public.llm_key_operations
                WHERE id=:id AND user_id=:uid AND instance_id=:iid FOR UPDATE'''),
                {'id':operation_id,'uid':user_id,'iid':self.instance_id}).mappings().one()
            if op['state']=='confirmed':
                return _summary(op)
            if op['state'] not in ('submitted','reconciling') or op['kind']!='create':
                raise KeyOperationError('operation_state_conflict')
            db.execute(text('''INSERT INTO public.llm_credential_refs
                (id,user_id,instance_id,creation_operation_id,key_hash,key_prefix,label,state)
                VALUES(:credential_id,:user_id,:instance_id,:id,:key_hash,:key_prefix,:label,'active')'''), dict(op))
            result = db.execute(text("UPDATE public.llm_key_operations SET state='confirmed',reserved_slot=false,error_code=:error,updated_at=now() WHERE id=:id RETURNING *"),
                                {'id':operation_id,'error':'secret_not_delivered' if recovered else None}).mappings().one()
            response = _summary(result)
        return response

    def reconcile_create(self, *, user_id, operation_id):
        op=self._operation(user_id,operation_id)
        if op['kind']!='create':raise KeyOperationError('operation_kind_conflict')
        if op['state']=='confirmed':return _summary(op)
        try:
            info=self.gateway.lookup_key(op['key_hash'],user_id=str(op['user_id']),operation_id=str(op['id']))
        except Exception:
            return self._pending(str(op['user_id']),str(op['id']))
        if info is None or info['blocked']:
            return self._pending(str(op['user_id']),str(op['id']))
        return self._confirm(str(op['user_id']),str(op['id']),recovered=True)

    def revoke(self, *, user_id, credential_id, idempotency_key):
        return self._change('revoke', user_id, credential_id, idempotency_key)

    def remove(self, *, user_id, credential_id, idempotency_key):
        return self._change('remove', user_id, credential_id, idempotency_key)

    def _change(self, kind, user_id, credential_id, idempotency_key):
        user_id, credential_id, idempotency_key = (str(uuid.UUID(str(v))) for v in (user_id,credential_id,idempotency_key))
        params={'uid':user_id,'cid':credential_id,'iid':self.instance_id,'idem':idempotency_key,'kind':kind}
        request_hash=hashlib.sha256(json.dumps([kind,credential_id,self.instance_id]).encode()).hexdigest()
        with self.sessions.begin() as db:
            member=db.execute(text('''SELECT u.id FROM public.users u JOIN auth.users a ON a.id=u.id
                WHERE u.id=:uid AND COALESCE(u.is_active,true) AND a.deleted_at IS NULL
                  AND (a.banned_until IS NULL OR a.banned_until<=now()) FOR UPDATE OF u'''),params).first()
            if member is None:raise KeyOperationError('member_unavailable',403)
            previous=db.execute(text('''SELECT * FROM public.llm_key_operations
                WHERE user_id=:uid AND kind=:kind AND idempotency_key=:idem'''),params).mappings().first()
            if previous:
                if previous['request_hash']!=request_hash:raise KeyOperationError('idempotency_conflict')
                return _summary(previous)
            key=db.execute(text('''SELECT * FROM public.llm_credential_refs
                WHERE id=:cid AND user_id=:uid AND instance_id=:iid FOR UPDATE'''),params).mappings().first()
            if key is None:raise KeyOperationError('credential_not_found',404)
            final_state='revoked' if kind=='revoke' else 'removed'
            completed=key['state'] in ('revoked','removed') if kind=='revoke' else key['state']=='removed'
            if not completed and key['state']!=('active' if kind=='revoke' else 'revoked'):
                raise KeyOperationError('credential_state_conflict')
            params.update(id=str(uuid.uuid4()),request_hash=request_hash,key_hash=key['key_hash'],prefix=key['key_prefix'],label=key['label'],
                          state='confirmed' if completed else 'submitted',pending_state='revoking' if kind=='revoke' else 'removing')
            result=db.execute(text('''INSERT INTO public.llm_key_operations
                (id,user_id,instance_id,idempotency_key,request_hash,kind,state,credential_id,key_hash,key_prefix,label,reserved_slot)
                VALUES(:id,:uid,:iid,:idem,:request_hash,:kind,:state,:cid,:key_hash,:prefix,:label,false) RETURNING *'''),params).mappings().one()
            if completed:return _summary(result)
            db.execute(text('UPDATE public.llm_credential_refs SET state=:pending_state WHERE id=:cid'),params)
            native_identity={'user_id':user_id,'operation_id':str(key['creation_operation_id'])}
        try:
            method=self.gateway.block_key if kind=='revoke' else self.gateway.delete_blocked_key
            if method(params['key_hash'],**native_identity) is not True:
                raise KeyOperationError('gateway_result_unconfirmed',503)
        except Exception:
            return self._pending(user_id,params['id'])
        return self._finish_change(user_id,params['id'])

    def _finish_change(self, user_id, operation_id):
        with self.sessions.begin() as db:
            op=db.execute(text('''SELECT * FROM public.llm_key_operations
                WHERE id=:id AND user_id=:uid AND instance_id=:iid FOR UPDATE'''),
                {'id':operation_id,'uid':user_id,'iid':self.instance_id}).mappings().one()
            if op['state']=='confirmed':return _summary(op)
            if op['state'] not in ('submitted','reconciling') or op['kind'] not in ('revoke','remove'):
                raise KeyOperationError('operation_state_conflict')
            params={'id':str(op['credential_id']),'uid':user_id,'state':'revoked' if op['kind']=='revoke' else 'removed','hide':op['kind']=='remove'}
            db.execute(text('''UPDATE public.llm_credential_refs SET state=:state,verified_at=now(),
                hidden_at=CASE WHEN :hide THEN COALESCE(hidden_at,now()) ELSE hidden_at END
                WHERE id=:id AND user_id=:uid'''),params)
            result=db.execute(text("UPDATE public.llm_key_operations SET state='confirmed',error_code=NULL,updated_at=now() WHERE id=:id RETURNING *"),{'id':operation_id}).mappings().one()
            return _summary(result)

    def reconcile_change(self, *, user_id, operation_id):
        op=self._operation(user_id,operation_id)
        if op['kind'] not in ('revoke','remove'):raise KeyOperationError('operation_kind_conflict')
        if op['state']=='confirmed':return _summary(op)
        with self.sessions() as db:
            key=db.execute(text('''SELECT creation_operation_id FROM public.llm_credential_refs
                WHERE id=:cid AND user_id=:uid AND instance_id=:iid'''),
                {'cid':str(op['credential_id']),'uid':str(op['user_id']),'iid':self.instance_id}).first()
        if key is None:raise KeyOperationError('credential_not_found',404)
        try:
            info=self.gateway.lookup_key(op['key_hash'],user_id=str(op['user_id']),operation_id=str(key.creation_operation_id))
        except Exception:
            return self._pending(str(op['user_id']),str(op['id']))
        if info is None or (op['kind']=='revoke' and info['blocked']):
            return self._finish_change(str(op['user_id']),str(op['id']))
        return self._pending(str(op['user_id']),str(op['id']))

    def get_operation(self, *, user_id, operation_id):
        return _summary(self._operation(user_id,operation_id))

    def reconcile_pending(self, *, limit=25):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise KeyOperationError('invalid_batch_limit',422)
        with self.sessions() as db:
            rows = db.execute(text('''SELECT id,user_id,kind FROM public.llm_key_operations
                WHERE instance_id=:iid AND state IN ('submitted','reconciling')
                  AND updated_at < now()-interval '30 seconds'
                ORDER BY updated_at,id LIMIT :limit'''), {'iid':self.instance_id,'limit':limit}).mappings().all()
        results=[]
        for row in rows:
            method=self.reconcile_create if row['kind']=='create' else self.reconcile_change
            try:
                results.append(method(user_id=str(row['user_id']),operation_id=str(row['id'])))
            except KeyOperationError as error:
                results.append({'operation_id':str(row['id']),'status':'needs_attention','error_code':error.code})
        return results

    def list_operations(self, *, user_id):
        with self.sessions() as db:
            rows = db.execute(text('''SELECT o.* FROM public.llm_key_operations o
                JOIN public.users u ON u.id=o.user_id JOIN auth.users a ON a.id=u.id
                WHERE o.user_id=:uid AND o.instance_id=:iid
                  AND o.state IN ('submitted','reconciling','needs_attention')
                  AND COALESCE(u.is_active,true) AND a.deleted_at IS NULL
                  AND (a.banned_until IS NULL OR a.banned_until<=now())
                ORDER BY o.created_at,o.id LIMIT 50'''),
                {'uid':str(uuid.UUID(str(user_id))),'iid':self.instance_id}).mappings().all()
        return [_summary(row) for row in rows]

    def list_keys(self, *, user_id):
        uid=str(uuid.UUID(str(user_id)))
        with self.sessions() as db:
            active=db.execute(text('''SELECT u.id FROM public.users u JOIN auth.users a ON a.id=u.id
                WHERE u.id=:uid AND COALESCE(u.is_active,true) AND a.deleted_at IS NULL
                  AND (a.banned_until IS NULL OR a.banned_until<=now())'''),{'uid':uid}).first()
            if active is None:raise KeyOperationError('member_unavailable',403)
            rows=db.execute(text('''SELECT k.id,k.label,k.key_prefix,k.state,k.created_at,i.base_url,i.models
                FROM public.llm_credential_refs k JOIN public.llm_gateway_instances i ON i.id=k.instance_id
                WHERE k.user_id=:uid AND k.instance_id=:iid AND k.hidden_at IS NULL ORDER BY k.created_at DESC,k.id'''),
                {'uid':uid,'iid':self.instance_id}).mappings().all()
        return [{'id':str(r['id']),'label':r['label'],'masked_key':r['key_prefix']+'…','status':r['state'],
                 'is_active':r['state'] in ('active','revoking','needs_attention'),'created_at':r['created_at'].isoformat(),
                 'backend':'litellm','base_url':r['base_url'],'models':r['models']} for r in rows]
