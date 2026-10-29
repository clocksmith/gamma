"""Independent small-oracle and separate justified maximum-case development checks."""
import importlib.util,json,subprocess,time,traceback,sys,copy
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
    started=time.monotonic();o=load('gamma24b_oracles',ROOT/'oracles.py');c=load('gamma24b_cases',ROOT/'cases.py');h=load('gamma24b_harness',ROOT/'native_harness.py')
    counts=Counter();failures=[];commands=[]
    for pid in [1622,1656]:
        module=load('gamma24b_'+str(pid),ROOT/'python'/f'{pid}.py')
        cases=[('small',args,o.reference(pid,args),'independent literal reference') for p,args in c.small_cases() if p==pid]
        cases += [('boundary',args,expected,proof) for p,args,expected,proof in c.boundary_cases() if p==pid]
        packets=[{'id':pid,'args':args} for _,args,_,_ in cases]
        command=['node',str(ROOT/'native_harness.cjs')];commands.append(command)
        js=subprocess.run(command,input=json.dumps(packets),capture_output=True,text=True,timeout=120)
        assert js.returncode==0,js.stderr
        results=json.loads(js.stdout);assert len(results)==len(cases)
        for index,(kind,args,expected,proof) in enumerate(cases):
            try:
                o.validate_domain(pid,args)
                actual=h.observe(module,pid,copy.deepcopy(args));assert actual==expected
                counts[f'{pid}:python:{kind}']+=1
                assert 'error' not in results[index],results[index].get('error')
                assert results[index]['result']==expected
                counts[f'{pid}:javascript:{kind}']+=1
            except Exception:
                failures.append({'id':pid,'kind':kind,'case_index':index,'args':args,'expected':expected,'traceback':traceback.format_exc(),'js':results[index]})
        print(pid, 'small',sum(kind=='small' for kind,*_ in cases),'boundary',sum(kind=='boundary' for kind,*_ in cases),'failures',len(failures),flush=True)
    receipt={'schema':'gamma.native-authored-development-checks.v1','qualification_status':'unknown','elapsed_seconds':time.monotonic()-started,'python':sys.version,'node':subprocess.check_output(['node','--version'],text=True).strip(),'passed_counts':dict(counts),'failure_count':len(failures),'failures':failures,'commands':commands,'invocation':'python3 development_checks.py','limitations':'Local native-class execution, oracle results and valid boundary checks only; no isolated qualification or serving activation.'}
    attempt=1
    while (ROOT/f'development-results-attempt{attempt}.json').exists():attempt+=1
    (ROOT/f'development-results-attempt{attempt}.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if failures:raise SystemExit(1)
if __name__=='__main__':main()
