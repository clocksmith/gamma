import hashlib
import json
import unittest
from unittest.mock import patch
import search


class SearchTests(unittest.TestCase):
    def fixture(self):
        seed=['a','b','c','d','x']
        g=search.CheckedGraph({'p':'abx','q':'cdx'},['a','ab','b','c','cd','d','x','xy'],seed,capacity=6,banned=['abx','cdx'])
        limits={'seconds':600,'evaluations':1000,'epochs':3,'shortlist':4,'expected_free_slots':1}
        return g,seed,limits

    def execute(self,limit=None,clock=None,emitter=None):
        g,seed,limits=self.fixture();events=[];retained=[]
        if limit is not None:limits['evaluations']=limit
        def emit(row):
            events.append(row)
            if emitter:emitter(row,g)
        def retain(state,index):retained.append(state);return {'index':index,'dictionary_sha256':str(index)}
        kw={} if clock is None else {'clock':clock}
        final,result=search.execute(g,seed,limits,emit,retain,**kw)
        return g,final,result,events,retained

    def test_complete_search_counters_caps_and_charged_rescores(self):
        g,final,r,events,retained=self.execute()
        self.assertLess(final['objective'],g.seed['objective']);self.assertTrue(final['eligible'])
        self.assertEqual(r['attempted'],sum(x['attempted'] for x in r['counters'].values()))
        self.assertEqual(r['completed'],r['attempted'])
        self.assertGreater(r['counters']['remove']['coverage_failures'],0)
        self.assertTrue(all(b['objective']<a['objective'] for a,b in zip(retained,retained[1:])))
        for a in r['accepted']:
            row=next(e for e in events if e['event']=='evaluation' and e['evaluation']==a['rescore_evaluation'])
            self.assertTrue(row['complete']);self.assertEqual(row['kind'],'rescore');self.assertEqual(row['score'],a['after'])
        self.assertTrue(all(not x['cap_failures'] for x in retained))
        self.assertTrue(all(len(e['opportunity_sha256'])==64 for e in events if e['event']=='sweep_start'))

    def test_evaluation_partial_retains_only_completed_full_rescore(self):
        g,final,r,events,retained=self.execute(limit=2)
        self.assertEqual(r['stop'],'evaluation_limit');self.assertEqual(len(retained),2)
        self.assertTrue(r['accepted'][0]['partial_sweep']);self.assertEqual(r['counters']['rescore']['completed'],1)
        g,final,r,events,retained=self.execute(limit=1)
        self.assertEqual(final['active'],g.seed['active']);self.assertEqual(len(retained),1)

    def test_deadline_during_full_rescore_never_retains_trial(self):
        now=[0];armed=[False]
        def emit(row,g):
            if row['event']=='evaluation' and row['kind']=='add' and row['complete'] and not armed[0]:
                original=g.path;armed[0]=True
                def path(pid,active):
                    value=original(pid,active);now[0]=601;return value
                g.path=path
        g,final,r,events,retained=self.execute(clock=lambda:now[0],emitter=emit)
        self.assertEqual(r['stop'],'time_limit');self.assertEqual(final['active'],g.seed['active'])
        self.assertEqual(r['counters']['rescore']['attempted'],1);self.assertEqual(r['counters']['rescore']['completed'],0)
        self.assertEqual(r['attempted'],2);self.assertEqual(r['completed'],1)

    def test_cap_failure_and_coverage_failure_are_counted_attempts(self):
        seed=['a','ab','b','c','x'];pool=['a','ab','b','c','cc','x']
        g=search.CheckedGraph({'x':'abx','y':'ccccx'},pool,seed,capacity=5,banned=['abx','ccccx'])
        events=[];retained=[];limits={'seconds':600,'evaluations':100,'epochs':1,'shortlist':4,'expected_free_slots':0}
        final,r=search.execute(g,seed,limits,events.append,lambda s,i:retained.append(s) or {'index':i})
        failures=[e for e in events if e['event']=='evaluation' and e['outcome']=='cap_failure']
        self.assertTrue(failures);self.assertTrue(any(e['outcome']=='coverage_failure' for e in events if e['event']=='evaluation'))
        for e in failures:
            self.assertTrue(e['complete']);w=e['cap_failure_witness'];self.assertGreater(w['N'],w['cap']);self.assertEqual(w['cap'],g.caps[w['pid']])
        self.assertEqual(r['attempted'],r['completed']);self.assertTrue(all(s['eligible'] for s in retained))
        swaps=[e for e in events if e['event']=='evaluation' and e['kind']=='swap']
        self.assertEqual(len(swaps),len(seed));self.assertTrue(final['eligible'])

    def test_deadline_after_early_failure_still_charges_attempt(self):
        for failure_kind in ('coverage','cap'):
            with self.subTest(failure_kind=failure_kind):
                seed=['a','ab','b','c','x'];pool=['a','ab','b','c','cc','x'];now=[0]
                g=search.CheckedGraph({'x':'abx','y':'ccccx'},pool,seed,capacity=5,banned=['abx','ccccx'])
                original=g.evaluate
                def evaluate(*args,**kwargs):
                    result,receipt=original(*args,**kwargs)
                    if (failure_kind=='coverage' and result is None) or (failure_kind=='cap' and result is not None and result['cap_failures']):now[0]=601
                    return result,receipt
                g.evaluate=evaluate;events=[]
                final,r=search.execute(g,seed,{'seconds':600,'evaluations':100,'epochs':1,'shortlist':4,'expected_free_slots':0},events.append,lambda s,i:{'index':i},clock=lambda:now[0])
                self.assertEqual(r['stop'],'time_limit');self.assertEqual(r['attempted'],r['completed']+1)
                last=[e for e in events if e['event']=='evaluation'][-1]
                self.assertFalse(last['complete']);self.assertEqual(last['outcome'],'interrupted');self.assertTrue(final['eligible'])


if __name__=='__main__':unittest.main()
