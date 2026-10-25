"""Bounded typed/effect qualification for five full-source traversal alternatives."""
import argparse,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'paired-authoring-v1'))
import baseline_replay as b
from baseline_replay import load_inputs,module,sha,encoded,write,tag,exact,parse,sandbox,pinned_runtime,host_judge
IDS=[103,104,107,111,112]
def pins():
 return {name:sha((HERE/name).read_bytes()) for name in ('qualify.py','verify.py','CONTRACT.md')}
def freeze(sources,output):
 if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('source freeze must stay outside repository')
 spec,_=b.module('traversal_transfer',LIT/'readable-joint-blocks-v1/transfer.py').load_manifest()
 if not set(IDS)<=set(spec['partition']['dev_fit']):raise ValueError('family is not entirely permitted dev-fit')
 raw={pid:(sources/f'{pid}.js').read_bytes() for pid in IDS}
 if any(not value for value in raw.values()):raise ValueError('empty complete source')
 contract={'schema':'gamma.traversal-family.sources.v1','ids':IDS,'source_directory':str(sources),'sources':{str(pid):{'path':f'{pid}.js','sha256':sha(value),'bytes':len(value)} for pid,value in raw.items()},'code_sha256':pins(),'baseline_loader_sha256':sha(Path(b.__file__).read_bytes()),'source_policy_sha256':sha((HERE/'CONTRACT.md').read_bytes()),'protected_access':False,'m1_population':500,'m1_qualified':False,'candidate_executions':0}
 output.mkdir(parents=True,exist_ok=False)
 for pid,value in raw.items():(output/f'{pid}.js').write_bytes(value)
 write(output/'contract.json',contract);return contract

def load_freeze(frozen):
 contract=json.loads((frozen/'contract.json').read_text())
 if contract.get('schema')!='gamma.traversal-family.sources.v1' or contract.get('ids')!=IDS or contract.get('code_sha256')!=pins() or contract.get('baseline_loader_sha256')!=sha(Path(b.__file__).read_bytes()) or contract.get('source_policy_sha256')!=sha((HERE/'CONTRACT.md').read_bytes()) or contract.get('protected_access') is not False or contract.get('m1_qualified') is not False:raise ValueError('frozen source/code/scope drift')
 if set(contract['sources'])!={str(i) for i in IDS}:raise ValueError('incomplete source population')
 sources={}
 for pid in IDS:
  row=contract['sources'][str(pid)]
  if row.get('path')!=f'{pid}.js':raise ValueError('noncanonical frozen source path')
  raw=(frozen/row['path']).read_bytes()
  if sha(raw)!=row['sha256'] or len(raw)!=row['bytes'] or not raw:raise ValueError('frozen source bytes drift')
  sources[pid]=raw
 return contract,sources

def run(root,output,node_path,frozen,max_wall=600):
    if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private output must be outside repository')
    if not 1<=max_wall<=3600:raise ValueError('wall budget outside 1..3600')
    output.mkdir(parents=True,exist_ok=False)
    source_contract,sources=load_freeze(frozen)
    ids=IDS
    loaded,hashes,input_manifest=load_inputs(root,ids)
    for pid,source in sources.items():
        loaded[pid]['source']=source
        (output/f'{pid}.js').write_bytes(source)
    historical=json.loads((LIT/'name-search-v1/contract.json').read_text())['code_hashes']
    harnesses={}
    for name in ('harness.cjs','harness-exact-integer.cjs','qualify_rules.py'):
        raw=(LIT/'admission500-v1'/name).read_bytes()
        if sha(raw)!=historical['admission500-v1/'+name]:raise ValueError('historical harness/oracle hash mismatch')
        harnesses[name]=raw
    rules=module('baseline_rules',LIT/'admission500-v1/qualify_rules.py')
    runtime=pinned_runtime.freeze_runtime(node_path)
    contract={'schema':'gamma.traversal-family.runtime-replay.v1','ids':list(loaded),'permitted_population':400,'m1_population':500,'protected_access':False,'input_manifest_sha256':input_manifest,'input_hashes':hashes,'runtime':runtime,'batch_cases':32,'max_wall_seconds':max_wall,
              'runner_sha256':sha(Path(__file__).read_bytes()),'sandbox_sha256':sha(Path(sandbox.__file__).read_bytes()),'runtime_adapter_sha256':sha(Path(pinned_runtime.__file__).read_bytes()),'host_judge_sha256':sha(Path(host_judge.__file__).read_bytes()),'historical_code_sha256':{name:sha(raw) for name,raw in harnesses.items()},
              'entry':'solve','pass_rule':'unchanged host judge_case AND exact historical result/type/args-before/args-after/alias/error observation parity','integer_transport':'historical repair.tag; alwaysBigInt only 633; otherwise tag abs(integer)>2^53-1','m1_qualified':False}
    contract.update({'source_freeze':str(frozen),'source_freeze_sha256':sha(encoded(source_contract)),'sources':source_contract['sources'],'baseline_loader_sha256':sha(Path(b.__file__).read_bytes()),'source_policy_sha256':source_contract['source_policy_sha256'],'scope':'fixed-five development-fit traversal family; no M1 claim'})
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
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 f=sub.add_parser('freeze');f.add_argument('--sources',type=Path,required=True)
 r=sub.add_parser('run');r.add_argument('--inputs',type=Path,required=True);r.add_argument('--node-path',type=Path,required=True);r.add_argument('--freeze',type=Path,required=True);r.add_argument('--max-wall',type=int,default=600)
 for parser in (f,r):parser.add_argument('--output',type=Path,required=True)
 a=p.parse_args()
 if a.command=='freeze':c=freeze(a.sources,a.output);print(json.dumps({'status':'frozen','ids':IDS,'candidate_executions':0,'m1_qualified':False}))
 else:
  result=run(a.inputs,a.output,a.node_path,a.freeze,a.max_wall);print(json.dumps({k:result[k] for k in ('status','qualified','candidate_executions','checks_passed','cases')}));raise SystemExit(0 if result['status']=='completed' else 2)
