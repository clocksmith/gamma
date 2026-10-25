"""Fully charged solve adapters for independently replayed paired alternatives.

No AST rewriting, hidden helper or method substitution: append exact adapter
bytes to the entire candidate, then qualify those complete bytes afresh.
"""
import argparse
import json
from pathlib import Path
import re
import sys
import time
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import baseline_replay as b
import qualify as paired


def emit(source,method):
    if not re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*',method):raise ValueError('invalid declared method')
    adapter=('\nfunction solve(...args){return new Solution().'+method+'(...args);}\n').encode()
    return source+adapter,adapter


def verify_paired(inputs,report_path,ids):
    """Replay every case of all three variants for each requested problem.

    Historical successful strict-float receipts remain usable: the frozen source
    identities and actual observations must also pass the original host oracle.
    Their code/contract/observation hashes are retained in the new experiment.
    """
    report_raw=report_path.read_bytes();report=json.loads(report_raw)
    contract_raw=(report_path.parent/'contract.json').read_bytes();contract=json.loads(contract_raw)
    if report.get('contract_sha256')!=b.sha(contract_raw):raise ValueError('paired contract digest mismatch')
    if contract.get('schema')!='gamma.paired.frozen-case-replay.v1' or report.get('status') not in ('completed','failed','blocked') or contract.get('batch_cases')!=32 or contract.get('protected_access') is not False:raise ValueError('paired receipt scope/status mismatch')
    b.pinned_runtime.validate_manifest(contract['runtime'])
    frozen,_=paired.inputs(inputs,ids)
    identities={(r['problem_id'],r['language']):r for r in contract['source_identities']}
    approved={(r['problem_id'],r['language']):r for r in json.loads((HERE/'manifest.json').read_text())['source_inventory']}
    rows={r['id']:r for r in report['rows']}
    if len(identities)!=len(contract['source_identities']) or len(rows)!=len(report['rows']):raise ValueError('duplicate evidence identities')
    if not set(ids)<=set(contract['ids']):raise ValueError('requested IDs outside paired receipt')
    result={}
    for pid in ids:
        if pid in paired.BLOCKED:raise ValueError('unresolved alternative contract')
        row=rows.get(pid,{})
        if row.get('status')!='frozen-case-parity-passed' or row.get('failures')!=[]:raise ValueError('paired problem has no passing complete evidence')
        data=frozen[pid];cases=json.loads(data['cases'])
        if contract['input_sha256'].get(str(pid))!={k:b.sha(data[k]) for k in ('source','cases')}:raise ValueError('paired input identity mismatch')
        if row.get('cases_total')!=len(cases):raise ValueError('paired case coverage mismatch')
        for lang in ('python','javascript'):
            ident=identities[pid,lang]
            current=approved[pid,lang]
            if any(ident.get(k)!=current.get(k) for k in ('path','semantics_path','sha256','semantics_sha256')):raise ValueError('paired identity differs from approved source inventory')
            if b.sha((HERE/ident['path']).read_bytes())!=ident['sha256'] or b.sha((HERE/ident['semantics_path']).read_bytes())!=ident['semantics_sha256']:raise ValueError('paired source/sidecar no longer matches evidence')
        baseline=[];observations={}
        for variant in ('baseline','python','javascript'):
            if row['cases_passed'].get(variant)!=len(cases):raise ValueError('paired variant coverage mismatch')
            records=[]
            for offset in range(0,len(cases),32):
                stem=f'{pid}-{variant}-{offset}';raw=(report_path.parent/(stem+'.stdout')).read_bytes();stderr=(report_path.parent/(stem+'.stderr')).read_bytes()
                observations[stem]={'stdout_sha256':b.sha(raw),'stderr_sha256':b.sha(stderr)}
                records.extend(paired.parse(raw,len(cases[offset:offset+32])))
            if variant=='baseline':baseline=records
            for i,(case,record) in enumerate(zip(cases,records)):
                if not paired.matches(case,record) or (variant!='baseline' and not paired.effects_match(record,baseline[i])):raise ValueError('paired oracle/effect evidence replay failed')
        result[pid]={'paired_report_sha256':b.sha(report_raw),'paired_contract_sha256':b.sha(contract_raw),'paired_runner_sha256':contract['code_sha256'],'observation_hashes':observations,'identity':identities[pid,'javascript']}
    return result


def run(inputs,output,node_path,evidence,max_wall=600,candidate_ids=()):
    if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private observations must stay outside repository')
    if not 1<=max_wall<=1800:raise ValueError('bounded wall time required')
    output.mkdir(parents=True,exist_ok=False)
    eligible={}
    for item in evidence:
        ids=item['ids']
        if set(ids)&set(eligible):raise ValueError('duplicate adapted problem')
        eligible.update(verify_paired(inputs,Path(item['report']),ids))
    # Explicit new-mechanism route: absence of an old paired pass is recorded,
    # never disguised. The complete adapted bytes still face every historical
    # oracle/type/effect case below before any fit-pool eligibility.
    if candidate_ids:
        paired.inputs(inputs,list(candidate_ids))  # enforces dev-fit before payload reads
        inventory={(r['problem_id'],r['language']):r for r in json.loads((HERE/'manifest.json').read_text())['source_inventory']}
        for pid in candidate_ids:
            if pid in eligible or pid in paired.BLOCKED:raise ValueError('duplicate or unresolved new-mechanism candidate')
            eligible[pid]={'route':'explicit-new-mechanism-requires-fresh-full-qualification','prior_paired_pass':False,'identity':inventory[pid,'javascript']}
    if not eligible:raise ValueError('empty adapted source experiment')
    loaded,hashes,input_manifest=b.load_inputs(inputs,sorted(eligible))
    runtime=b.pinned_runtime.freeze_runtime(node_path)
    historical=json.loads((b.LIT/'name-search-v1/contract.json').read_text())['code_hashes']
    harness_path=b.LIT/'admission500-v1/harness.cjs';harness=harness_path.read_bytes()
    rules_path=b.LIT/'admission500-v1/qualify_rules.py'
    for name,path in [('harness.cjs',harness_path),('qualify_rules.py',rules_path)]:
        if b.sha(path.read_bytes())!=historical['admission500-v1/'+name]:raise ValueError('historical harness/oracle drift')
    rules=b.module('adapted_rules',rules_path)
    sources={};source_rows=[]
    for pid,proof in sorted(eligible.items()):
        ident=proof['identity'];source=(HERE/ident['path']).read_bytes();semantics_raw=(HERE/ident['semantics_path']).read_bytes()
        if b.sha(source)!=ident['sha256'] or b.sha(semantics_raw)!=ident['semantics_sha256']:raise ValueError('adapted candidate/sidecar identity drift')
        semantics=json.loads(semantics_raw);entry=semantics['entry_point']
        if not entry.startswith('Solution.'):raise ValueError('unsupported candidate interface')
        complete,adapter=emit(source,entry[len('Solution.'):]);sources[pid]=complete
        (output/f'{pid}.js').write_bytes(complete)
        source_rows.append({'id':pid,'candidate_sha256':b.sha(source),'semantics_sha256':b.sha(semantics_raw),'adapter_sha256':b.sha(adapter),'adapted_sha256':b.sha(complete),'candidate_bytes':len(source),'adapter_bytes':len(adapter),'complete_bytes':len(complete),'path':f'{pid}.js'})
    contract={'schema':'gamma.adapted-paired-qualification.v1','ids':sorted(eligible),'sources':source_rows,'paired_evidence':eligible,'input_hashes':hashes,'input_manifest_sha256':input_manifest,'runtime':runtime,'batch_cases':32,'max_wall_seconds':max_wall,'code_sha256':b.sha(Path(__file__).read_bytes()),'baseline_loader_sha256':b.sha(Path(b.__file__).read_bytes()),'paired_verifier_sha256':b.sha(Path(paired.__file__).read_bytes()),'harness_sha256':b.sha(harness),'oracle_sha256':b.sha(rules_path.read_bytes()),'protected_access':False,'m1_qualified':False}
    b.write(output/'contract.json',contract)
    report={'schema':contract['schema'],'contract_sha256':b.sha(b.encoded(contract)),'status':'running','rows':[],'candidate_executions':0,'m1_qualified':False,'protected_access':False}
    started=time.monotonic()
    try:
        for pid,data in loaded.items():
            if data['metadata']['transport']!='standard':raise ValueError('only paired JSON candidates supported')
            cases=json.loads(data['cases']);baseline=json.loads(data['baseline'])
            row={'id':pid,'adapted_sha256':b.sha(sources[pid]),'cases':len(cases),'checks_passed':0,'passed':False,'failures':[],'calls':[]};report['rows'].append(row)
            for offset in range(0,len(cases),32):
                if time.monotonic()-started>max_wall:raise TimeoutError('adapted qualification wall budget exhausted')
                batch=cases[offset:offset+32]
                payload={'entry':'solve','calls':[{'args':c['args']} for c in batch]}
                res=b.pinned_runtime.run_node(node_path,manifest=runtime,files={'program.js':sources[pid],'harness.cjs':harness,'inputs.json':b.encoded(payload)},limits=b.sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2),node_args=['--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'])
                report['candidate_executions']+=1;stem=f'{pid}-{offset}';(output/(stem+'.stdout')).write_bytes(res.stdout);(output/(stem+'.stderr')).write_bytes(res.stderr)
                row['calls'].append({'stem':stem,'stdout_sha256':b.sha(res.stdout),'stderr_sha256':b.sha(res.stderr),'exit_code':res.exit_code,'timed_out':res.timed_out})
                try:
                    if not res.ok:raise RuntimeError('isolated process failure')
                    records=b.parse(res.stdout,len(batch))
                    for i,(case,record) in enumerate(zip(batch,records)):
                        valid,observed=rules.judge_case(case,record);parity=b.exact(observed,baseline[offset+i]);row['checks_passed']+=int(valid and parity)
                        if not valid or not parity:row['failures'].append({'case_index':offset+i,'oracle':valid,'historical_parity':parity})
                except Exception as error:row['failures'].append({'offset':offset,'error':type(error).__name__+': '+str(error)})
            row['passed']=row['checks_passed']==len(cases) and not row['failures'];b.write(output/'report.json',report)
        report['status']='completed'
    except Exception as error:report['status']='failed';report['error']=type(error).__name__+': '+str(error)
    finally:
        report['elapsed_seconds']=time.monotonic()-started;b.write(output/'report.json',report)
    # This is a proposed pool manifest; consumer must replay qualification before fit.
    b.write(output/'fit-pool.json',{'schema':'gamma.adapted-fit-pool.v1','original_control':'all frozen permitted400 sources remain unchanged','qualification_report_sha256':b.sha((output/'report.json').read_bytes()),'qualification_contract_sha256':report['contract_sha256'],'alternatives':[s for s in source_rows if next(r for r in report['rows'] if r['id']==s['id'])['passed']] if report['status']=='completed' else [],'requires_independent_evidence_replay':True,'protected_access':False,'m1_qualified':False})
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--node-path',type=Path,required=True);p.add_argument('--evidence',type=Path);p.add_argument('--candidate-ids');p.add_argument('--max-wall',type=int,default=600);a=p.parse_args()
    report=run(a.inputs,a.output,a.node_path,json.loads(a.evidence.read_text()) if a.evidence else [],a.max_wall,[] if not a.candidate_ids else [int(x) for x in a.candidate_ids.split(',')])
    print(json.dumps({'status':report['status'],'passed':sum(r['passed'] for r in report['rows']),'problems':len(report['rows']),'executions':report['candidate_executions']}))
