"""Exact count-only proposals; reconstruct every accepted state's full worklist."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('incremental_v4_core',HERE.parent/'incremental-merge-v4/search.py')
search=importlib.util.module_from_spec(spec);spec.loader.exec_module(search)
joint=search.joint;ALPHABET=search.ALPHABET;digest=search.digest
class Builder(search.Builder):
 def compositions(self,state):
  if any('used' not in row for row in state['all_rows'].values()):
   graph=self.graphs[tuple(sorted(state['ids']))]
   state['all_rows']=graph.materialize(ALPHABET+state['learned'],state['all_rows'])
  return super().compositions(state)
