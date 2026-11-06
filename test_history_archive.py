import json
import tempfile
import unittest
from pathlib import Path
from history_archive import archive_snapshot

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.record = {'observation_date':'2026-11-04', 'source_file_sha256':'a'*64,
                       'retrieved_at_utc':'2026-11-05T14:00:00+00:00'}
    def test_persists_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            path=archive_snapshot(self.record,d)
            self.assertEqual(json.loads(Path(path).read_text()),self.record)
    def test_deduplicates_identical_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            a=archive_snapshot(self.record,d)
            self.assertEqual(a,archive_snapshot(self.record,d))
            self.assertEqual(len(list(Path(d).rglob('*.json'))),1)
    def test_later_retrieval_preserves_first_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            first = archive_snapshot(self.record, d)
            later = {**self.record, 'retrieved_at_utc':'2026-11-05T19:00:00+00:00'}
            self.assertEqual(archive_snapshot(later, d), first)
            self.assertEqual(json.loads(Path(first).read_text()), self.record)
            with self.assertRaises(ValueError):
                archive_snapshot({**later, 'observation_count': 12}, d)
    def test_rejects_collision(self):
        with tempfile.TemporaryDirectory() as d:
            archive_snapshot(self.record,d)
            with self.assertRaises(ValueError):archive_snapshot({**self.record,'retrieved_at_utc':'different'},d)
    def test_rejects_bad_hash(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):archive_snapshot({**self.record,'source_file_sha256':'no'},d)
