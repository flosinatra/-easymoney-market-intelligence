import io
import tempfile
import unittest
from pathlib import Path
from evidence_store import store_evidence, list_evidence
from collect_treasury import collect

CSV = b'Date,2 Yr,10 Yr\n11/03/2026,3.75,4.12\n'
class FakeResponse(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *args): self.close()

class ArchiveTests(unittest.TestCase):
    def test_archive_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'data.db'
            p={'source':'US Treasury','dataset':'Daily Treasury Par Yield Curve Rates',
               'retrieved_at_utc':'2026-11-05T14:00:00+00:00','latest_observation_date':'2026-11-03'}
            self.assertTrue(store_evidence(db,p)['stored'])
            self.assertFalse(store_evidence(db,p)['stored'])
            self.assertEqual(len(list_evidence(db)),1)
    def test_missing_timestamp_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                store_evidence(Path(tmp)/'data.db',{'source':'US Treasury','dataset':'X'})
    def test_url_rejects_untrusted_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                collect('https://fake-treasury.gov/data.csv',Path(tmp)/'db')
    def test_controlled_fetch_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=collect('https://home.treasury.gov/example.csv',Path(tmp)/'db',
                           opener=lambda req,timeout: FakeResponse(CSV))
            self.assertEqual(result['latest_observation_date'],'2026-11-03')
            self.assertFalse(result['research_ready'])
            self.assertEqual(len(list_evidence(Path(tmp)/'db')),1)
if __name__=='__main__': unittest.main()
