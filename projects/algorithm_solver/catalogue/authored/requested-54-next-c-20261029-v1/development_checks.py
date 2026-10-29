"""Local development checks only; not isolated qualification."""
import copy,importlib.util,json,subprocess,time,sys,traceback
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
o=load('c_oracles',R/'oracles.py');cases=load('c_cases',R/'cases.py')

def identities(value,out):
    if isinstance(value,(list,dict,o.TreeNode)):
        if id(value) in out:return
        out.add(id(value))
        for v in value.values() if isinstance(value,dict) else value if isinstance(value,list) else vars(value).values():identities(v,out)

def invoke(m,pid,args,name,official):
    args=copy.deepcopy(args);before=copy.deepcopy(args)
    if pid==919:
        ops,rows=args;original=o.build(rows[0][0]);original_before=o.snapshot(original);receiver=m.CBTInserter(original);input_nodes=set();identities(original,input_nodes);result=[None];stable=None
        for op,row in zip(ops[1:],rows[1:]):
            value=getattr(receiver,op)(*row)
            if op=='get_root':
                if stable is not None:assert value is stable
                stable=value;output_nodes=set();identities(value,output_nodes);assert not input_nodes&output_nodes;result.append(o.snapshot(value))
            else:assert type(value) is int;result.append(value)
        assert original_before==o.snapshot(original)
    elif pid==933:
        ops,rows=args;receiver=m.RecentCounter();result=[None]
        for op,row in zip(ops[1:],rows[1:]):
            value=getattr(receiver,op)(*row);assert type(value) is int;result.append(value)
    else:
        result=(getattr(m.Solution(),name) if official else m.solve)(*args);input_ids=set();output_ids=set();identities(args,input_ids);identities(result,output_ids);assert not input_ids&output_ids
    assert args==before
    return result

def main():
    start=time.monotonic();metadata={x['id']:x for x in json.loads((R/'statement-provenance.json').read_text())};failures=[];records=[];counts=Counter()
    all_small=list(cases.small_cases());boundaries=list(cases.boundary_cases())
    for pid in cases.IDS:
        m=load('candidate'+str(pid),R/'python'/f'{pid}.py');m.TreeNode=o.TreeNode;name=metadata[pid]['official_interface'].get('name');generated=[('small',args,o.reference(pid,args),'Independent reference') for p,args in all_small if p==pid]+[('boundary',args,expected,proof) for p,args,expected,proof in boundaries if p==pid]
        command=['node',str(R/'development_runner.cjs'),str(R)]
        run=subprocess.run(command,input=json.dumps([{'id':pid,'args':args,'name':name} for _,args,_,_ in generated]),capture_output=True,text=True,timeout=120)
        if run.returncode:raise RuntimeError(run.stderr)
        js=json.loads(run.stdout);assert len(js)==len(generated)
        for i,(kind,args,expected,proof) in enumerate(generated):
            try:
                o.domain(pid,args);assert 'error' not in js[i],js[i].get('error')
                for lang,outputs in [('python',[invoke(m,pid,args,name,False),invoke(m,pid,args,name,True)]),('javascript',[js[i]['result'],js[i]['wrapper']])]:
                    for actual in outputs:assert o.compare(pid,args,actual,expected),(pid,lang,kind,str(actual)[:150],str(expected)[:150])
                    counts[f'{pid}:{lang}:{kind}']+=1
            except Exception:failures.append({'id':pid,'case':i,'kind':kind,'args':args,'expected':expected,'traceback':traceback.format_exc(),'javascript':js[i]})
        records.append({'id':pid,'small_cases':sum(kind=='small' for kind,*_ in generated),'boundary_cases':sum(kind=='boundary' for kind,*_ in generated)});print(pid,records[-1],'failures',len(failures),flush=True)
    receipt={'schema':'gamma.authored-development-checks.v1','qualification_status':'unknown','runtime_seconds':time.monotonic()-start,'python':sys.version,'node':subprocess.check_output(['node','--version'],text=True).strip(),'records':records,'passed_counts':dict(counts),'failure_count':len(failures),'failures':failures,'invocation':'python3 development_checks.py','node_command':['node','development_runner.cjs','<cohort absolute directory>'],'scope':'Small independent oracles; separate analytic maxima; canonical and official wrappers/native constructor methods; input effects and aliases; not qualification'}
    attempt=1
    while (R/f'development-results-attempt{attempt}.json').exists():attempt+=1
    (R/f'development-results-attempt{attempt}.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if failures:raise SystemExit(1)
if __name__=='__main__':main()
