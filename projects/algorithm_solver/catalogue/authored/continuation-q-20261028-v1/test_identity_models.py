import importlib.util
from pathlib import Path
import unittest
_spec=importlib.util.spec_from_file_location('gamma_q_toy_identity_models',Path(__file__).with_name('identity_models.py'))
_m=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_m)
class ToyList:
    def __init__(self,value):self.val=value;self.next=None
class ToyGraph:
    def __init__(self,value):self.val=value;self.neighbors=[]
class ToyRandom:
    def __init__(self,value):self.val=value;self.next=None;self.random=None
class Identities(unittest.TestCase):
    def test_original_cycle_identity(self):
        head,nodes=_m.materialize(142,{'values':[7,7],'pos':1},ToyList)
        self.assertEqual(_m.original_entry(head.next,nodes),1)
        with self.assertRaises(ValueError):_m.original_entry(ToyList(7),nodes)
        self.assertEqual(_m.snapshot(142,nodes)[1]['next'],1)
    def test_graph_clone_alias_rejected(self):
        root,nodes=_m.materialize(133,{'values':[1,2],'neighbors':[[1],[0]],'root':0},ToyGraph)
        with self.assertRaises(ValueError):_m.clone_pool(133,root,nodes)
        clone,pool=_m.materialize(133,{'values':[1,2],'neighbors':[[1],[0]],'root':0},ToyGraph)
        self.assertEqual(len(_m.clone_pool(133,clone,nodes)),2)
        self.assertEqual(_m.snapshot(133,nodes),_m.snapshot(133,pool))
    def test_random_alias_topology(self):
        head,nodes=_m.materialize(138,{'values':[1,1],'random':[1,0]},ToyRandom)
        snap=_m.snapshot(138,nodes);self.assertEqual(snap[0]['random'],1);self.assertEqual(snap[1]['random'],0)
        with self.assertRaises(ValueError):_m.clone_pool(138,head,nodes)
    def test_reorder_original_pool(self):
        head,nodes=_m.materialize(143,{'values':[1,1,1,1]},ToyList)
        for a,b in zip([0,3,1,2],[3,1,2,None]):nodes[a].next=None if b is None else nodes[b]
        self.assertEqual(_m.reordered(head,nodes,None)['original_identity_order'],[0,3,1,2])
        with self.assertRaises(ValueError):_m.reordered(head,nodes,head)
if __name__=='__main__':unittest.main()
