import unittest
from datetime import date,datetime,timezone
from treasury_macro_bridge import merge
from macro_factor_evidence import assemble
from pathlib import Path
class IntegrityTests(unittest.TestCase):
    def test_unverified_publication_does_not_count_as_verified_factor_evidence(self):
        now=datetime(2026,11,6,12,tzinfo=timezone.utc)
        treasury={"observation_date":"2026-11-05","retrieved_at_utc":"2026-11-06T01:00:00Z","source_url":"https://home.treasury.gov/curve","yields_percent":{"10-year":4.3}}
        bridged=merge(treasury,{},now)
        report=assemble(bridged,now.date())
        self.assertEqual(report["factors"]["Rates"]["status"],"MISSING_VERIFIED_EVIDENCE")
        self.assertIn("invalid_or_future_dated",report["factors"]["Rates"]["rejected"])
    def test_explicit_unverified_publication_rejected_even_if_date_present(self):
        record={"indicator":"Nominal yield","value":4.3,"observation_date":"2026-11-05","published_date":"2026-11-06","source":"US Treasury","publication_date_verified":False}
        report=assemble({"Rates":[record]},date(2026,11,6))
        self.assertEqual(report["factors"]["Rates"]["rejected"],["publication_date_unverified"])
    def test_workflow_does_not_continue_after_failed_collector(self):
        import yaml
        workflow=yaml.safe_load(Path('.github/workflows/treasury.yml').read_text())
        steps=workflow['jobs']['collect']['steps']
        for step in steps:
            if step.get('run','').startswith('python '):
                self.assertNotEqual(step.get('if'),'always()')
if __name__=='__main__':unittest.main()
