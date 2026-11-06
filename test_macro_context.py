import unittest
from datetime import datetime,timezone,date
from collect_macro_context import parse_series,collect,SERIES,read_series,parse_series_page
class MacroContextTests(unittest.TestCase):
    def test_latest_nonfuture(self):
        data=b'DATE,INDPRO\n2026-10-01,101.5\n2026-11-01,102.5\n2026-12-01,103.5\n'
        self.assertEqual(parse_series(data,'INDPRO',date(2026,11,5)),(date(2026,11,1),102.5))
    def test_observation_date_header(self):
        raw = b'observation_date,INDPRO\n2026-10-01,101.5\n'
        self.assertEqual(parse_series(raw, 'INDPRO', date(2026, 11, 5)),
                         (date(2026, 10, 1), 101.5))
    def test_missing_values_skipped(self):
        self.assertEqual(parse_series(b'DATE,INDPRO\n2026-10-01,3\n2026-11-01,.\n','INDPRO',date(2026,11,5))[1],3)
    def test_wrong_schema_rejected(self):
        with self.assertRaises(ValueError):parse_series(b'date,value\n2026-01-01,4','INDPRO',date(2026,11,5))
    def test_collection_is_never_verified_publication(self):
        class Resp:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,n):return b'DATE,'+self.id.encode()+b'\n2026-10-01,4.5\n'
        def opener(req,timeout):
            r=Resp();r.id=req.full_url.split('=')[-1];return r
        r=collect(datetime(2026,11,5,tzinfo=timezone.utc),opener)
        self.assertEqual(len(r['series']),4)
        self.assertFalse(r['release_dates_verified'])
        self.assertTrue(all(v['publication_date'] is None for v in r['series'].values()))
    def test_archive_fallback_requires_requested_vintage(self):
        import io
        now = datetime(2026, 11, 6, 3, tzinfo=timezone.utc)
        def opener(req, timeout):
            if req.full_url.startswith('https://alfred.'):
                return io.BytesIO(b'observation_date,INDPRO_20261105\n2026-09-01,103.95\n')
            raise OSError('timed out')
        day, value, url = read_series('INDPRO', now, opener)
        self.assertEqual((day, value), (date(2026, 9, 1), 103.95))
        self.assertTrue(url.startswith('https://alfred.stlouisfed.org/'))
        self.assertIn('vintage_date=2026-11-05', url)

    def test_series_page_requires_matching_series_and_observation(self):
        url = 'https://fred.stlouisfed.org/series/WALCL'
        html = (f'<link rel="canonical" href="{url}">'
                '<meta name="dcterms:PeriodOfTime" content="start:2002-12-18; end:2026-11-04;">'
                '<p>Nov 4, 2026: <span class="series-meta-observation-value">6,748,145</span></p>')
        today = date(2026, 11, 5)
        self.assertEqual(parse_series_page(html.encode(), url, today), (date(2026, 11, 4), 6748145))
        for invalid in (html.replace('WALCL', 'INDPRO'), html.replace('Nov 4', 'Nov 3')):
            with self.assertRaises(ValueError):
                parse_series_page(invalid.encode(), url, today)

    def test_failed_source_is_not_faked(self):
        def opener(*args,**kwargs):raise OSError('offline')
        r=collect(datetime(2026,11,5,tzinfo=timezone.utc),opener)
        self.assertEqual(r['status'],'CONTEXT_UNAVAILABLE')
        self.assertEqual(len(r['errors']),4)
if __name__=='__main__':unittest.main()
