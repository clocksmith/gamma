"""Finite independent development checks; no qualification/admission effects."""
import importlib.util
from pathlib import Path
import ast,json,subprocess,unittest
ROOT=Path(__file__).parent

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
O=load(ROOT/'oracles.py','gamma_public51_O_'+ROOT.name);C=load(ROOT/'cases.py','gamma_public51_C_'+ROOT.name);A=load(ROOT/'adapters.py','gamma_public51_A_'+ROOT.name)
class Candidates(unittest.TestCase):
 def test_python_independent_cases(self):
  for pid in O.IDS:
   module=load(ROOT/'python'/f'{pid}.py','gamma_public51_candidate_'+str(pid));rows=C.build_cases(pid,True)
   for index,row in enumerate(rows):
    with self.subTest(pid=pid,case=index,category=row['category']):
     args=A.native(pid,row['args']);before=A.effects(pid,args);actual=module.solve(*args);self.assertEqual(A.effects(pid,args),before);actual=A.normalize(pid,actual,before[1]);self.assertTrue(A.matches(pid,actual,row['expected'],row['args']),str(actual)[:100])
 def test_javascript_independent_cases(self):
  contracts={r['id']:r for r in json.loads((ROOT/'contracts.json').read_text())['problems']}
  for pid in O.IDS:
   rows=C.build_cases(pid,True);packets=[{'pid':pid,'args':r['args']} for r in rows];expected=list(rows)
   if pid not in O.CLASSES:packets.append({'pid':pid,'args':rows[0]['args'],'wrapper':contracts[pid]['official_interface']['name']});expected.append(rows[0])
   run=subprocess.run(['node',str(ROOT/'development_runner.cjs')],input=json.dumps(packets),text=True,capture_output=True,timeout=120);self.assertEqual(run.returncode,0,run.stderr);results=json.loads(run.stdout);self.assertEqual(len(results),len(expected))
   for index,(result,row) in enumerate(zip(results,expected)):
    with self.subTest(pid=pid,case=index,category=row['category']):
     self.assertTrue(result['ok'],result.get('error'));actual=result['result'];actual=sorted(actual,key=repr) if pid==1110 else actual;self.assertTrue(A.matches(pid,actual,row['expected'],row['args']),str(actual)[:100])
 def test_reference_domain_rejects_bad_inputs(self):
  for pid,args in [(963,[[[0,0],[0,0]]]),(964,[1,1]),(969,[[1,1]]),(975,[[]]),(980,[[[0]]]),(982,[[65536]]),(984,[10,0]),(996,[[0]*13]),(1000,[[1],1]),(1012,[0]),(1095,[0,[1,2,3]]),(1712,[[1,2]]),(1718,[21]),(1728,[['MCF'],0,1]),(1840,[1,[]]),(2735,[[0],1])]:
   if pid in O.IDS:
    with self.subTest(pid=pid),self.assertRaises((ValueError,IndexError,TypeError)):O.validate_domain(pid,args)
 def test_candidate_dependencies_and_io(self):
  allowed={'collections','heapq','bisect','functools','math','random','itertools'}
  for pid in O.IDS:
   tree=ast.parse((ROOT/'python'/f'{pid}.py').read_text())
   for n in ast.walk(tree):
    if isinstance(n,ast.Import):self.assertTrue(all(x.name in allowed for x in n.names))
    if isinstance(n,ast.ImportFrom):self.assertIn(n.module,allowed)
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,{'open','input','print','eval','exec','__import__'})
   text=(ROOT/'javascript'/f'{pid}.js').read_text()
   for forbidden in ['require(', 'process.', 'console.', 'fetch(']:self.assertNotIn(forbidden,text)
if __name__=='__main__':unittest.main()
