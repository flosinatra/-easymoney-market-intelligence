import tempfile
import unittest
from pathlib import Path
from hosted_run import execute

class HostedRunTests(unittest.TestCase):
    def test_one_failed_provider_does_not_block_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            def fail(): raise OSError('offline')
            result=execute(d,treasury_collector=fail,macro_collector=lambda:None)
            self.assertEqual(result['treasury'],'COLLECTION_FAILED')
            self.assertEqual(result['pipeline'],'REPORTS_BUILT_NOT_GATE_PASSED')
            self.assertTrue((Path(d)/'pipeline_status.json').exists())
    def test_both_failed_still_publish_failure_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            def fail(): raise OSError('offline')
            result=execute(d,treasury_collector=fail,macro_collector=fail)
            self.assertEqual(result['macro'],'COLLECTION_FAILED')
            self.assertTrue((Path(d)/'hosted_collection_receipt.json').exists())
    def test_receipt_does_not_claim_successful_feed_from_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            result=execute(d,treasury_collector=lambda:None,macro_collector=lambda:None)
            self.assertEqual(result['pipeline'],'REPORTS_BUILT_NOT_GATE_PASSED')
            self.assertEqual(result['macro'],'COLLECTION_FAILED_OR_UNVERIFIED')

    def test_returned_empty_result_not_claimed_as_success(self):
        with tempfile.TemporaryDirectory() as d:
            r=execute(d,treasury_collector=lambda:None,macro_collector=lambda:None)
            self.assertEqual(r['treasury'],'RESULT_UNVERIFIED')
            self.assertEqual(r['macro_collected_series'],0)
    def test_partial_macro_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            r=execute(d,treasury_collector=lambda:None,macro_collector=lambda:{'series':{'Growth':{}},'errors':{'Credit':'offline'}})
            self.assertEqual(r['macro'],'PARTIAL')
            self.assertEqual(r['macro_failed_factors'],['Credit'])
