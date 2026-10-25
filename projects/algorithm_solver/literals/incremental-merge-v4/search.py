"""Exact first-two-gate branch bound; full worklist, no top-k or heuristic skip."""
import time
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("incremental_v3_core",HERE.parent/"incremental-merge-v3/search.py")
search=importlib.util.module_from_spec(spec);spec.loader.exec_module(search)
joint=search.joint;ALPHABET=search.ALPHABET;digest=search.digest
objective=search.v2.legacy.objective

class Builder(search.Builder):
 def gate_bound(self,state,piece):
  # Source selection minimizes selection count before its tie breaks, so the
  # perproblem minimum over every variant is the exact relevant lower bound.
  counts={pid:row['selections'] for pid,row in state['selected'].items()}
  if piece not in state['learned']:
   length=len(piece)
   for key,starts in self.graph.occurrence(piece).items():
    if key not in state['all_rows']:continue
    pid=self.owners[key]
    uses=min(len(starts),len(self.texts[key])//length)
    lower=max(0,state['all_rows'][key]['selections']-uses*(length-1))
    counts[pid]=min(counts[pid],lower)
  return (sum(n>96 for n in counts.values()),sum(n>32 for n in counts.values()))

 def best_move(self,state,*,prune=True):
  moves=self.compositions(state);bounds={};work=[]
  for piece,removed in moves:
   if self.deadline is not None and time.process_time()>=self.deadline:raise TimeoutError('bounded exact gate-bound slice exhausted')
   if piece not in bounds:bounds[piece]=self.gate_bound(state,piece)
   work.append((bounds[piece],piece,removed))
  work.sort(key=lambda row:(row[0],len(row[1]),row[1],row[2]))
  best=None;skipped=0;evaluated=0;current=objective(state['metrics'])
  for bound,piece,removed in work:
   incumbent=current[:2] if best is None else best[0][0][:2]
   # Equality cannot be pruned: later character/selection/byte terms may win.
   if prune and bound>incumbent:skipped+=1;continue
   learned=sorted((set(state['learned'])-set(removed))|{piece})
   candidate=self.score(state['ids'],learned,state['all_rows'],[piece,*removed]);evaluated+=1
   if objective(candidate['metrics'])>=current:continue
   rank=(objective(candidate['metrics']),len(learned),piece,removed)
   if best is None or rank<best[0]:best=(rank,piece,removed,candidate)
  return best,{'worklist':len(moves),'distinct_piece_bounds':len(bounds),'exact_evaluations':evaluated,'safely_pruned':skipped}

 def run(self):
  ids=sorted(self.references);resumed=self.resumed.get(('consolidation',tuple(ids)))
  state=self.score(ids,resumed['learned_literals'] if resumed else self.initial)
  if resumed and resumed['operation'].endswith('-exhausted'):return state
  self.emit('consolidation-start',state)
  while True:
   best,stats=self.best_move(state)
   if best is None:
    self.emit('consolidation-exhausted',state,candidates_considered=stats['worklist'],bound_accounting=stats);return state
   _,piece,removed,candidate=best
   self.emit('consolidation-add',candidate,added=piece,retired=list(removed),previous_metrics=state['metrics'],candidates_considered=stats['worklist'],bound_accounting=stats,move_kind='audited-primitive-union' if piece in self.allowed else 'adjacent-parent-composition',changed_source_problems=[p for p in ids if state['choices'][p]!=candidate['choices'][p]])
   state=candidate
