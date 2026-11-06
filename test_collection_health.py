import tempfile
import unittest
import json
from pathlib import Path
from collect_macro_context import run
from collection_health import receipt

class CollectionHealthTests(unittest.TestCase):
    def test_complete(self):
        self.assertEqual(receipt({'series':{'a':1,'b':2},'errors':{}},2)['collection_status'],'COMPLETE')
    def test_partial(self):
        self.assertEqual(receipt({'series':{'a':1},'errors':{'b':'network'}},2)['collection_status'],'PARTIAL')
    def test_failed(self):
        self.assertEqual(receipt({'series':{},'errors':{'a':'DNS'}},2)['collection_status'],'FAILED')
    def test_failure_preserves_prior_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'macro.json';h=Path(d)/'health.json'
            p.write_text('{"old":true}')
            run(str(p),str(h),collector=lambda:{'series':{},'errors':{'Growth':'DNS'},'retrieved_at_utc':'2026-11-06T00:00:00Z'})
            self.assertEqual(json.loads(p.read_text()),{'old':True})
            self.assertEqual(json.loads(h.read_text())['collection_status'],'FAILED')
    def test_success_updates_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'macro.json';h=Path(d)/'health.json'
            run(str(p),str(h),collector=lambda:{'retrieved_at_utc':'2026-11-06T00:00:00Z','series':{'Growth':{'series_id':'INDPRO','retrieved_at_utc':'2026-11-06T00:00:00Z','value':2}},'errors':{}})
            self.assertEqual(json.loads(p.read_text())['series']['Growth']['value'],2)
            self.assertEqual(json.loads(h.read_text())['collection_status'],'PARTIAL')
