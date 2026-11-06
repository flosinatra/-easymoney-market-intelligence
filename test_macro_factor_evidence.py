import unittest
from datetime import date
from macro_factor_evidence import assemble,FACTORS
class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.today=date(2026,11,5)
        self.item={"indicator":"Example observation","value":2.5,"unit":"%",
                   "observation_date":"2026-11-02","published_date":"2026-11-04",
                   "source":"Example official agency"}
    def test_empty_does_not_score(self):
        r=assemble({},self.today)
        self.assertIsNone(r["regime_score"])
        self.assertEqual(r["status"],"EVIDENCE_INCOMPLETE")
    def test_all_factors_still_no_score(self):
        r=assemble({f:[self.item] for f in FACTORS},self.today)
        self.assertEqual(r["status"],"EVIDENCE_PRESENT_AWAITING_WORKBOOK_SCORING")
        self.assertTrue(all(r["factors"][f]["score_1_to_5"] is None for f in FACTORS))
    def test_future_publication_rejected(self):
        item={**self.item,"published_date":"2026-11-06"}
        r=assemble({"Growth":[item]},self.today)
        self.assertFalse(r["factors"]["Growth"]["observations"])
    def test_stale_rejected(self):
        item={**self.item,"published_date":"2026-09-01","observation_date":"2026-08-01"}
        r=assemble({"Growth":[item]},self.today)
        self.assertEqual(r["factors"]["Growth"]["rejected"],["stale"])
    def test_expectations_preserved(self):
        item={**self.item,"expectation":2.1,"previous":2.3}
        r=assemble({"Inflation":[item]},self.today)
        self.assertEqual(r["factors"]["Inflation"]["observations"][0]["expectation"],2.1)
    def test_missing_source_rejected(self):
        item={**self.item,"source":""}
        r=assemble({"Rates":[item]},self.today)
        self.assertFalse(r["factors"]["Rates"]["observations"])
if __name__=="__main__": unittest.main()
