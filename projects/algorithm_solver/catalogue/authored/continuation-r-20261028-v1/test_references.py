"""R independent source-free controls; never import candidate sources."""
from copy import deepcopy
from functools import lru_cache
import importlib.util
from itertools import product
from pathlib import Path
import unittest
SPEC=importlib.util.spec_from_file_location('r_case_controls',Path(__file__).with_name('cases.py'))
cases=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(cases)
o=cases.oracle

class References(unittest.TestCase):
    def test_blocked_members_never_get_oracles(self):
        self.assertEqual(o.BLOCKED_IDS,(156,159,161,163))
        for pid in o.BLOCKED_IDS:
            with self.assertRaises(ValueError):o.expected(pid,[])

    def test_LRU_recency_and_return_types(self):
        args=[['LRUCache','put','put','get','put','get','put','get','get','get'],[[2],[1,1],[2,2],[1],[3,3],[2],[4,4],[1],[3],[4]]]
        self.assertEqual(o.expected(146,args),[None,None,None,1,None,-1,None,-1,3,4])
        self.assertEqual(o.class_return_types(146,args,'javascript'),['constructed','undefined','undefined','number','undefined','number','undefined','number','number','number'])

    def test_LRU_timestamp_crosscheck(self):
        ops=(('get',[0]),('get',[1]),('put',[0,0]),('put',[1,1]),('put',[0,2]))
        for capacity in (1,2):
            for sequence in product(ops,repeat=4):
                cache={};clock={};out=[None]
                for tick,(name,row) in enumerate(sequence):
                    key=row[0]
                    if name=='get':
                        out.append(cache.get(key,-1))
                        if key in cache:clock[key]=tick
                    else:
                        cache[key]=row[1];clock[key]=tick
                        if len(cache)>capacity:
                            victim=min(clock,key=clock.get);del cache[victim];del clock[victim]
                        out.append(None)
                self.assertEqual(o.expected(146,[['LRUCache']+[r[0] for r in sequence],[[capacity]]+[r[1] for r in sequence]]),out)

    def test_MinStack_duplicates_bounds_nonempty(self):
        args=[['MinStack','push','push','push','getMin','pop','getMin','pop','top'],[[],[-2**31],[-2**31],[2**31-1],[],[],[],[],[]]]
        self.assertEqual(o.expected(155,args),[None,None,None,None,-2**31,None,-2**31,None,-2**31])
        for args in ([['MinStack','pop'],[[],[]]],[['MinStack','push'],[[],[True]]]):
            with self.assertRaises(ValueError):o.expected(155,args)

    def test_list_identity_ties_permitted_values_preserved(self):
        args=[{'__list_node__':[2,1,1]}];before=[{'id':i,**row} for i,row in enumerate(o.list_nodes(args[0]))]
        for order in ((1,2,0),(2,1,0)):
            after=[{'id':i,'value':v,'next':None} for i,v in enumerate([2,1,1])]
            for a,b in zip(order,order[1:]):after[a]['next']=b
            state={'before':before,'after':after,'argument_roots':[0],'result_root':order[0]};self.assertTrue(o.accepts_list_identity(args,state))
            wrong=deepcopy(state);wrong['after'][0]['value']=1;self.assertFalse(o.accepts_list_identity(args,wrong))
            wrong=deepcopy(state);wrong['after'][0]['next']=order[0];self.assertFalse(o.accepts_list_identity(args,wrong))

    def test_intersection_physical_identity_not_values(self):
        self.assertIsNone(o.expected(160,[cases.shared([1,1],[1,1],[])]))
        args=[cases.shared([1,1],[1],[1,1])];self.assertEqual(o.expected(160,args),3)
        self.assertEqual(o.expected(160,[cases.shared([],[],[8])]),0)
        nodes,roots,_=o.shared_graph(args[0]);snap=[{'id':i,**row} for i,row in enumerate(nodes)]
        state={'before':snap,'after':deepcopy(snap),'argument_roots':roots,'result_root':3};self.assertTrue(o.accepts_intersection_identity(args,state))
        state['result_root']=0;self.assertFalse(o.accepts_intersection_identity(args,state))

    def test_graph_cycle_and_bool_id_rejected(self):
        graph=cases.shared([1],[2],[]);graph['__list_graph__']['nodes'][0]['next']=0
        with self.assertRaises(ValueError):o.expected(160,[graph])
        graph=cases.shared([1],[2],[]);graph['__list_graph__']['argument_roots'][0]=False
        with self.assertRaises(ValueError):o.expected(160,[graph])

    def test_iterator_repeated_hasNext(self):
        args=[['BSTIterator','hasNext','hasNext','next','next','hasNext','next','hasNext'],[[{'__tree_node__':[2,1,3]}],[],[],[],[],[],[],[]]]
        self.assertEqual(o.expected(173,args),[None,True,True,1,2,True,3,False])
        self.assertEqual(o.class_return_types(173,args,'python'),['constructed','bool','bool','int','int','bool','int','bool'])
        with self.assertRaises(ValueError):o.expected(173,[['BSTIterator','next','next'],[[{'__tree_node__':[1]}],[],[]]])

    def test_profit_bruteforce_schedule_crosscheck(self):
        def brute(k,prices):
            @lru_cache(None)
            def walk(day,left):
                if not left:return 0
                return max([0]+[prices[sell]-prices[buy]+walk(sell+1,left-1) for buy in range(day,len(prices)) for sell in range(buy+1,len(prices))])
            return walk(0,k)
        for n in range(1,6):
            for prices in product((0,1,3),repeat=n):
                for k in (1,2,3):self.assertEqual(o.expected(188,[k,list(prices)]),brute(k,prices))

    def test_profit_max_boundaries_and_types(self):
        self.assertEqual(o.expected(188,[100,[0,1000]*500]),100000)
        self.assertEqual(o.expected(188,[100,list(range(1000))]),999)
        self.assertEqual(o.expected(188,[1,[1000]*1000]),0)
        for args in ([0,[1]],[1,[]],[True,[1]],[1,[False]]):
            with self.assertRaises(ValueError):o.validate(188,args)

if __name__=='__main__':unittest.main()
