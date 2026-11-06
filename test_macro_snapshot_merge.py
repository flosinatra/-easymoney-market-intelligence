import unittest
from datetime import datetime, timezone
from macro_snapshot_merge import merge
from macro_context_integrity import validate

class PartialCollectionTests(unittest.TestCase):
    def setUp(self):
        self.old={'retrieved_at_utc':'2026-11-04T12:00:00+00:00','series':{'Growth':{
            'series_id':'INDPRO','retrieved_at_utc':'2026-11-04T12:00:00+00:00',
            'value':100.0,'observation_date':'2026-10-01','publication_date':None,
            'publication_date_verified':False,'status':'CONTEXT_ONLY_RELEASE_DATE_UNVERIFIED'}}}
        self.new={'retrieved_at_utc':'2026-11-06T12:00:00+00:00','series':{'Inflation':{
            'series_id':'CPIAUCSL','retrieved_at_utc':'2026-11-06T12:00:00+00:00',
            'value':300.0,'observation_date':'2026-10-01','publication_date':None,
            'publication_date_verified':False,'status':'CONTEXT_ONLY_RELEASE_DATE_UNVERIFIED'}}}
    def test_partial_retains_old_with_old_timestamp(self):
        r=merge(self.old,self.new)
        self.assertEqual(r['retained_series_count'],1)
        self.assertEqual(r['new_series_count'],1)
        self.assertEqual(r['series']['Growth']['retrieved_at_utc'],self.old['retrieved_at_utc'])
    def test_old_record_not_counted_fresh(self):
        r=validate(merge(self.old,self.new),datetime(2026,11,6,13,tzinfo=timezone.utc))
        self.assertEqual(r['factors']['Growth'],'STALE_OR_INVALID_SERIES')
        self.assertEqual(r['available_factors'],1)
    def test_failed_attempt_keeps_snapshot(self):
        self.assertEqual(merge(self.old,{'series':{},'retrieved_at_utc':'2026-11-06T12:00:00+00:00'}),self.old)
    def test_no_future_or_missing_attempt_time(self):
        self.assertEqual(merge(self.old,{'series':self.new['series']}),self.old)
    def test_new_row_overwrites_same_factor(self):
        x=dict(self.new['series']['Inflation'],series_id='INDPRO')
        a={'retrieved_at_utc':self.new['retrieved_at_utc'],'series':{'Growth':x}}
        self.assertEqual(merge(self.old,a)['series']['Growth']['value'],300)
if __name__=='__main__': unittest.main()
