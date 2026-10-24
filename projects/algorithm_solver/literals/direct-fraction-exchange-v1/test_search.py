import unittest
import search


class SearchTests(unittest.TestCase):
    def run_search(self,evaluations=100,clock=None):
        graph=search.CheckedGraph({'x':'ab'},['a','ab','b','ba'],capacity=3)
        rows=[];saved=[]
        def retain(state,ordinal):
            saved.append((ordinal,state['order'],state['objective']))
            return {'dictionary_sha256':str(ordinal),'entries':len(state['active'])}
        limits={'seconds':600,'evaluations':evaluations,'epochs':3,'shortlist':4,'expected_free_slots':1}
        kwargs={} if clock is None else {'clock':clock}
        final,result=search.execute(graph,['a','b'],limits,rows.append,retain,**kwargs)
        return final,result,rows,saved

    def test_exact_search_and_counter_reconciliation(self):
        final,r,rows,saved=self.run_search()
        self.assertEqual(final['active'],{'ab'})
        self.assertEqual(final['F'],-1)
        self.assertEqual(r['attempted'],sum(v['attempted'] for v in r['counters'].values()))
        self.assertEqual(r['completed'],sum(v['completed'] for v in r['counters'].values()))
        self.assertTrue(all(b[2]<a[2] for a,b in zip(saved,saved[1:])))
        self.assertEqual([row['event_no'] for row in rows],list(range(len(rows))))
        for accept in (row for row in rows if row['event']=='accept'):
            probe=next(row for row in rows if row['event']=='evaluation' and row['evaluation']==accept['rescore_evaluation'])
            self.assertTrue(probe['complete']);self.assertEqual(probe['kind'],'rescore')
            self.assertEqual(probe['objective'],accept['after'])

    def test_partial_sweep_retains_only_already_rechecked_best(self):
        final,r,rows,saved=self.run_search(evaluations=2)
        self.assertEqual(r['stop'],'evaluation_limit');self.assertEqual(r['attempted'],2)
        self.assertEqual(final['active'],{'a','ab','b'})
        self.assertTrue(r['accepted'][-1]['partial_sweep'])
        self.assertEqual(r['counters']['rescore']['completed'],1)
        final,r,rows,saved=self.run_search(evaluations=1)
        self.assertEqual(final['active'],{'a','b'});self.assertEqual(r['accepted'],[])

    def test_interrupt_inside_trial_preserves_attempt_and_seed(self):
        calls=0
        def clock():
            nonlocal calls
            calls+=1
            return 0 if calls<5 else 601
        final,r,rows,saved=self.run_search(clock=clock)
        self.assertEqual(r['stop'],'time_limit')
        self.assertEqual(final['active'],{'a','b'})
        interrupted=[row for row in rows if row['event']=='evaluation' and not row['complete']]
        self.assertEqual(len(interrupted),1)
        self.assertEqual(r['attempted'],1);self.assertEqual(r['completed'],0)


if __name__=='__main__':unittest.main()
