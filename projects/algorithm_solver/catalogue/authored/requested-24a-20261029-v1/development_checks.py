"""Local native ABI/effects/oracle checks; independent isolated qualification pending."""
import importlib.util,json,subprocess,time,sys,traceback,copy,py_compile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
O=load('oracle24a',ROOT/'oracles.py');C=load('cases24a',ROOT/'cases.py')

def shape(root):
    q=[root];index={id(root):0};rows=[]
    for node in q:
        children=[]
        for child in (node.left,node.right):
            if child is None:children.append(None)
            else:
                if id(child) not in index:index[id(child)]=len(q);q.append(child)
                children.append(index[id(child)])
        rows.append([node.val,*children])
    return rows

def identities(obj,seen,unique=False):
    if isinstance(obj,(list,dict)):
        if id(obj) in seen:
            if unique:raise AssertionError('mutable alias')
            return
        seen.add(id(obj))
        for value in obj.values() if isinstance(obj,dict) else obj:identities(value,seen,unique)

def invoke(module,pid,args,official=False):
    args=copy.deepcopy(args);original=copy.deepcopy(args)
    if pid==1530:
        node=O.make_tree(args[0]);before=shape(node)
        output=module.Solution().countPairs(node,args[1]) if official else module.solve(node,args[1]);assert shape(node)==before
    else:
        ops,rows=args;name='ThroneInheritance' if pid==1600 else 'ParkingSystem';receiver=getattr(module,name)(*rows[0]);output=[None]
        for op,row in zip(ops[1:],rows[1:]):
            value=getattr(receiver,op)(*row)
            if op in ('birth','death'):assert value is None
            output.append(value)
    assert args==original
    inputs=set();outputs=set();identities(args,inputs);identities(output,outputs,True);assert not inputs&outputs
    return output

def main():
    start=time.monotonic();counts=[];failures=[];commands=[]
    # Small cases use reference(). Large cases use separately specified analytic expectations only.
    small=list(C.small_cases());boundaries=list(C.boundary_cases())
    for pid in [1530,1600,1603]:
        py_compile.compile(str(ROOT/'python'/f'{pid}.py'),doraise=True)
        syntax=['node','--check',str(ROOT/'javascript'/f'{pid}.js')];commands.append(syntax);subprocess.run(syntax,check=True,capture_output=True)
        module=load('candidate24a_'+str(pid),ROOT/'python'/f'{pid}.py')
        cases=[('small',args,O.reference(pid,args),'small independent oracle') for p,args in small if p==pid]
        cases += [('boundary',args,expected,reason) for p,args,expected,reason in boundaries if p==pid]
        command=['node',str(ROOT/'development_runner.cjs'),str(ROOT)];commands.append(command)
        process=subprocess.run(command,input=json.dumps([{'id':pid,'args':args} for _,args,_,_ in cases]),capture_output=True,text=True,timeout=120);assert process.returncode==0,process.stderr
        records=json.loads(process.stdout);assert len(records)==len(cases)
        for index,((kind,args,expected,reason),record) in enumerate(zip(cases,records)):
            try:
                O.validate_domain(pid,args);assert 'error' not in record,record.get('error')
                values={'python':invoke(module,pid,args),'javascript':record['result']}
                if pid==1530:values.update(python_wrapper=invoke(module,pid,args,True),javascript_wrapper=record['wrapper'])
                for language,result in values.items():
                    assert type(result) is type(expected) and result==expected,(language,pid,index,kind,str(result)[:120],str(expected)[:120])
                    # JSON bool and Python integer equality are insufficient: native scalar result types must agree.
                    if pid==1603:assert all(type(x) is bool for x in result[1:])
            except Exception:
                failures.append({'id':pid,'index':index,'kind':kind,'args':args,'expected':expected,'traceback':traceback.format_exc(),'js_record':record})
        counts.append({'id':pid,'small_cases_per_language':sum(kind=='small' for kind,*_ in cases),'boundary_cases_per_language':sum(kind=='boundary' for kind,*_ in cases),'official_wrapper_checked':pid==1530,'native_class_checked':pid!=1530})
        print(pid,counts[-1],'failures',len(failures),flush=True)
    receipt={'schema':'gamma.authoring-development-results.v1','qualification_status':'unknown','python_runtime':sys.version,'node_runtime':subprocess.check_output(['node','--version'],text=True).strip(),'runtime_seconds':time.monotonic()-start,'commands':commands,'invocation':'python3 development_checks.py','records':counts,'failures':failures,'failure_count':len(failures),'scope':'Local development references, analytic maximum boundaries, native ABI, mutation and aliases; no isolation, qualification, activation or promotion'}
    attempt=1
    while (ROOT/f'development-results-attempt{attempt}.json').exists():attempt+=1
    (ROOT/f'development-results-attempt{attempt}.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
