import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from gate_coverage import evaluate

class GateCoverageTests(unittest.TestCase):
    def setUp(self): self.matrix=Path(__file__).with_name('source_matrix.csv')
    def test_full_audit_is_preserved(self):
        d=evaluate(self.matrix)
        self.assertEqual([g['field_count'] for g in d['gates']],[22,17,26,19,23])
        self.assertEqual(d['journal']['field_count'],18)
        self.assertFalse(d['all_gates_complete'])
        self.assertTrue(all(g['gate_result']=='NOT_ASSESSED' for g in d['gates']))
    def test_partial_treasury_does_not_pass_gate(self):
        with TemporaryDirectory() as t:
            p=Path(t)/'treasury.json'
            p.write_text(json.dumps({'observation_date':'2026-11-05','retrieved_at_utc':'2026-11-05T23:00:00Z','yields_percent':{'10-year':4.1}}))
            d=evaluate(self.matrix,p)
            self.assertEqual(d['gates'][0]['verified_daily_observations'],1)
            self.assertEqual(d['gates'][0]['gate_result'],'NOT_ASSESSED')
    def test_missing_feed_is_not_verified(self):
        d=evaluate(self.matrix,'/missing/treasury.json')
        self.assertEqual(d['gates'][0]['verified_daily_observations'],0)
if __name__=='__main__':unittest.main()
