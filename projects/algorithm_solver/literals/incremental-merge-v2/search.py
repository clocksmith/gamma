"""Continue a vocabulary by exact adjacent composition and parent retirement."""
import importlib.util,itertools
from pathlib import Path
HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('incremental_v1_core',HERE.parent/'incremental-merge-v1/search.py')
legacy=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(legacy)
joint=legacy.joint;ALPHABET=legacy.ALPHABET;digest=legacy.digest

class Builder(legacy.Builder):
 def __init__(self,*args,initial=(),**kwargs):
  super().__init__(*args,**kwargs);self.initial=list(initial)
 def compositions(self,state):
  pairs=set()
  for pid in state['ids']:
   for key in self.groups[pid]:
    stream=state['all_rows'][key]['used'];pairs.update(zip(stream,stream[1:]))
  learned=set(state['learned']);moves=set()
  for left,right in sorted(pairs):
   piece=left+right
   if not self.legal(piece):continue
   parents=sorted({p for p in (left,right) if p in learned})
   for count in range(len(parents)+1):
    for removed in itertools.combinations(parents,count):
     candidate=(learned-set(removed))|{piece}
     if candidate==learned or len(candidate)>self.capacity-96:continue
     moves.add((piece,removed))
  return sorted(moves,key=lambda x:(len(x[0]),x[0],x[1]))
 def run(self):
  ids=sorted(self.references)
  resumed=self.resumed.get(('consolidation',tuple(ids)))
  state=self.score(ids,resumed['learned_literals'] if resumed else self.initial)
  if resumed and resumed['operation'].endswith('-exhausted'):return state
  self.emit('consolidation-start',state)
  while True:
   moves=self.compositions(state);best=None
   for piece,removed in moves:
    learned=sorted((set(state['learned'])-set(removed))|{piece})
    candidate=self.score(ids,learned,state['all_rows'],[piece,*removed])
    if legacy.objective(candidate['metrics'])>=legacy.objective(state['metrics']):continue
    rank=(legacy.objective(candidate['metrics']),len(learned),piece,removed)
    if best is None or rank<best[0]:best=(rank,piece,removed,candidate)
   if best is None:
    self.emit('consolidation-exhausted',state,candidates_considered=len(moves));return state
   _,piece,removed,candidate=best
   self.emit('consolidation-add',candidate,added=piece,retired=list(removed),previous_metrics=state['metrics'],
             candidates_considered=len(moves),changed_source_problems=[p for p in ids if state['choices'][p]!=candidate['choices'][p]])
   state=candidate
