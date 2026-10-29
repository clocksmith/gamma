"""Finite development checks only; no admission or independent qualification."""
import importlib.util
from pathlib import Path
import json
import random
import subprocess
import unittest
import hashlib

ROOT=Path(__file__).parent

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
A=load(ROOT/'adapters.py','gamma_ds39_adapters');O=load(ROOT/'oracles.py','gamma_ds39_candidate_oracles');C=load(ROOT/'cases.py','gamma_ds39_candidate_cases')

class Candidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows={pid:C.build_cases(pid,True) for pid in O.IDS}
        cls.contracts={r['id']:r for r in json.loads((ROOT/'contracts.json').read_text())['problems']}

    def invoke(self,pid,module,row,wrapper=False):
        args=A.native(pid,row['args']);before=A.effects(pid,args)
        original=random.randrange;ticket=0
        if pid==710:
            def draw(bound):
                nonlocal ticket
                value=ticket%bound;ticket+=1;return value
            random.randrange=draw
        try:
            fn=getattr(module.Solution(),self.contracts[pid]['official_interface']['name']) if wrapper else module.solve
            result=fn(*args)
        finally:random.randrange=original
        self.assertEqual(A.effects(pid,args),before,'input mutation')
        return A.normalize(pid,result,before[1])

    def test_python_against_independent_references(self):
        for pid,rows in self.rows.items():
            module=load(ROOT/'python'/f'{pid}.py',f'gamma_ds39_candidate_{pid}')
            for index,row in enumerate(rows):
                with self.subTest(pid=pid,case=index,category=row['category']):
                    self.assertTrue(A.matches(pid,self.invoke(pid,module,row),row['expected'],row['args']))
            if pid not in O.CLASSES:
                with self.subTest(pid=pid,official_wrapper=True):self.assertTrue(A.matches(pid,self.invoke(pid,module,rows[0],True),rows[0]['expected'],rows[0]['args']))

    def test_javascript_against_independent_references(self):
        packets=[];expected=[]
        for pid,rows in self.rows.items():
            for row in rows:packets.append({'pid':pid,'args':row['args']});expected.append((pid,row))
            if pid not in O.CLASSES:packets.append({'pid':pid,'args':rows[0]['args'],'wrapper':self.contracts[pid]['official_interface']['name']});expected.append((pid,rows[0]))
        run=subprocess.run(['node',str(ROOT/'development_runner.cjs')],input=json.dumps(packets),text=True,capture_output=True,timeout=120)
        self.assertEqual(run.returncode,0,run.stderr);results=json.loads(run.stdout);self.assertEqual(len(results),len(expected))
        for index,(result,(pid,row)) in enumerate(zip(results,expected)):
            with self.subTest(pid=pid,case=index,category=row['category']):
                self.assertTrue(result['ok'],result.get('error'))
                actual=result['result']
                if pid==652:actual=sorted(actual,key=repr)
                if pid==721:actual=sorted(actual)
                self.assertTrue(A.matches(pid,actual,row['expected'],row['args']),str(actual)[:150])

    def test_modules_have_no_io_or_external_dependencies(self):
        import ast
        allowed={'heapq','collections','fractions','array','random'}
        for pid in O.IDS:
            source=(ROOT/'python'/f'{pid}.py').read_text();tree=ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):self.assertTrue(all(x.name in allowed for x in node.names))
                if isinstance(node,ast.ImportFrom):self.assertIn(node.module,allowed)
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):self.assertNotIn(node.func.id,{'open','input','print','exec','eval','__import__'})
            text=(ROOT/'javascript'/f'{pid}.js').read_text()
            for forbidden in ['require(', 'process.', 'console.', 'fetch(', 'XMLHttpRequest']:self.assertNotIn(forbidden,text)
if __name__=='__main__':unittest.main()
