import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from evidence_store import store_evidence
from health_report import evaluate_archive

NOW = datetime(2026, 11, 5, 15, 0, tzinfo=timezone.utc)

class HealthTests(unittest.TestCase):
    def test_missing_archive_never_claims_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            result = evaluate_archive(Path(temp)/'missing.db', NOW)
            self.assertFalse(result['archive_exists'])
            self.assertFalse(result['research_ready'])
            self.assertEqual(result['datasets'], [])

    def test_capture_and_observation_ages_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp)/'evidence.db'
            store_evidence(db, {'source':'US Treasury','dataset':'Daily Treasury Par Yield Curve Rates',
                'retrieved_at_utc':'2026-11-05T14:00:00+00:00',
                'latest_observation_date':'2026-11-03'})
            result = evaluate_archive(db, NOW)
            self.assertEqual(result['datasets'][0]['retrieval_age_seconds'], 3600)
            self.assertEqual(result['datasets'][0]['observation_age_days'], 2)
            self.assertFalse(result['live_intraday_market_data_verified'])

    def test_future_capture_flagged(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp)/'evidence.db'
            store_evidence(db, {'source':'US Treasury','dataset':'Test',
                'retrieved_at_utc':'2026-11-06T14:00:00+00:00',
                'latest_observation_date':'2026-11-03'})
            result = evaluate_archive(db, NOW)
            self.assertEqual(result['datasets'][0]['status'], 'INVALID_CAPTURE_TIME')

if __name__ == '__main__': unittest.main()
