import unittest
from datetime import datetime,timezone
from treasury_macro_bridge import merge
class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,6,12,tzinfo=timezone.utc)
        self.t={"observation_date":"2026-11-05","retrieved_at_utc":"2026-11-06T01:00:00Z",
                "source_url":"https://home.treasury.gov/resource-center",
                "yields_percent":{"2-year":4.1,"10-year":4.4}}
    def test_valid_rates_flow(self):
        x=merge(self.t,{},self.now)
        self.assertEqual(len(x["Rates"]),2)
        self.assertFalse(x["Rates"][0]["publication_date_verified"])
        self.assertIsNone(x["Rates"][0]["published_date"])
    def test_preserves_other_factors(self):
        x=merge(self.t,{"Growth":[{"indicator":"GDP"}]},self.now)
        self.assertEqual(x["Growth"][0]["indicator"],"GDP")
    def test_no_duplicate_treasury_rows(self):
        a=merge(self.t,{},self.now)
        b=merge(self.t,a,self.now)
        self.assertEqual(len(b["Rates"]),2)
    def test_stale_no_injection(self):
        self.t["observation_date"]="2026-10-01"
        self.assertNotIn("Rates",merge(self.t,{},self.now))
    def test_untrusted_url_rejected(self):
        self.t["source_url"]="https://example.com/"
        self.assertNotIn("Rates",merge(self.t,{},self.now))
    def test_future_retrieval_rejected(self):
        self.t["retrieved_at_utc"]="2026-11-07T01:00:00Z"
        self.assertNotIn("Rates",merge(self.t,{},self.now))
