"""Actual local development execution, not isolated qualification."""
import json,copy,subprocess,time,sys,importlib.util,traceback
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import oracles,cases

def load(pid):
    spec=importlib.util.spec_from_file_location('candidate_'+str(pid),ROOT/'python'/f'{pid}.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def invoke(module,pid,args,official=False):
    args=copy.deepcopy(args)
    if pid==863:args[0]=oracles.decode_tree(args[0])
    before=copy.deepcopy(args)
    if pid in [855,900,901]:
        ops,rows=args;receiver=getattr(module,ops[0])(*rows[0]);result=[None]
        for op,row in zip(ops[1:],rows[1:]):
            value=getattr(receiver,op)(*row)
            if op=='leave':assert value is None
            result.append(value)
    else:
        method='distanceK' if pid==863 else 'superEggDrop';fn=getattr(module.Solution(),method) if official else module.solve;result=fn(*args)
    if pid==863:
        assert oracles.encode_tree(args[0])==oracles.encode_tree(before[0]) and args[1:]==before[1:]
        assert type(result) is list and result is not args[0]
    else:assert args==before
    return result

def main():
    start=time.monotonic();records=[];failures=[];commands=[]
    for pid in cases.IDS:
        module=load(pid);generated=[('small',args,oracles.reference(pid,args),'independent small reference') for p,args in cases.small_cases() if p==pid]
        generated.extend(('boundary',args,expected,proof) for p,args,expected,proof in cases.boundary_cases() if p==pid)
        command=['node',str(ROOT/'development_runner.cjs'),str(ROOT)];commands.append(command)
        process=subprocess.run(command,input=json.dumps([{'id':pid,'args':args} for _,args,_,_ in generated]),text=True,capture_output=True,timeout=120);assert process.returncode==0,process.stderr
        js=json.loads(process.stdout);assert len(js)==len(generated)
        for i,(kind,args,expected,proof) in enumerate(generated):
            try:
                oracles.validate_domain(pid,args);assert 'error' not in js[i],js[i].get('error')
                for actual in [invoke(module,pid,args),invoke(module,pid,args,True),js[i]['result'],js[i]['official']]:assert oracles.compare(pid,actual,expected),(pid,kind,actual,expected)
            except Exception:failures.append({'id':pid,'case_index':i,'kind':kind,'args':args,'expected':expected,'traceback':traceback.format_exc()})
        rec={'id':pid,'small_cases_per_language':sum(kind=='small' for kind,*_ in generated),'boundary_cases_per_language':sum(kind=='boundary' for kind,*_ in generated)};records.append(rec);print(rec,'failures',len(failures),flush=True)
    receipt={'schema':'gamma.authored-development-checks.v1','records':records,'runtime_seconds':time.monotonic()-start,'python':sys.version,'node':subprocess.check_output(['node','--version'],text=True).strip(),'failure_count':len(failures),'failures':failures,'commands':commands,'invocation':'python3 development_checks.py','qualification_status':'unknown','entrypoints':'canonical+official for863/887; direct native class with fresh receivers twice per trace for855/900/901','effects':'arguments unchanged;863 result fresh array; native void returns checked'}
    index=1
    while (ROOT/f'development-results-attempt{index}.json').exists():index+=1
    (ROOT/f'development-results-attempt{index}.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if failures:raise SystemExit(1)
if __name__=='__main__':main()
