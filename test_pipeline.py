import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timezone
from pipeline import run
class PipelineTests(unittest.TestCase):
    def test_missing_inputs_do_not_fabricate_assessment(self):
        with tempfile.TemporaryDirectory() as d:
            r=run(d,datetime(2026,11,6,12,tzinfo=timezone.utc))
            self.assertEqual(r['weekly_regime_status'],'NOT_ASSESSED')
            self.assertFalse(r['automated_macro_score_available'])
            self.assertTrue((Path(d)/'pipeline_status.json').exists())
    def test_treasury_observation_flows_into_rates(self):
        with tempfile.TemporaryDirectory() as d:
            t={'observation_date':'2026-11-05','retrieved_at_utc':'2026-11-06T01:00:00Z',
               'source_url':'https://home.treasury.gov/resource-center',
               'yields_percent':{'2-year':4.1,'10-year':4.4}}
            (Path(d)/'treasury.json').write_text(json.dumps(t))
            run(d,datetime(2026,11,6,12,tzinfo=timezone.utc))
            e=json.loads((Path(d)/'macro_factor_evidence.json').read_text())
            self.assertEqual(len(e['factors']['Rates']['observations']),0)
            self.assertEqual(len(e['factors']['Rates']['rejected']),2)
            self.assertEqual(e['status'],'EVIDENCE_INCOMPLETE')
    def test_other_factor_evidence_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            item={'indicator':'GDP','value':2.1,'observation_date':'2026-11-01',
                  'published_date':'2026-11-04','source':'Official'}
            (Path(d)/'macro_observations.json').write_text(json.dumps({'Growth':[item]}))
            run(d,datetime(2026,11,6,12,tzinfo=timezone.utc))
            e=json.loads((Path(d)/'macro_factor_evidence.json').read_text())
            self.assertEqual(e['factors']['Growth']['observations'][0]['indicator'],'GDP')
if __name__=='__main__':unittest.main()
