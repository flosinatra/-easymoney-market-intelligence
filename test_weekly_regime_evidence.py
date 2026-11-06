import unittest
from datetime import datetime,timezone
from weekly_regime_evidence import build
class RatesEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,6,12,tzinfo=timezone.utc)
        self.data={"observation_date":"2026-11-05","retrieved_at_utc":"2026-11-06T01:00:00Z",
                   "source_url":"https://home.treasury.gov/",
                   "yields_percent":{"2-year":4.2,"10-year":4.5}}
    def test_daily_rates_not_scored(self):
        x=build(self.data,self.now)
        self.assertEqual(x["status"],"DAILY_NOMINAL_RATE_CONTEXT_ONLY")
        self.assertIsNone(x["score_1_to_5"])
        self.assertEqual(x["observations"]["10-year_yield_percent"],4.5)
    def test_stale_not_accepted(self):
        self.data["observation_date"]="2026-10-20"
        self.assertEqual(build(self.data,self.now)["status"],"STALE")
    def test_future_retrieval_rejected(self):
        self.data["retrieved_at_utc"]="2026-11-07T01:00:00Z"
        self.assertEqual(build(self.data,self.now)["status"],"UNVERIFIED")
    def test_no_fake_rates(self):
        self.data["yields_percent"]={"10-year":None}
        self.assertEqual(build(self.data,self.now)["status"],"UNVERIFIED")
if __name__=="__main__": unittest.main()
