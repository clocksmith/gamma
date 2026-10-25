"""Private, bounded frozen-case replay. Never a stand-alone admission receipt.

Only the pinned dev-fit partition can be opened. Expected values remain on the
host. JSON-tree inputs are supported first; typed nodes and exact-integer
transport fail closed rather than receiving guessed adapters. Independent
contract/domain/complexity review remains a separate mandatory promotion gate.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / 'readable-joint-blocks-v1'
sys.path.insert(0, str(HERE.parent.parent))
from algsolve.judge import sandbox
from algsolve.judge.declared_comparison import exact
from algsolve.judge.functional_semantics import unordered_outer
BLOCKED = {1064, 1086, 1087, 1153, 2898}
SCHEMA = 'gamma.paired.frozen-case-replay.v1'

PYTHON_RUNNER = r'''import json,sys
packet=json.load(sys.stdin)
namespace={"__name__":"candidate"}
exec(compile(open("program.py").read(),"program.py","exec"),namespace)
def identities(args,result,keep=None):
    paths={}
    def visit(value,path):
        if type(value) not in (list,dict):return
        if keep is not None:keep.append(value)
        paths.setdefault(id(value),[]).append(path)
        if len(paths[id(value)])>1:return
        for key,item in (enumerate(value) if type(value) is list else value.items()):visit(item,path+"/"+str(key))
    for i,value in enumerate(args):visit(value,"arg/"+str(i))
    visit(result,"result")
    return paths
def valid(value):
    if value is None or type(value) in (bool,int,float,str):return
    if type(value) is list:
        for item in value:valid(item)
        return
    raise TypeError("unsupported non-JSON result")
for i,call in enumerate(packet["calls"]):
    args=call["args"]
    keep=[]
    before=identities(args,None,keep)
    try:
        result=getattr(namespace["Solution"](),packet["method"])(*args)
        valid(result);after=identities(args,result)
        record={"i":i,"result":result,"args_after":args,"alias_paths":sorted(sorted(v) for v in after.values() if len(v)>1),"identity_survival":sorted([sorted(paths),sorted(after.get(key,[]))] for key,paths in before.items())}
        print(json.dumps(record,allow_nan=False,separators=(",",":")))
    except Exception as error:print(json.dumps({"i":i,"error":type(error).__name__+": "+str(error)[:300]}))
print(json.dumps({"done":len(packet["calls"])}))
'''
JAVASCRIPT_RUNNER = r'''"use strict";
const fs=require("fs"),vm=require("vm");
const packet=JSON.parse(fs.readFileSync(0,"utf8"));
vm.runInThisContext(fs.readFileSync("program.js","utf8"),{timeout:1000});
const target=packet.baseline?vm.runInThisContext("solve"):vm.runInThisContext("Solution");
function identities(args,result){
 const paths=new Map();
 function visit(value,path){
  if(value===null||typeof value!=="object")return;
  if(paths.has(value)){paths.get(value).push(path);return;}
  paths.set(value,[path]);
  for(const key of Object.keys(value))visit(value[key],path+"/"+key);
 }
 args.forEach((value,i)=>visit(value,"arg/"+i));visit(result,"result");
 return paths;
}
function assertJSON(value){
 if(value===null||typeof value==="string"||typeof value==="boolean")return;
 if(typeof value==="number"&&Number.isFinite(value))return;
 if(Array.isArray(value)){for(const item of value)assertJSON(item);return;}
 if(typeof value==="object"&&Object.getPrototypeOf(value)===Object.prototype){for(const item of Object.values(value))assertJSON(item);return;}
 throw new Error("unsupported non-JSON result");
}
for(let i=0;i<packet.calls.length;i++){
 const args=packet.calls[i].args,before=identities(args,null);let record;
 try{const result=packet.baseline?target(...args):new target()[packet.method](...args);
 assertJSON(result);assertJSON(args);const after=identities(args,result);record={i,result,args_after:args,alias_paths:[...after.values()].filter(v=>v.length>1).map(v=>v.sort()),identity_survival:[...before].map(([key,paths])=>[paths.sort(),(after.get(key)||[]).sort()])};
 }catch(error){record={i,error:String(error)}}
 process.stdout.write(JSON.stringify(record)+"\n");
}
process.stdout.write(JSON.stringify({done:packet.calls.length})+"\n");
'''


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def write(path,value):path.write_bytes(encoded(value))


def plain(value):
    """Lossless matched JSON/Number transport only; no typed-marker guessing."""
    if value is None or type(value) in (str,bool):return True
    if type(value) is int:return abs(value)<=2**53-1
    if type(value) is float:return value==value and abs(value)<=2**53-1
    if type(value) is list:return all(plain(v) for v in value)
    # Typed objects, maps and custom containers need a separately reviewed adapter.
    return False


def packet(method,cases,baseline=False):
    return {'method':method,'baseline':baseline,'calls':[{'args':case['args']} for case in cases]}


def parse(raw,count):
    def pairs(items):
        out={}
        for key,value in items:
            if key in out:raise ValueError('duplicate output key')
            out[key]=value
        return out
    def invalid(value):raise ValueError('nonfinite output')
    rows=[json.loads(line,object_pairs_hook=pairs,parse_constant=invalid) for line in raw.splitlines()]
    if len(rows)!=count+1 or rows[-1]!={'done':count} or type(rows[-1].get('done')) is not int:raise ValueError('incomplete output')
    for i,row in enumerate(rows[:-1]):
        if type(row) is not dict or type(row.get('i')) is not int or row['i']!=i:raise ValueError('output index mismatch')
    return rows[:-1]


def matches(case,row):
    if 'error' in row or 'result' not in row:return False
    mode=case.get('compare','return')
    if mode=='return':return exact(row['result'],case['expected'])
    if mode=='return:unordered_outer':return unordered_outer(case['expected'],row['result'])
    return False


def effects_match(left,right):
    return ('args_after' in left and 'args_after' in right and
            exact(left['args_after'],right['args_after']) and
            type(left.get('alias_paths')) is list and
            sorted(left['alias_paths'])==sorted(right.get('alias_paths',[])) and
            type(left.get('identity_survival')) is list and
            sorted(left['identity_survival'])==sorted(right.get('identity_survival',[])))


def inputs(root,ids):
    transfer=load_module('paired_transfer',PILOT/'transfer.py')
    spec=transfer.derive_manifest()
    permitted=set(spec['partition']['dev_fit'])
    if len(permitted)!=300 or not set(ids)<=permitted:raise ValueError('outside frozen development-fit partition')
    receipt=json.loads(transfer.read_relative(root,'transfer-receipt.json'))
    if (receipt['partition']!=spec['partition'] or receipt.get('final_heldout_payload_files_opened')!=0
            or receipt.get('protected_payload_files_opened')!=0 or receipt.get('payload_files')!=1202
            or receipt.get('manifest_sha256')!=sha((json.dumps(spec,indent=2)+'\n').encode())):
        raise ValueError('transfer receipt scope or commitment mismatch')
    metadata_raw=transfer.read_relative(root,'population400/manifest.json')
    if sha(metadata_raw)!=receipt['filtered_metadata_sha256']:raise ValueError('filtered metadata hash mismatch')
    metadata={r['id']:r for r in json.loads(metadata_raw)['rows']}
    files={(r.get('id'),r['kind']):r for r in spec['files'] if r.get('id') in ids}
    result={}
    for pid in ids:
        payload={}
        for kind in ('source','cases'):
            row=files[pid,kind];raw=transfer.read_relative(root,row['path'])
            if sha(raw)!=row['sha256']:raise ValueError('frozen input hash mismatch')
            payload[kind]=raw
        result[pid]={'metadata':metadata[pid],**payload}
    return result,spec


def run(root,output,ids,node_path=None,max_wall=600):
    if output.resolve().is_relative_to(HERE.parents[3]):
        raise ValueError('private observations must stay outside the repository')
    if not ids or len(ids)!=len(set(ids)) or any(type(pid) is not int for pid in ids):
        raise ValueError('require unique integer development IDs')
    if not 1<=max_wall<=1800:raise ValueError('wall budget must be between 1 and 1800 seconds')
    output.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    frozen,spec=inputs(root,ids)
    inventory=json.loads((HERE/'manifest.json').read_text())['source_inventory']
    identities={(r['problem_id'],r['language']):r for r in inventory}
    from algsolve.judge import pinned_runtime
    node_path=node_path or Path('/usr/bin/node')
    runtime_identity=pinned_runtime.freeze_runtime(node_path)
    contract={'schema':SCHEMA,'ids':ids,'denominator':300,'protected_access':False,'runtime':runtime_identity,
              'python_runtime_sha256':sha(Path('/usr/bin/python3').read_bytes()),
              'code_sha256':sha(Path(__file__).read_bytes()),'pinned_runtime_sha256':sha(Path(pinned_runtime.__file__).read_bytes()),'sandbox_sha256':sha(Path(sandbox.__file__).read_bytes()),
              'batch_cases':32,'max_wall_seconds':max_wall,'source_identities':[identities[pid,lang] for pid in ids for lang in ('python','javascript')],
              'input_sha256':{str(pid):{kind:sha(v[kind]) for kind in ('source','cases')} for pid,v in frozen.items()},
              'comparison':'strict JSON return (stronger than legacy float tolerance), declared unordered outer only; exact predecessor mutation/alias/identity parity',
              'promotion_authority':False,'remaining_gates':['authoritative domain reconciliation','effect contract audit','complexity qualification','literal cost qualification']}
    write(output/'contract.json',contract)
    report={'schema':SCHEMA,'contract_sha256':sha(encoded(contract)),'rows':[],'candidate_executions':0,'m1_qualified':False,'promoted':False,'status':'running'}
    try:
        for pid,data in frozen.items():
            row={'id':pid,'status':'blocked','cases_passed':{},'failures':[]};report['rows'].append(row)
            cases=json.loads(data['cases'])
            if pid in BLOCKED:row['blocker']='known unresolved frozen-domain contract';continue
            if data['metadata']['transport']!='standard' or any(not plain(c.get('args')) or not plain(c.get('expected')) or c.get('kwargs') or c.get('validator') or c.get('compare','return') not in ('return','return:unordered_outer') for c in cases):
                row['blocker']='unsupported typed, exact-integer or non-JSON contract';continue
            observations={}
            for variant,language in (('baseline','javascript'),('python','python'),('javascript','javascript')):
                ident=identities[pid,language]
                source=data['source'] if variant=='baseline' else (HERE/ident['path']).read_bytes()
                semantics=(HERE/ident['semantics_path']).read_bytes()
                if variant!='baseline' and (sha(source)!=ident['sha256'] or sha(semantics)!=ident['semantics_sha256']):raise ValueError('candidate or semantics hash drift')
                method=json.loads(semantics)['entry_point'].split('.')[-1]
                records=[]
                for offset in range(0,len(cases),32):
                    if time.monotonic()-started>max_wall:raise TimeoutError('total wall budget exhausted')
                    batch=cases[offset:offset+32]
                    files={'program.py' if language=='python' else 'program.js':source,'runner.py' if language=='python' else 'runner.cjs':PYTHON_RUNNER if language=='python' else JAVASCRIPT_RUNNER}
                    limits=sandbox.Limits(cpu_seconds=3,wall_seconds=5,memory_bytes=1024**3,max_output_bytes=8*1024**2)
                    call_input=encoded(packet(method,batch,variant=='baseline'))
                    if language=='javascript':
                        result=pinned_runtime.run_node(node_path,manifest=runtime_identity,files=files,stdin=call_input,limits=limits,node_args=['--jitless','--single-threaded','--max-old-space-size=64','runner.cjs'])
                    else:
                        result=sandbox.run(['/usr/bin/python3','-I','-S','runner.py'],files=files,stdin=call_input,limits=limits)
                    report['candidate_executions']+=1
                    stem=output/f'{pid}-{variant}-{offset}'
                    stem.with_suffix('.stdout').write_bytes(result.stdout);stem.with_suffix('.stderr').write_bytes(result.stderr)
                    if not result.ok:raise RuntimeError(f'process failure {pid} {variant} {offset}')
                    records.extend(parse(result.stdout,len(batch)))
                observations[variant]=records
                passed=0
                for index,(case,record) in enumerate(zip(cases,records)):
                    correct=matches(case,record)
                    effect=variant=='baseline' or effects_match(record,observations['baseline'][index])
                    passed+=int(correct and effect)
                    if not correct or not effect:row['failures'].append({'variant':variant,'case_index':index,'return_correct':correct,'predecessor_effect_parity':effect})
                row['cases_passed'][variant]=passed
            row['cases_total']=len(cases)
            row['status']='frozen-case-parity-passed' if not row['failures'] else 'failed'
            write(output/'report.json',report)
        report['status']='completed'
    except Exception as error:
        report['status']='blocked' if isinstance(error,sandbox.SandboxUnavailable) else 'failed'
        report['error']=type(error).__name__+': '+str(error)
    finally:
        report['elapsed_seconds']=time.monotonic()-started;write(output/'report.json',report)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--inputs',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--ids',required=True);parser.add_argument('--node-path',type=Path);parser.add_argument('--max-wall',type=int,default=600)
    a=parser.parse_args();ids=[int(v) for v in a.ids.split(',')]
    if len(ids)!=len(set(ids)):raise SystemExit('duplicate ids')
    report=run(a.inputs,a.output,ids,a.node_path,a.max_wall)
    print(json.dumps({'status':report['status'],'candidate_executions':report['candidate_executions'],'rows':len(report['rows'])}))
    raise SystemExit(0 if report['status']=='completed' else 2)
