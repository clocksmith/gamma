"""Linked source/primitive union, preserving the accepted vocabulary lineage."""
import importlib.util,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('incremental_v2_core',HERE.parent/'incremental-merge-v2/search.py');v2=importlib.util.module_from_spec(spec);spec.loader.exec_module(v2)
joint=v2.joint;ALPHABET=v2.ALPHABET;digest=v2.digest
class Builder(v2.Builder):
 def __init__(self,*args,audited_helpers=(),**kwargs):
  super().__init__(*args,**kwargs)
  self.hard_banned=joint.banned_strings(self.texts);self.allowed={}
  for row in audited_helpers:
   piece=row['text']
   if hashlib.sha256(piece.encode()).hexdigest()!=row['sha256'] or len(piece.encode())!=row['bytes']:raise ValueError('primitive byte identity drift')
   if any(body and body in piece for body in self.hard_banned):raise ValueError('audited primitive contains a whole frozen solve/body')
   owners={self.owners[k] for k in self.graph.occurrence(piece)}
   if len(owners)<2:raise ValueError('primitive lacks distinct qualified fit support')
   self.allowed[piece]=row['sha256']
 def legal(self,piece):
  if piece in getattr(self,'allowed',{}):return True
  return super().legal(piece)
 def compositions(self,state):
  moves=set(super().compositions(state));learned=set(state['learned'])
  for piece in self.allowed:
   if piece in learned:continue
   for removed in [(),*((p,) for p in sorted(learned))]:
    if len((learned-set(removed))|{piece})<=self.capacity-96:moves.add((piece,removed))
  return sorted(moves,key=lambda x:(len(x[0]),x[0],x[1]))
 def run(self):
  ids=sorted(self.references);resumed=self.resumed.get(('consolidation',tuple(ids)))
  state=self.score(ids,resumed['learned_literals'] if resumed else self.initial)
  if resumed and resumed['operation'].endswith('-exhausted'):return state
  self.emit('consolidation-start',state)
  while True:
   moves=self.compositions(state);best=None
   for piece,removed in moves:
    learned=sorted((set(state['learned'])-set(removed))|{piece})
    candidate=self.score(ids,learned,state['all_rows'],[piece,*removed])
    if v2.legacy.objective(candidate['metrics'])>=v2.legacy.objective(state['metrics']):continue
    rank=(v2.legacy.objective(candidate['metrics']),len(learned),piece,removed)
    if best is None or rank<best[0]:best=(rank,piece,removed,candidate)
   if best is None:self.emit('consolidation-exhausted',state,candidates_considered=len(moves));return state
   _,piece,removed,candidate=best
   self.emit('consolidation-add',candidate,added=piece,retired=list(removed),previous_metrics=state['metrics'],candidates_considered=len(moves),move_kind='audited-primitive-union' if piece in self.allowed else 'adjacent-parent-composition',changed_source_problems=[p for p in ids if state['choices'][p]!=candidate['choices'][p]])
   state=candidate
