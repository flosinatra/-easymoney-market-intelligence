import unittest
from datetime import datetime, timezone
from freshness import evaluate

class FreshnessTests(unittest.TestCase):
    def test_missing_does_not_look_live(self):
        result = evaluate({'retrieved_at_utc':'2026-11-05T12:00:00+00:00', 'series':{}}, datetime(2026,11,5,12,1,tzinfo=timezone.utc))
        self.assertEqual(result['retrieval_age_seconds'], 60)
        self.assertFalse(result['research_ready'])
        self.assertFalse(result['series']['rates_ten_year_yield']['usable_for_intraday_quote'])
    def test_recent_observation_not_assumed_live(self):
        snap={'retrieved_at_utc':'2026-11-05T12:00:00+00:00', 'series':{'rates_ten_year_yield':{'status':'ok','observations':[{'observation_date':'2026-11-05','value':4.0}]}}}
        result=evaluate(snap, datetime(2026,11,5,12,1,tzinfo=timezone.utc))
        self.assertEqual(result['series']['rates_ten_year_yield']['observation_age_days'], 0)
        self.assertFalse(result['series']['rates_ten_year_yield']['exact_publication_time_verified'])
        self.assertFalse(result['series']['rates_ten_year_yield']['usable_for_intraday_quote'])

if __name__=='__main__': unittest.main()
