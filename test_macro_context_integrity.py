import unittest
from datetime import datetime, timezone
from macro_context_integrity import validate
from collect_macro_context import SERIES

class MacroIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,5,18,tzinfo=timezone.utc)
        self.snapshot={'retrieved_at_utc':'2026-11-05T17:00:00+00:00','series':{}}
        for factor,(sid,_,_) in SERIES.items():
            self.snapshot['series'][factor]={'series_id':sid,'value':4.2,'observation_date':'2026-10-01',
                'publication_date':None,'publication_date_verified':False,
                'status':'CONTEXT_ONLY_RELEASE_DATE_UNVERIFIED'}
    def test_four_series_not_scored(self):
        r=validate(self.snapshot,self.now)
        self.assertEqual(r['available_factors'],4)
        self.assertEqual(r['status'],'CONTEXT_AVAILABLE_UNSCORED')
        self.assertNotIn('score',r)
    def test_missing_series(self):
        del self.snapshot['series']['Credit']
        r=validate(self.snapshot,self.now)
        self.assertEqual(r['status'],'CONTEXT_PARTIAL_UNSCORED')
        self.assertIn('Credit',r['missing_factors'])
    def test_stale_retrieval(self):
        self.snapshot['retrieved_at_utc']='2026-10-01T17:00:00+00:00'
        self.assertEqual(validate(self.snapshot,self.now)['status'],'STALE_OR_INVALID_RETRIEVAL')
    def test_future_retrieval(self):
        self.snapshot['retrieved_at_utc']='2026-11-06T17:00:00+00:00'
        self.assertEqual(validate(self.snapshot,self.now)['status'],'STALE_OR_INVALID_RETRIEVAL')
    def test_unverified_publication_required(self):
        self.snapshot['series']['Growth']['publication_date_verified']=True
        self.assertEqual(validate(self.snapshot,self.now)['available_factors'],3)
    def test_nan_rejected(self):
        self.snapshot['series']['Growth']['value']=float('nan')
        self.assertEqual(validate(self.snapshot,self.now)['available_factors'],3)
