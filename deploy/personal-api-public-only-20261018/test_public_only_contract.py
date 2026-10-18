import unittest
from datetime import datetime, timezone
import relay_release_core as core
import relay_remote_runner as runner
from unittest import mock
from types import SimpleNamespace

class PublicOnlyTests(unittest.TestCase):
 def natural(self):
  return {'schema':core.AUTH_SMOKE_SCHEMA,'release':core.RELEASE,'observed_at':'2026-10-18T12:30:00+00:00','new_container_id':'new-cid','verification_kind':'natural_completed_request','successful_completed_requests':1,'public_gateway_authenticated':True,'credential_fingerprint_unchanged':True,'direct_windows_models_status':403,'request_id_sha256':'a'*64,'smoke_summary_sha256':'b'*64}
 def check(self,receipt):
  return core.validate_auth_smoke_receipt(receipt,now=datetime(2026,10,18,12,31,tzinfo=timezone.utc),awaiting_at=datetime(2026,10,18,12,29,tzinfo=timezone.utc),new_container_id='new-cid')
 def test_natural_public_success_requires_no_terminal_key(self):
  self.assertTrue(self.check(self.natural())['public_gateway_authenticated'])
 def test_failed_or_unauthenticated_or_changed_key_never_passes(self):
  for k,v in [('successful_completed_requests',0),('public_gateway_authenticated',False),('credential_fingerprint_unchanged',False),('direct_windows_models_status',200),('new_container_id','old-cid')]:
   r=self.natural();r[k]=v
   with self.subTest(k=k),self.assertRaises(core.GateError): self.check(r)
 def test_capacity_uses_backup_environment(self):
  self.assertEqual(runner.STACK_ENV,runner.CAPACITY_CHECKER.parent/'.env')
 def test_drain_refuses_unknown_or_active_runtime(self):
  good={'status':'ok','concurrency':{'active':0,'waiting':0,'database_in_use':0,'max_active':8,'max_waiting':24,'database_limit':3}}
  self.assertTrue(runner.runtime_drained(good))
  for key in ('active','waiting','database_in_use'):
   bad={'status':'ok','concurrency':dict(good['concurrency'])};bad['concurrency'][key]=1
   self.assertFalse(runner.runtime_drained(bad))
  self.assertFalse(runner.runtime_drained({}))
 def test_recovery_can_stop_unit_when_container_already_stopped(self):
  ops=runner.RealOps.__new__(runner.RealOps)
  ops.store=SimpleNamespace(read=lambda:{'stage':'recovery_started','old_id':'old'})
  ops.name_owner=lambda name:'old'
  ops.inspect=lambda name:{'State':{'Running':False}}
  with mock.patch.object(runner.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as stop:
   ops.stop_unit();stop.assert_called_once()
 def test_recovery_can_stop_unit_during_name_gap(self):
  ops=runner.RealOps.__new__(runner.RealOps)
  ops.store=SimpleNamespace(read=lambda:{'stage':'recovery_started','old_id':'old'})
  ops.name_owner=lambda name:None
  ops.inspect=lambda name:(_ for _ in ()).throw(AssertionError('no named container exists'))
  with mock.patch.object(runner.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as stop:
   ops.stop_unit();stop.assert_called_once()

if __name__=='__main__': unittest.main()
