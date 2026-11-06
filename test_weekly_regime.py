import unittest
from weekly_regime import assess, FACTORS

class WeeklyRegimeTests(unittest.TestCase):
    def valid(self):
        d={"Week of Date":"2026-11-02","Regime":"Defensive","Lead Driver":"Growth",
           "Failure #1":"Growth rebounds","Failure #2":"Yields rise"}
        for f in FACTORS:
            d[f+" 1-5"]=3
            d[f+" Evidence"]={"summary":"Documented evidence","source":"Official release","published_date":"2026-11-02"}
        return d
    def test_mean_and_metadata(self):
        d=self.valid();d["Growth 1-5"]=5
        r=assess(d)
        self.assertEqual(r["regime_score"],3.4)
        self.assertEqual(r["gate_result"],"DOCUMENTED_RESEARCH_ONLY")
    def test_missing_evidence_blocks_score(self):
        d=self.valid();d.pop("Credit Evidence")
        r=assess(d)
        self.assertIsNone(r["regime_score"])
        self.assertIn("Credit Evidence (summary/source/published_date)",r["missing"])
    def test_out_of_range_blocks_score(self):
        d=self.valid();d["Growth 1-5"]=6
        self.assertIsNone(assess(d)["regime_score"])
    def test_boolean_not_a_score(self):
        d=self.valid();d["Growth 1-5"]=True
        self.assertIsNone(assess(d)["regime_score"])
    def test_invalid_week(self):
        d=self.valid();d["Week of Date"]="2026-11-03"
        self.assertIsNone(assess(d)["regime_score"])
    def test_no_invented_regime(self):
        d=self.valid();d.pop("Regime")
        r=assess(d)
        self.assertIsNone(r["regime"])
        self.assertEqual(r["gate_result"],"SCORED_AWAITING_REGIME_INTERPRETATION")
if __name__=="__main__":unittest.main()
