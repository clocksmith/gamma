"""Observer-to-independent-host-checker toy integration; no candidate execution."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

HERE=Path(__file__).resolve().parent

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
h=load(HERE/'harness.py','p_integration_observer')
o=load(HERE/'host_check.py','p_successor_host_check')
class TreeNode:
    def __init__(self,val=0,left=None,right=None):self.val,self.left,self.right=val,left,right
class Node:
    def __init__(self,val=0,left=None,right=None,next=None):self.val,self.left,self.right,self.next=val,left,right,next

class IntegrationTests(unittest.TestCase):
    def test_python_all_ten_wrappers_against_independent_checker(self):
        board=[[str((r*3+r//3+c)%9+1) for c in range(9)] for r in range(9)]
        fixtures=[(17,['2'],lambda self,digits:['c','a','b']),(37,[board],lambda self,board:None),(65,['1'],lambda self,s:True),(87,['a','a'],lambda self,a,b:True),(95,[1],lambda self,n:[TreeNode(1)]),(108,[[1,2]],lambda self,nums:TreeNode(1,None,TreeNode(2)))]
        def recover(self,root):root.val,root.left.val=root.left.val,root.val
        def flatten(self,root):root.right,root.left=root.left,None
        def connect(self,root):root.left.next=root.right;return root
        fixtures.extend([(99,[{'__tree_node__':[1,2,3]}],recover),(114,[{'__tree_node__':[1,2]}],flatten),(116,[{'__next_node__':[1,2,3]}],connect),(117,[{'__next_node__':[1,2,3]}],connect)])
        for pid,args,method in fixtures:
            solution=type('Solution',(),{h.METHODS[pid]:method});record=h.observe({'Solution':solution,'TreeNode':TreeNode,'Node':Node},pid,{'args':args})
            self.assertEqual(o.check_observation(pid,args,record,'python'),(True,None),pid)
            damaged=dict(record,method='solve')
            self.assertFalse(o.check_observation(pid,args,damaged,'python')[0])
    def test_js_all_ten_wrappers_against_independent_checker(self):
        node=os.environ.get('NODE_BIN') or shutil.which('node')
        if not node:self.skipTest('existing Node runtime unavailable; no installation')
        result=subprocess.run([node,str(HERE/'toy_records.cjs')],capture_output=True,check=True,timeout=20)
        rows=[json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual({row['pid'] for row in rows},set(h.METHODS))
        for row in rows:self.assertEqual(o.check_observation(row['pid'],row['args'],row['record'],'javascript'),(True,None),row['pid'])

if __name__=='__main__':unittest.main()
