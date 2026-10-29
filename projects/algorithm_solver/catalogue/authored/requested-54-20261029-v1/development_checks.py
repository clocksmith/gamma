"""Run small oracle checks and separate analytic maximum cases in both languages.
This local runner is development evidence, not isolated qualification.
"""
import copy,hashlib,importlib.util,json,subprocess,time,traceback,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
o=load('request54_oracles',ROOT/'oracles.py');c=load('request54_cases',ROOT/'cases.py')

def identities(x,out,unique=False):
    if isinstance(x,(list,dict)) or isinstance(x,o.TreeNode):
        if id(x) in out:
            if unique:raise AssertionError('mutable output alias')
            return
        out.add(id(x))
        values=x.values() if isinstance(x,dict) else x if isinstance(x,list) else vars(x).values()
        for v in values:identities(v,out,unique)

def invoke(module,pid,args,name,official=False):
    args=copy.deepcopy(args)
    if pid==872:args=[o.tree(t) for t in args]
    before=copy.deepcopy(args);inputs=set();identities(args,inputs)
    if pid==895:
        ops,rows=args;receiver=module.FreqStack(*rows[0]);result=[None]
        for op,row in zip(ops[1:],rows[1:]):
            value=getattr(receiver,op)(*row)
            if op=='push':assert value is None
            result.append(value)
    else:
        fn=getattr(module.Solution(),name) if official else module.solve
        result=fn(*args)
    if pid==872:assert [o.tree_value(t) for t in args]==[o.tree_value(t) for t in before]
    else:assert args==before
    outputs=set();identities(result,outputs,True);assert not inputs&outputs
    return [o.tree_value(t) for t in result] if pid==894 else result

def main():
    start=time.monotonic();metadata={r['id']:r for r in json.loads((ROOT/'statement-provenance.json').read_text())};failures=[];counts=Counter();commands=[];records=[]
    for pid in c.IDS:
        name=metadata[pid]['official_interface'].get('name','FreqStack');module=load('request54_'+str(pid),ROOT/'python'/f'{pid}.py');module.TreeNode=o.TreeNode
        generated=[('small',args,o.reference(pid,args),'Independent small-domain oracle') for p,args in c.small_cases() if p==pid]
        generated += [('boundary',args,expected,proof) for p,args,expected,proof in c.boundary_cases() if p==pid]
        packets=[{'id':pid,'args':a,'name':name} for _,a,_,_ in generated]
        command=['node',str(ROOT/'development_runner.cjs'),str(ROOT)];commands.append(command)
        result=subprocess.run(command,input=json.dumps(packets),capture_output=True,text=True,timeout=120)
        if result.returncode:raise RuntimeError(result.stderr)
        js=json.loads(result.stdout);assert len(js)==len(generated)
        for i,(kind,args,expected,proof) in enumerate(generated):
            try:
                o.validate_domain(pid,args)
                for language,actuals in [('python',[invoke(module,pid,args,name),invoke(module,pid,args,name,True)]),('javascript',[js[i].get('result'),js[i].get('wrapper')])]:
                    assert 'error' not in js[i],js[i].get('error')
                    for actual in actuals:
                        if pid==927 and kind=='boundary' and expected==[-1,-1]:assert actual==expected
                        else:assert o.compare(pid,args,actual,expected),(language,pid,kind,str(actual)[:200],str(expected)[:200])
                    counts[f'{pid}:{language}:{kind}']+=1
            except Exception:
                failures.append({'id':pid,'case_index':i,'kind':kind,'args':args,'expected':expected,'traceback':traceback.format_exc(),'javascript':js[i]})
        records.append({'id':pid,'small_cases':sum(k=='small' for k,*_ in generated),'boundary_cases':sum(k=='boundary' for k,*_ in generated)})
        print(pid,'small',records[-1]['small_cases'],'boundary',records[-1]['boundary_cases'],'failures',len(failures),flush=True)
    receipt={'schema':'gamma.authored-development-checks.v1','qualification_status':'unknown','runtime_seconds':time.monotonic()-start,'python':sys.version,'node':subprocess.check_output(['node','--version'],text=True).strip(),'records':records,'passed_counts':dict(counts),'failures':failures,'failure_count':len(failures),'commands':commands,'invocation':'python3 development_checks.py','scope':'Independent local oracle + analytic boundary, canonical and official wrapper, mutation/alias checks; no isolation/qualification/activation'}
    # Preserve attempts, including failures.
    attempt=1
    while (ROOT/f'development-results-attempt{attempt}.json').exists():attempt+=1
    (ROOT/f'development-results-attempt{attempt}.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
