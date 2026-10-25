"""Independent host-only gate for fully charged adapted source alternatives."""
import argparse
import json
from pathlib import Path
import re
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import adapted_candidates as adapted
b=adapted.b


def verify(inputs,report_path):
    report_raw=report_path.read_bytes();report=json.loads(report_raw)
    contract_raw=(report_path.parent/'contract.json').read_bytes();contract=json.loads(contract_raw)
    if report.get('contract_sha256')!=b.sha(contract_raw) or report.get('status')!='completed':raise ValueError('incomplete adapted qualification')
    if contract.get('schema')!='gamma.adapted-paired-qualification.v1' or contract.get('protected_access') is not False or contract.get('batch_cases')!=32:raise ValueError('adapted scope changed')
    if contract.get('code_sha256')!=b.sha(Path(adapted.__file__).read_bytes()) or contract.get('baseline_loader_sha256')!=b.sha(Path(b.__file__).read_bytes()) or contract.get('paired_verifier_sha256')!=b.sha(Path(adapted.paired.__file__).read_bytes()):raise ValueError('adapted runner identity drift')
    b.pinned_runtime.validate_manifest(contract['runtime'])
    loaded,hashes,manifest=b.load_inputs(inputs,contract['ids'])
    # Additional dev-fit gate: baseline loader alone also permits consumed dev-val.
    adapted.paired.inputs(inputs,contract['ids'])
    if hashes!=contract.get('input_hashes') or manifest!=contract.get('input_manifest_sha256'):raise ValueError('adapted input identity drift')
    pinned=json.loads((b.LIT/'name-search-v1/contract.json').read_text())['code_hashes']
    for name,key in [('harness.cjs','harness_sha256'),('qualify_rules.py','oracle_sha256')]:
        if contract.get(key)!=pinned['admission500-v1/'+name] or contract[key]!=b.sha((b.LIT/'admission500-v1'/name).read_bytes()):raise ValueError('historical adapter oracle drift')
    rules=b.module('adapted_replay_rules',b.LIT/'admission500-v1/qualify_rules.py')
    sources=contract['sources'];rows=report['rows']
    if [r['id'] for r in sources]!=list(loaded) or [r['id'] for r in rows]!=list(loaded):raise ValueError('adapted source population mismatch')
    qualified=[];failed=[];executions=0;checks=0
    for source,row,(pid,data) in zip(sources,rows,loaded.items()):
        if source.get('path')!=f'{pid}.js':raise ValueError('noncanonical adapted source path')
        complete=(report_path.parent/source['path']).read_bytes();size=source['candidate_bytes'];suffix=complete[size:]
        if (len(complete)!=source.get('complete_bytes') or len(suffix)!=source.get('adapter_bytes') or
            b.sha(complete)!=source.get('adapted_sha256') or b.sha(complete[:size])!=source.get('candidate_sha256') or b.sha(suffix)!=source.get('adapter_sha256') or
            not re.fullmatch(rb'\nfunction solve\(\.\.\.args\)\{return new Solution\(\)\.[A-Za-z_$][A-Za-z0-9_$]*\(\.\.\.args\);\}\n',suffix)):raise ValueError('complete source or charged adapter mismatch')
        if row.get('adapted_sha256')!=source['adapted_sha256']:raise ValueError('qualified bytes mismatch')
        cases=json.loads(data['cases']);base=json.loads(data['baseline']);offsets=list(range(0,len(cases),32));failures=[];passed_checks=0
        if len(row['calls'])!=len(offsets) or row.get('cases')!=len(cases):raise ValueError('incomplete adapted executions')
        for offset,call in zip(offsets,row['calls']):
            stem=f'{pid}-{offset}'
            if call.get('stem')!=stem or type(call.get('exit_code')) is not int or type(call.get('timed_out')) is not bool:raise ValueError('invalid adapted execution metadata')
            stdout=(report_path.parent/(stem+'.stdout')).read_bytes();stderr=(report_path.parent/(stem+'.stderr')).read_bytes()
            if b.sha(stdout)!=call.get('stdout_sha256') or b.sha(stderr)!=call.get('stderr_sha256'):raise ValueError('adapted observation digest mismatch')
            try:
                if call['exit_code']!=0 or call['timed_out']:raise RuntimeError('isolated process failure')
                batch=cases[offset:offset+32];records=b.parse(stdout,len(batch))
                for i,(case,record) in enumerate(zip(batch,records)):
                    valid,observed=rules.judge_case(case,record);parity=b.exact(observed,base[offset+i]);passed_checks+=int(valid and parity)
                    if not valid or not parity:failures.append({'case_index':offset+i,'oracle':valid,'historical_parity':parity})
            except Exception as error:failures.append({'offset':offset,'error':type(error).__name__+': '+str(error)})
            executions+=1
        passed=passed_checks==len(cases) and not failures
        if row.get('checks_passed')!=passed_checks or row.get('passed') is not passed or row.get('failures')!=failures:raise ValueError('adapted independent replay disagrees')
        checks+=passed_checks
        if passed:qualified.append(source)
        else:failed.append(pid)
    if report.get('candidate_executions')!=executions:raise ValueError('adapted execution aggregate mismatch')
    pool=json.loads((report_path.parent/'fit-pool.json').read_text())
    if pool.get('qualification_report_sha256')!=b.sha(report_raw) or pool.get('qualification_contract_sha256')!=b.sha(contract_raw) or pool.get('alternatives')!=qualified:raise ValueError('adapted pool not bound to verified qualification')
    return {'verified':True,'alternatives':qualified,'failed_ids':failed,'problems':len(loaded),'checks_passed':checks,'executions':executions,'report_sha256':b.sha(report_raw),'m1_qualified':False,'protected_access':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();print(json.dumps(verify(a.inputs,a.report),sort_keys=True))
