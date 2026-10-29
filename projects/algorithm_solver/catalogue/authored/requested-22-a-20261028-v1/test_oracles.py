import copy
import importlib.util
import json
from pathlib import Path
import random
import shutil
import subprocess
import unittest
HERE=Path(__file__).parent
def _load(name,file):
    spec=importlib.util.spec_from_file_location(name,file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
_o=_load('gamma_r22a_reference_test_oracles',HERE/'oracles.py')
_c=_load('gamma_r22a_reference_test_cases',HERE/'cases.py')
reference,validate_domain=_o.reference,_o.validate_domain
WRAPPERS={726:'countOfAtoms',730:'countPalindromicSubsequences',736:'evaluate',741:'cherryPickup'}
def trace(pid,pairs):return [[_o.CLASSES[pid]]+['book']*len(pairs),[[]]+[list(p) for p in pairs]]
def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(map(exact,a,b))
    return a==b
class References(unittest.TestCase):
    def test_formula(self):
        self.assertEqual(reference(726,['HHe2(OH)2']),'H3He2O2');self.assertEqual(reference(726,['((Ab)3Ab)2']),'Ab8')
    def test_calendars(self):
        self.assertEqual(reference(729,trace(729,[(1,5),(5,9),(4,6),(0,1)])),[None,True,True,False,True])
        self.assertEqual(reference(731,trace(731,[(1,5),(1,5),(1,5),(5,6),(4,6)])),[None,True,True,False,True,False])
        self.assertEqual(reference(732,trace(732,[(1,5),(2,3),(2,6),(7,8)])),[None,1,2,3,3])
        self.assertEqual(reference(732,trace(732,[(0,10**9)]*30)),[None]+list(range(1,31)))
    def test_palindromes(self):
        for s,count in [('aba',4),('abcd',4),('aaaa',4),('abba',6)]:self.assertEqual(reference(730,[s]),count)
    def test_palindrome_references_agree(self):
        rng=random.Random(7)
        for _ in range(300):
            s=''.join(rng.choice('abcd') for _ in range(rng.randrange(1,12)))
            self.assertEqual(reference(730,[s]),_o.palindrome_letter_intervals(s))
        self.assertEqual(_o.palindrome_letter_intervals('a'+'b'*298+'a'),298*2+2)
    def test_lisp_scope(self):
        self.assertEqual(reference(736,['(let x 1 (add (let x 2 x) x))']),3);self.assertEqual(reference(736,['(let x 2 y x x 5 (add x y))']),7)
    def test_cherries(self):
        for n in range(2,6):self.assertEqual(reference(741,[[[1]*n for _ in range(n)]]),4*n-4)
        self.assertEqual(reference(741,[[[0,-1],[-1,0]]]),0);self.assertEqual(reference(741,[[[1]]]),1)
    def test_domain(self):
        for pid,args in [(726,['H1']),(726,['()']),(726,['2H']),(726,['h']),(726,['H(O)0']),(729,[['MyCalendarTwo'],[[]]]),(729,trace(729,[(5,5)])),
                         (732,trace(732,[(0,1)]*401)),(730,['abe']),(736,['(add 1  2)']),(736,['(let add 1 add)']),(736,['(add x 1)']),(736,['(mult 65536 32768)']),
                         (741,[[[-1,0],[0,0]]]),(741,[[[0,0]]]),(741,[[[True]]])]:
            with self.assertRaises(ValueError,msg=str(args)[:60]):validate_domain(pid,args)
    def test_generated_cases_domain_valid(self):
        for pid in _o.IDS:
            for row in _c.build_cases(pid,include_maximum=True):validate_domain(pid,row['args'])
JS_RUNNER=r'''
const fs=require('fs');const job=JSON.parse(fs.readFileSync(0,'utf8'));const mod=require(job.path);const out=[];
for(const args of job.cases){const before=JSON.stringify(args);let value,native=null;
 value=mod(...args);
 if(job.cls){const C=mod[job.cls];const r=new C();native=[null];for(let i=1;i<args[0].length;i++)native.push(r.book(...args[1][i]));}
 else native=mod[job.wrapper](...args);
 out.push({value,native,unchanged:JSON.stringify(args)===before});}
process.stdout.write(JSON.stringify(out));'''
class Candidates(unittest.TestCase):
    """Author-local self-check of own candidates; not isolated qualification."""
    def run_python(self,pid,rows):
        path=HERE/'python'/f'{pid}.py'
        if not path.exists():self.skipTest('candidate absent')
        module=_load(f'gamma_r22a_candidate_python_{pid}',path);passed=0
        for row in rows:
            args=copy.deepcopy(row['args']);value=module.solve(*args)
            if pid in _o.CLASSES:
                receiver=getattr(module,_o.CLASSES[pid])();native=[None]+[receiver.book(*r) for r in args[1][1:]]
            else:native=getattr(module.Solution(),WRAPPERS[pid])(*args)
            self.assertTrue(exact(value,row['expected']) and exact(native,row['expected']),f'{pid} python {str(row["args"])[:80]}')
            self.assertEqual(args,row['args']);passed+=1
        return passed
    def run_javascript(self,pid,rows):
        path=HERE/'javascript'/f'{pid}.js'
        if not path.exists() or not shutil.which('node'):self.skipTest('candidate or node absent')
        job={'path':str(path),'cases':[r['args'] for r in rows],'cls':_o.CLASSES.get(pid),'wrapper':WRAPPERS.get(pid)}
        out=json.loads(subprocess.run(['node','-e',JS_RUNNER],input=json.dumps(job),capture_output=True,text=True,check=True).stdout)
        for row,got in zip(rows,out):
            self.assertTrue(exact(got['value'],row['expected']) and exact(got['native'],row['expected']),f'{pid} javascript {str(row["args"])[:80]}')
            self.assertTrue(got['unchanged'])
        self.assertEqual(len(out),len(rows));return len(out)
    def test_candidates(self):
        for pid in _o.IDS:
            rows=_c.build_cases(pid,include_maximum=True)
            for language,runner in [('python',self.run_python),('javascript',self.run_javascript)]:
                with self.subTest(pid=pid,language=language):
                    print(f'{pid} {language} {runner(pid,rows)}/{len(rows)} passed',flush=True)
if __name__=='__main__':unittest.main()
