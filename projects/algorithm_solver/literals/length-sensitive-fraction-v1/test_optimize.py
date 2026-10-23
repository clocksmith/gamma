"""Synthetic optimizer/diagnostic/deadline checks; no corpus inputs."""
import subprocess
import sys
import time
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import implicit
import optimize
import supervise

class OptimizeTests(unittest.TestCase):
    def config(self):return {'iterations':12,'seconds':5,'denominator':1000,'halve_after':3,'primal_every':3}
    def fixture(self):
        texts={'a':'ababababac','b':'babababcab','c':'cabacacaba'};index=implicit.Index(texts,set(texts.values()))
        oldq={p:[0]*len(t) for p,t in texts.items()};old=index.base.certificate(oldq,4,1000)
        return index,oldq,old

    def test_zero_parent_diagnostics_deduplicate_and_bound_retained(self):
        index,oldq,old=self.fixture();trace=[];checkpoints=[]
        info,q,seed,best,generated=optimize.optimize(index,['a','b','c','z'],oldq,old,4,self.config(),trace.append,lambda q,c:checkpoints.append(c))
        self.assertEqual(seed,['a','b','c']);self.assertEqual(len(info['bin_release']),22)
        self.assertTrue(all(r['status']=='duplicate_baseline' for r in info['bin_release']))
        self.assertGreaterEqual(info['certificate']['numerator'],old['numerator'])
        self.assertEqual(info['certificate']['numerator'],implicit.verify(index,q,4,1000))
        self.assertEqual(info['best_objective'],optimize.dual.objective(index.texts,best))
        self.assertEqual(len(trace),23+info['iterations']);self.assertTrue(checkpoints)
        self.assertEqual(info['certificate']['numerator'],max(r['best_numerator'] for r in trace))

    def test_exact_release_dedup_and_initial_source_preservation(self):
        initial={'a':[[1,2,3]+[0]*8,[0,1,4]+[0]*8]}
        plan=list(optimize.release_sweep(initial));self.assertEqual(len(plan),22)
        self.assertEqual(plan[0][0]['status'],'evaluate');self.assertEqual(plan[1][0]['status'],'duplicate_diagnostic')
        self.assertEqual(plan[1][0]['duplicate_of'],[0,'half_floor'])
        self.assertEqual(plan[2][0]['status'],'evaluate');self.assertEqual(plan[3][0]['status'],'evaluate')
        self.assertTrue(all(row[0]['status']=='duplicate_baseline' for row in plan[6:]))
        for record,q in plan:
            if q is None:continue
            b=record['bin']
            for i in range(2):
                for other in range(11):
                    if other!=b:self.assertEqual(q['a'][i][other],initial['a'][i][other])
        self.assertEqual(initial['a'][0][:3],[1,2,3])

    def test_parent_corruption_rejected_and_zero_budget_keeps_verified_baseline(self):
        index,q,cert=self.fixture();bad=dict(cert,numerator=cert['numerator']+1)
        with self.assertRaises(AssertionError):optimize.optimize(index,['a','b','c'],q,bad,4,self.config(),lambda _:None)
        info,bestq,*_=optimize.optimize(index,['a','b','c'],q,cert,4,{**self.config(),'seconds':0},lambda _:None)
        self.assertEqual(info['stop'],'time_limit');self.assertEqual(info['iterations'],0)
        self.assertEqual(info['certificate']['numerator'],cert['numerator']);self.assertEqual(bestq,implicit.lift_start_multipliers(q))

    def test_exact_equality_is_only_optimum_stop(self):
        index=implicit.Index({'a':'aaaa'},{'aaaa'});q={'a':[0]*4};cert=index.base.certificate(q,3,1000)
        info,*_=optimize.optimize(index,['a','aa'],q,cert,3,self.config(),lambda _:None)
        self.assertEqual(info['stop'],'exact_primal_optimum_certificate')
        self.assertEqual(info['certificate']['integer_lower_bound'],info['best_objective'])

    def test_process_deadline_and_worker_error_reject_whole_job(self):
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],start_new_session=True)
        try:
            with self.assertRaises(TimeoutError):supervise.wait_workers([p],time.monotonic()+.02)
        finally:supervise.stop_workers([p])
        self.assertEqual(p.returncode,-9)
        p=subprocess.Popen([sys.executable,'-c','raise SystemExit(7)'],start_new_session=True)
        try:
            with self.assertRaises(RuntimeError):supervise.wait_workers([p],time.monotonic()+2)
        finally:supervise.stop_workers([p])
        self.assertEqual(p.returncode,7)

if __name__=='__main__':unittest.main()
