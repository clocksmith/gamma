"""Fresh exact-byte qualification for the direct-entry candidate supply."""
import argparse,importlib.util,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
_spec=importlib.util.spec_from_file_location('gamma_direct_entry_supply',HERE/'supply.py');supply=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(supply)
b=supply.b
from baseline_replay import load_inputs,module,sha,encoded,write,tag,exact,parse,sandbox,pinned_runtime,host_judge
def run(root,output,node_path,prepared,max_wall=1800):
    if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private output must be outside repository')
    if not 1<=max_wall<=3600:raise ValueError('wall budget outside 1..3600')
    output.mkdir(parents=True,exist_ok=False)
    supply_contract,sources=supply.load(root,prepared)
    ids=list(sources)
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
    contract={'schema':'gamma.direct-entry.runtime-replay.v1','ids':list(loaded),'permitted_population':400,'m1_population':500,'protected_access':False,'input_manifest_sha256':input_manifest,'input_hashes':hashes,'runtime':runtime,'batch_cases':32,'max_wall_seconds':max_wall,
              'runner_sha256':sha(Path(__file__).read_bytes()),'sandbox_sha256':sha(Path(sandbox.__file__).read_bytes()),'runtime_adapter_sha256':sha(Path(pinned_runtime.__file__).read_bytes()),'host_judge_sha256':sha(Path(host_judge.__file__).read_bytes()),'historical_code_sha256':{name:sha(raw) for name,raw in harnesses.items()},
              'entry':'solve','pass_rule':'unchanged host judge_case AND exact historical result/type/args-before/args-after/alias/error observation parity','integer_transport':'historical repair.tag; alwaysBigInt only 633; otherwise tag abs(integer)>2^53-1','m1_qualified':False}
    contract.update({'prepared':str(prepared),'supply_contract_sha256':sha(encoded(supply_contract)),'cohort':166,'unsupported':supply_contract['unsupported'],'sources':supply_contract['sources'],'baseline_loader_sha256':sha(Path(b.__file__).read_bytes()),'supply_code_sha256':supply.pins()})
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
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--node-path',type=Path,required=True);p.add_argument('--prepared',type=Path,required=True);p.add_argument('--max-wall',type=int,default=1800);a=p.parse_args()
 r=run(a.inputs,a.output,a.node_path,a.prepared,a.max_wall)
 print(json.dumps({k:r[k] for k in ('status','qualified','candidate_executions','checks_passed','cases')}));raise SystemExit(0 if r['status']=='completed' else 2)
