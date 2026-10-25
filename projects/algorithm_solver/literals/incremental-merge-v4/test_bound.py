import importlib.util,os,random,sys,unittest
from pathlib import Path
CORE=Path(os.environ.get('GAMMA_INCREMENTAL_CORE',str(Path(__file__).resolve().parent)));sys.path.insert(0,str(CORE))
MODULE=Path(os.environ.get('GAMMA_GATE_BOUND_MODULE',str(CORE/'search.py')))
s=importlib.util.spec_from_file_location('gate_bound_test_module',MODULE);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class BoundTests(unittest.TestCase):
 def builder(self,texts):
  texts={key:'function solve(a){return '+repr(text).replace(chr(39),chr(34))+';}' for key,text in texts.items()}
  owners={key:key.split(':')[0] for key in texts};refs={pid:next(k for k in texts if owners[k]==pid) for pid in sorted(set(owners.values()))}
  return m.Builder(texts,owners,refs,{pid:'synthetic' for pid in refs},capacity=128)
 def test_exhaustive_synthetic_worklists(self):
  rng=random.Random(20261025);total=skipped=0
  for trial in range(100):
   shared=''.join(rng.choice('abcd;() ') for _ in range(rng.randrange(20,100)))
   texts={f'{pid}:{variant}':shared+''.join(rng.choice('abcd;() ') for _ in range(rng.randrange(3,25))) for pid in range(3) for variant in range(2)}
   b=self.builder(texts);pieces=sorted({text[i:i+n] for text in texts.values() for i in range(len(text)) for n in (2,3,4) if i+n<=len(text)})
   rng.shuffle(pieces);learned=[p for p in pieces if b.legal(p)][:32 if trial%2 else 8]
   state=b.score(sorted(b.references),learned)
   full_best=None
   for piece,removed in b.compositions(state):
    candidate=b.score(state['ids'],sorted((set(learned)-set(removed))|{piece}),state['all_rows'],[piece,*removed])
    actual=(candidate['metrics']['above96'],candidate['metrics']['above32']);bound=b.gate_bound(state,piece)
    self.assertLessEqual(bound[0],actual[0]);self.assertLessEqual(bound[1],actual[1]);total+=1
    if m.objective(candidate['metrics'])<m.objective(state['metrics']):
     rank=(m.objective(candidate['metrics']),len(candidate['learned']),piece,removed)
     if full_best is None or rank<full_best:full_best=rank
   exact,all_stats=b.best_move(state,prune=False);bounded,stats=b.best_move(state,prune=True)
   self.assertEqual(full_best,None if exact is None else exact[0]);self.assertEqual(full_best,None if bounded is None else bounded[0])
   if exact is not None:self.assertEqual(exact[3]['choices'],bounded[3]['choices']);self.assertEqual(exact[3]['learned'],bounded[3]['learned'])
   self.assertEqual(stats['worklist'],all_stats['worklist']);skipped+=stats['safely_pruned']
  print({'synthetic_states':100,'all_move_bounds_checked':total,'safely_pruned':skipped})
 def test_existing_literal_has_zero_addition_gain(self):
  b=self.builder({'1:a':'abcabcXX','1:b':'abcdYY','2:a':'abcabcZZ'});state=b.score(['1','2'],['ab'])
  self.assertEqual(b.gate_bound(state,'ab'),(state['metrics']['above96'],state['metrics']['above32']))
 def test_all_variants_bound_not_only_selected(self):
  b=self.builder({'1:a':'abcdefghijklmno','1:b':'x'*40,'2:a':'abcdefghijklmno','2:b':'x'*40});state=b.score(['1','2'],[])
  # Unselected long variant can become the best after adding a repeated chunk.
  self.assertEqual(state['metrics']['above32'],2);self.assertTrue(all(v.endswith(':a') for v in state['choices'].values()))
  self.assertEqual(b.gate_bound(state,'x'*20),(0,0))
  new=b.score(['1','2'],['x'*20],state['all_rows'],['x'*20]);self.assertEqual(new['metrics']['above32'],0);self.assertTrue(all(v.endswith(':b') for v in new['choices'].values()))
if __name__=='__main__':unittest.main()
