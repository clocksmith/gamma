import copy
from itertools import combinations
from pathlib import Path
import tempfile
import unittest
import optimizer
import prototype
import report


class OptimizerTests(unittest.TestCase):
    def test_round_robin_and_operand_packs_are_matched(self):
        texts,nodes,keys,banned,_=prototype.counterexample()
        pools=optimizer.pool(texts,nodes,banned)
        state=optimizer.evaluate(texts,nodes,keys,optimizer.Budget(1,10))
        offered={arm:list(optimizer.streams(texts,state,pools,banned,arm)) for arm in ('L1','T1','LB','TB')}
        self.assertEqual([p for p in offered['LB'] if p['stream']=='literal_bundle'],
                         [p for p in offered['TB'] if p['stream']=='literal_bundle'])
        self.assertEqual([p for p in offered['L1'] if p['stream']=='literal_single'],
                         [p for p in offered['TB'] if p['stream']=='literal_single'])
        self.assertEqual([p['stream'] for p in offered['TB'][:4]],
                         ['literal_single','literal_bundle','constructor_single','constructor_bundle'])
        self.assertIn('longAlpha',pools['operand_pool'])
        self.assertTrue(all(len(p['additions'])<=5 for p in offered['TB']))
        for arm in ('L1','LB'):self.assertFalse(any('constructor' in p['stream'] for p in offered[arm]))

    def test_removal_combinations_bounded_and_sorted_even_infeasible(self):
        keys=[f'L{i}' for i in range(256)]
        loss={f'L{i}':i for i in range(13)};loss['L0']=float('inf')
        got=optimizer.removal_sets(keys,['Pnew','Lx','Ly'],loss)
        expected=list(combinations(sorted(loss,key=lambda k:(loss[k],k))[:12],3))
        expected.sort(key=lambda ks:(sum(loss[k] for k in ks),tuple(sorted(ks))))
        self.assertEqual(got,[tuple(sorted(ks)) for ks in expected[:12]])
        self.assertEqual(optimizer.removal_sets(keys[:250],['Lnew'],loss),[()])
        self.assertEqual(len(got),12)

    def test_optimizer_accepted_moves_fresh_replay_and_corrupt_singleton_rejected(self):
        texts,nodes,keys,banned,_=prototype.counterexample()
        pools=optimizer.pool(texts,nodes,banned)
        state,info=optimizer.optimize(texts,nodes,keys,pools,banned,{'trials':180,'seconds':10},'TB')
        self.assertLess(state['selections'],24)
        self.assertLessEqual(info['trials'],180)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            trace=info.pop('trace')
            for name,value in [('pool.json',pools),('trace.json',trace),('dictionary.json',state['keys'])]:report.run.analyze.write(root/name,value)
            arm={'arm':'TB','fit_search':{'search':info,'fit_selections':state['selections']}}
            got=report.audit_admissions(root,arm,texts,keys)
            self.assertGreater(len(got['accepted_moves']),0)
            accepted=next(r for r in trace if 'accepted_round' in r)
            trial=next(r for r in trace if r.get('trial')==accepted['accepted_trial'])
            trial['package_bytes']+=1
            report.run.analyze.write(root/'trace.json',trace)
            with self.assertRaises(AssertionError):report.audit_admissions(root,arm,texts,keys)


if __name__=='__main__':unittest.main()
