"""R host-checker integration and prospective packet controls, source-free only."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import harness
import host_check
import plan
from test_observers import ListNode,TreeNode

class Integration(unittest.TestCase):
    def test_six_python_official_toy_entries(self):
        class LRUCache:
            def __init__(self,c):self.data={}
            def get(self,k):return self.data.get(k,-1)
            def put(self,k,v):self.data[k]=v
        class MinStack:
            def __init__(self):self.values=[]
            def push(self,v):self.values.append(v)
            def pop(self):self.values.pop()
            def top(self):return self.values[-1]
            def getMin(self):return min(self.values)
        class BSTIterator:
            def __init__(self,root):self.root=root
            def next(self):return self.root.val
            def hasNext(self):return True
        class Solution:
            def maxProfit(self,k,p):return 7
            def insertionSortList(self,h):
                b=h.next;b.next=h;h.next=None;return b
            def getIntersectionNode(self,a,b):return b
        ns={'LRUCache':LRUCache,'MinStack':MinStack,'BSTIterator':BSTIterator,'Solution':Solution,'ListNode':ListNode,'TreeNode':TreeNode}
        fixtures={146:[['LRUCache','put','get'],[[1],[2,7],[2]]],155:[['MinStack','push','top','getMin','pop'],[[],[-2],[],[],[]]],147:[{'__list_node__':[2,1]}],160:[{'__list_graph__':{'nodes':[{'value':7,'next':1},{'value':7,'next':None}],'argument_roots':[0,1]}}],173:[['BSTIterator','hasNext','next'],[[{'__tree_node__':[3]}],[],[]]],188:[1,[0,7]]}
        for pid,args in fixtures.items():
            record=harness.observe(ns,pid,{'args':args});self.assertEqual(host_check.check(pid,args,record,'python'),(True,None))
            record['native_route']='solve';self.assertFalse(host_check.check(pid,args,record,'python')[0])
    def test_six_javascript_official_toy_entries(self):
        raw=subprocess.check_output(['node',str(Path(__file__).with_name('toy_records.cjs'))],timeout=20)
        rows=json.loads(raw);self.assertEqual(len(rows),6)
        for row in rows:self.assertEqual(host_check.check(row['pid'],row['args'],row['record'],'javascript'),(True,None))
    def test_isolated_python_main_loads_only_pinned_local_graph_helper(self):
        root=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)
            for name in ('harness.py','native_graphs.py'):(target/name).write_bytes((root/name).read_bytes())
            (target/'program.py').write_text('class Solution:\n    def maxProfit(self,k,prices): return 7\n')
            (target/'inputs.json').write_bytes(plan.encoded({'schema':'gamma.r-official-packet.v1','problem_id':188,'calls':[{'args':[1,[0,7]]}]}))
            output=subprocess.check_output([sys.executable,'-I','-S','harness.py'],cwd=target,timeout=20)
            rows=[json.loads(line) for line in output.splitlines()]
            self.assertEqual(rows[-1],{'done':1});self.assertEqual(host_check.check(188,[1,[0,7]],rows[0],'python'),(True,None))

    def test_javascript_main_uses_original_named_function(self):
        root=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)
            for name in ('harness.cjs','native_graphs.cjs'):(target/name).write_bytes((root/name).read_bytes())
            (target/'program.cjs').write_text('module.exports={maxProfit:(k,prices)=>7};\n')
            (target/'inputs.json').write_bytes(plan.encoded({'schema':'gamma.r-official-packet.v1','problem_id':188,'calls':[{'args':[1,[0,7]]}]}))
            output=subprocess.check_output(['node','--jitless','--single-threaded','--max-old-space-size=256','harness.cjs'],cwd=target,timeout=20,stderr=subprocess.PIPE)
            rows=[json.loads(line) for line in output.splitlines()]
            self.assertEqual(rows[-1],{'done':1});self.assertEqual(host_check.check(188,[1,[0,7]],rows[0],'javascript'),(True,None))

    def test_projection_bounds_all_six_javascript_toy_records(self):
        rows=json.loads(subprocess.check_output(['node',str(Path(__file__).with_name('toy_records.cjs'))],timeout=20))
        for row in rows:
            expected=host_check.oracle.expected(row['pid'],row['args'])
            bound=plan.projection(row['pid'],[{'args':row['args'],'expected':expected}],'javascript',host_check.oracle)[0]
            actual=len(plan.encoded({'i':0,**row['record']}))+1
            self.assertLessEqual(actual,bound)

    def test_plan_keeps_every_case_and_expected_values_outside_packet(self):
        rows=[{'args':[1,[0,7]],'expected':7},{'args':[1,[0]],'expected':0}]
        p=plan.batch_plan(188,rows,host_check.oracle)
        self.assertEqual(p['admitted_distinct_cases'],2);self.assertEqual(p['blocked_cases'],[])
        for b in p['batches']:
            wire=plan.packet(188,rows,b['indices']);self.assertTrue(all(set(c)=={'args'} for c in wire['calls']))
            self.assertEqual(b['indices'][0],b['indices'][-1])
    def test_large_case_bracketing_and_explicit_block(self):
        # Synthetic projection costs test transport control, not a problem claim.
        rows=[{'args':[0],'expected':0},{'args':[1],'expected':1}]
        with patch.object(plan,'projection',return_value=[256,10*1024**2]):
            p=plan.batch_plan(188,rows,None)
            self.assertIn([0,1,0],[b['indices'] for b in p['batches']]);self.assertEqual(p['blocked_cases'],[])
        with patch.object(plan,'projection',return_value=[256,17*1024**2]):
            p=plan.batch_plan(188,rows,None)
            self.assertEqual([r['case'] for r in p['blocked_cases']],[1]);self.assertEqual(p['logical_cases'],2)
    def test_no_child_file_write_limit_confused_with_host_input(self):
        rows=[{'args':['x'*(2*1024**2)],'expected':0}]
        with patch.object(plan,'projection',return_value=[256]):
            p=plan.batch_plan(188,rows,None)
            self.assertEqual(p['admitted_distinct_cases'],1)
            self.assertGreater(p['batches'][0]['host_input_bytes'],1024**2)

if __name__=='__main__':unittest.main()
