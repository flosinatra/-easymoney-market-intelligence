import unittest
from datetime import datetime, timezone
from collection_reconciliation import reconcile

class CollectionReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,6,12,tzinfo=timezone.utc)
        self.snapshot={'retrieved_at_utc':'2026-11-06T11:00:00+00:00'}
        self.receipt={'attempted_at_utc':'2026-11-06T11:00:00+00:00','collection_status':'COMPLETE'}
    def test_matched_success(self):
        self.assertTrue(reconcile(self.snapshot,self.receipt,self.now)['latest_attempt_produced_snapshot'])
    def test_failed_attempt_retains_but_does_not_claim_success(self):
        self.receipt.update(collection_status='FAILED',attempted_at_utc='2026-11-06T11:30:00+00:00')
        r=reconcile(self.snapshot,self.receipt,self.now)
        self.assertFalse(r['latest_attempt_produced_snapshot'])
        self.assertEqual(r['snapshot_status'],'CURRENT_CONTEXT_ONLY')
    def test_stale_snapshot(self):
        self.snapshot['retrieved_at_utc']='2026-10-20T11:00:00+00:00'
        self.assertEqual(reconcile(self.snapshot,self.receipt,self.now)['snapshot_status'],'STALE_CONTEXT_ONLY')
    def test_mismatched_success_receipt(self):
        self.receipt['attempted_at_utc']='2026-11-06T11:30:00+00:00'
        self.assertFalse(reconcile(self.snapshot,self.receipt,self.now)['latest_attempt_produced_snapshot'])
    def test_future_snapshot_rejected(self):
        self.snapshot['retrieved_at_utc']='2026-11-07T11:00:00+00:00'
        self.assertEqual(reconcile(self.snapshot,self.receipt,self.now)['snapshot_status'],'UNVERIFIED')
    def test_missing_receipt(self):
        self.assertFalse(reconcile(self.snapshot,{},self.now)['latest_attempt_success'])
