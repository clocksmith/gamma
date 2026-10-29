"""Independent small oracles and separate analytic boundaries; no qualification."""
import copy,importlib.util,json,subprocess,time,sys,traceback
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parent

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
o=load('next54a_oracles',R/'oracles.py');cases=load('next54a_cases',R/'cases.py')
def mutable(x,ids,unique=False):
 if isinstance(x,(list,dict)):
  if id(x) in ids:
   if unique:raise AssertionError('output alias')
   return
  ids.add(id(x))
  for value in (x.values() if isinstance(x,dict) else x):mutable(value,ids,unique)
def invoke(m,args,name,wrapper):
 a=copy.deepcopy(args);before=copy.deepcopy(a);inputs=set();mutable(a,inputs)
 result=(getattr(m.Solution(),name) if wrapper else m.solve)(*a)
 assert a==before;out=set();mutable(result,out,True);assert not out&inputs
 return result

def main():
 start=time.monotonic();metadata={x['id']:x for x in json.loads((R/'contracts.json').read_text())['problems']};failures=[];records=[];commands=[]
 for pid in cases.IDS:
  module=load('next54a_'+str(pid),R/'python'/f'{pid}.py');name=metadata[pid]['external_interface']['official']['name']
  scenarios=[('small',args,o.reference(pid,args),'independent small reference') for p,args in cases.small_cases() if p==pid]
  scenarios += [('boundary',args,expected,proof) for p,args,expected,proof in cases.boundary_cases() if p==pid]
  command=['node',str(R/'development_runner.cjs')];commands.append(command)
  proc=subprocess.run(command,input=json.dumps([{'id':pid,'args':a,'name':name} for kind,a,e,p in scenarios]),text=True,capture_output=True,timeout=120)
  assert proc.returncode==0,proc.stderr
  javascript=json.loads(proc.stdout);assert len(javascript)==len(scenarios)
  for i,(kind,args,expected,proof) in enumerate(scenarios):
   try:
    o.validate_domain(pid,args)
    assert 'error' not in javascript[i],javascript[i].get('error')
    results=[('python',invoke(module,args,name,False)),('python_wrapper',invoke(module,args,name,True)),('javascript',javascript[i]['result']),('javascript_wrapper',javascript[i]['wrapper'])]
    for language,result in results:assert o.compare(pid,args,result,expected),(language,result,expected)
   except Exception:failures.append({'id':pid,'case_index':i,'kind':kind,'args':args,'expected':expected,'traceback':traceback.format_exc(),'javascript':javascript[i]})
  records.append({'id':pid,'small_cases_per_language':sum(x[0]=='small' for x in scenarios),'boundary_cases_per_language':sum(x[0]=='boundary' for x in scenarios)})
  print(pid,records[-1],'failures',len(failures),flush=True)
 result={'schema':'gamma.authored-development-checks.v1','qualification_status':'unknown','runtime_seconds':time.monotonic()-start,'python':sys.version,'node':subprocess.check_output(['node','--version'],text=True).strip(),'invocation':'python3 development_checks.py','records':records,'small_cases_per_language':sum(x['small_cases_per_language'] for x in records),'boundary_cases_per_language':sum(x['boundary_cases_per_language'] for x in records),'canonical_and_official_checked':True,'mutation_and_alias_checks':True,'failure_count':len(failures),'failures':failures,'commands':commands}
 attempt=1
 while (R/f'development-results-attempt{attempt}.json').exists():attempt+=1
 (R/f'development-results-attempt{attempt}.json').write_text(json.dumps(result,indent=2)+'\n')
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
