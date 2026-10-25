"""Replay exact permitted 400 predecessors under a frozen successor runtime.

Reuses byte-identical historical typed/exact-integer harnesses and host oracle.
No final-heldout/protected input is accepted. Historical observations remain the
strict mutation/alias/type baseline; new failures never rewrite old receipts.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time
import hashlib
HERE=Path(__file__).resolve().parent
LIT=HERE.parent
sys.path.insert(0,str(LIT.parent))
from algsolve.judge import sandbox,pinned_runtime
from algsolve.judge import judge as host_judge


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);out=importlib.util.module_from_spec(spec);spec.loader.exec_module(out);return out

def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def write(path,value):path.write_bytes(encoded(value))


def tag(value,always=False):
    """Historical admission500 repair.tag: bool is never an integer transport."""
    if isinstance(value,bool):return value
    if isinstance(value,int) and (always or abs(value)>2**53-1):return {'__gamma_bigint_v1__':str(value)}
    if isinstance(value,list):return [tag(v,always) for v in value]
    if isinstance(value,dict):return {k:tag(v,always) for k,v in value.items()}
    return value


def exact(left,right):
    """Historical style150 parity equality, preserving bool and container types."""
    if isinstance(left,bool) or isinstance(right,bool):return type(left)==type(right) and left==right
    if isinstance(left,(int,float)) and isinstance(right,(int,float)):return left==right
    if type(left)!=type(right):return False
    if isinstance(left,list):return len(left)==len(right) and all(exact(a,b) for a,b in zip(left,right))
    if isinstance(left,dict):return left.keys()==right.keys() and all(exact(left[k],right[k]) for k in left)
    return left==right


def parse(raw,count):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('duplicate JSON key')
            result[k]=v
        return result
    def invalid(value):raise ValueError('nonfinite JSON')
    rows=[json.loads(line,object_pairs_hook=pairs,parse_constant=invalid) for line in raw.splitlines()]
    if len(rows)!=count+1 or type(rows[-1]) is not dict or rows[-1]!={'done':count} or type(rows[-1].get('done')) is not int:raise ValueError('incomplete protocol')
    for i,row in enumerate(rows[:-1]):
        if type(row) is not dict or type(row.get('i')) is not int or row['i']!=i:raise ValueError('invalid result index')
    return rows[:-1]


def load_inputs(root,ids=None):
    transfer=module('baseline_transfer',LIT/'readable-joint-blocks-v1/transfer.py')
    spec,manifest_hash=transfer.load_manifest()
    allowed=set(spec['partition']['dev_fit']+spec['partition']['dev_val'])
    ids=sorted(allowed) if ids is None else ids
    if not ids or len(ids)!=len(set(ids)) or any(type(x) is not int for x in ids) or not set(ids)<=allowed:raise ValueError('outside permitted frozen 400 partition')
    receipt=json.loads(transfer.read_relative(root,'transfer-receipt.json'))
    metadata=transfer.read_relative(root,'population400/manifest.json')
    if (receipt.get('manifest_sha256')!=manifest_hash or receipt.get('partition')!=spec['partition'] or receipt.get('payload_files')!=1202 or receipt.get('filtered_metadata_sha256')!=sha(metadata) or receipt.get('final_heldout_payload_files_opened')!=0 or receipt.get('protected_payload_files_opened')!=0):raise ValueError('private input receipt commitment mismatch')
    rows={r['id']:r for r in json.loads(metadata)['rows']}
    files={(r.get('id'),r['kind']):r for r in spec['files'] if r.get('id') in ids}
    loaded={};hashes={}
    for pid in ids:
        loaded[pid]={'metadata':rows[pid]};hashes[str(pid)]={}
        if rows[pid]['transport'] not in ('standard','exact-integer'):raise ValueError('unknown frozen transport')
        for kind in ('source','cases','baseline'):
            row=files[pid,kind];raw=transfer.read_relative(root,row['path'])
            if sha(raw)!=row['sha256']:raise ValueError('input hash mismatch '+row['path'])
            loaded[pid][kind]=raw;hashes[str(pid)][kind]=row['sha256']
    return loaded,hashes,manifest_hash


def run(root,output,node_path,ids=None,max_wall=1800):
    if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private output must be outside repository')
    if not 1<=max_wall<=3600:raise ValueError('wall budget outside 1..3600')
    output.mkdir(parents=True,exist_ok=False)
    loaded,hashes,input_manifest=load_inputs(root,ids)
    historical=json.loads((LIT/'name-search-v1/contract.json').read_text())['code_hashes']
    harnesses={}
    for name in ('harness.cjs','harness-exact-integer.cjs','qualify_rules.py'):
        raw=(LIT/'admission500-v1'/name).read_bytes()
        if sha(raw)!=historical['admission500-v1/'+name]:raise ValueError('historical harness/oracle hash mismatch')
        harnesses[name]=raw
    rules=module('baseline_rules',LIT/'admission500-v1/qualify_rules.py')
    runtime=pinned_runtime.freeze_runtime(node_path)
    contract={'schema':'gamma.baseline400.runtime-replay.v1','ids':list(loaded),'permitted_population':400,'m1_population':500,'protected_access':False,'input_manifest_sha256':input_manifest,'input_hashes':hashes,'runtime':runtime,'batch_cases':32,'max_wall_seconds':max_wall,
              'runner_sha256':sha(Path(__file__).read_bytes()),'sandbox_sha256':sha(Path(sandbox.__file__).read_bytes()),'runtime_adapter_sha256':sha(Path(pinned_runtime.__file__).read_bytes()),'host_judge_sha256':sha(Path(host_judge.__file__).read_bytes()),'historical_code_sha256':{name:sha(raw) for name,raw in harnesses.items()},
              'entry':'solve','pass_rule':'unchanged host judge_case AND exact historical result/type/args-before/args-after/alias/error observation parity','integer_transport':'historical repair.tag; alwaysBigInt only 633; otherwise tag abs(integer)>2^53-1','m1_qualified':False}
    write(output/'contract.json',contract)
    report={'schema':contract['schema'],'contract_sha256':sha(encoded(contract)),'status':'running','rows':[],'candidate_executions':0,'qualified':0,'m1_qualified':False,'protected_access':False}
    started=time.monotonic()
    try:
        for pid,data in loaded.items():
            cases=json.loads(data['cases']);base=json.loads(data['baseline']);meta=data['metadata']
            if len(cases)!=len(base) or len(cases)!=meta['cases']:raise ValueError('case/baseline count mismatch')
            row={'id':pid,'cases':len(cases),'checks_passed':0,'passed':False,'failures':[],'calls':[]};report['rows'].append(row)
            harness=harnesses['harness-exact-integer.cjs' if meta['transport']=='exact-integer' else 'harness.cjs']
            for offset in range(0,len(cases),32):
                if time.monotonic()-started>max_wall:raise TimeoutError('total runtime replay wall budget exceeded')
                batch=cases[offset:offset+32]
                calls=[{'args':tag(c['args'],pid==633) if meta['transport']=='exact-integer' else c['args']} for c in batch]
                result=pinned_runtime.run_node(node_path,manifest=runtime,files={'program.js':data['source'],'harness.cjs':harness,'inputs.json':encoded({'entry':'solve','calls':calls})},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2),node_args=['--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'])
                report['candidate_executions']+=1
                stem=f'{pid}-{offset}';(output/(stem+'.stdout')).write_bytes(result.stdout);(output/(stem+'.stderr')).write_bytes(result.stderr)
                row['calls'].append({'stem':stem,'exit_code':result.exit_code,'timed_out':result.timed_out,'wall_seconds':result.wall_seconds,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr)})
                try:
                    if not result.ok:raise RuntimeError('sandbox process failed')
                    records=parse(result.stdout,len(batch))
                    for index,(case,record) in enumerate(zip(batch,records)):
                        valid,observed=rules.judge_case(case,record);parity=exact(observed,base[offset+index]);row['checks_passed']+=int(valid and parity)
                        if not valid or not parity:row['failures'].append({'case_index':offset+index,'oracle':valid,'historical_effect_type_parity':parity,'error':record.get('error')})
                except Exception as error:row['failures'].append({'offset':offset,'execution_or_protocol':type(error).__name__+': '+str(error)})
            row['passed']=row['checks_passed']==len(cases) and not row['failures']
            report['qualified']+=int(row['passed']);write(output/'report.json',report)
            print(json.dumps({'id':pid,'passed':row['passed'],'checks_passed':row['checks_passed'],'cases':len(cases)}),flush=True)
        report['status']='completed'
    except Exception as error:
        report['status']='blocked' if isinstance(error,sandbox.SandboxUnavailable) else 'failed';report['error']=type(error).__name__+': '+str(error)
    finally:
        report['elapsed_seconds']=time.monotonic()-started;report['checks_passed']=sum(r['checks_passed'] for r in report['rows']);report['cases']=sum(r['cases'] for r in report['rows']);write(output/'report.json',report)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--node-path',type=Path,required=True);p.add_argument('--ids');p.add_argument('--max-wall',type=int,default=1800);a=p.parse_args()
    report=run(a.inputs,a.output,a.node_path,None if a.ids is None else [int(x) for x in a.ids.split(',')],a.max_wall)
    print(json.dumps({k:report[k] for k in ('status','qualified','candidate_executions','checks_passed','cases')}))
    raise SystemExit(0 if report['status']=='completed' and report['qualified']==len(report['rows']) else 2)
