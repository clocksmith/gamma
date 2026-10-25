"""Independently replay a baseline400 receipt before representation fitting.

Reads only the hash-bound permitted inputs and retained observations; never runs
candidate code. A summary's pass flags alone cannot authorize a dictionary fit.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
_spec=importlib.util.spec_from_file_location('gamma_direct_entry_qualify',HERE/'qualify.py');replay=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(replay)


def verify(inputs,report_path,required_ids=None,allow_failed=True,node_path=None):
    raw=report_path.read_bytes();report=json.loads(raw)
    contract_raw=(report_path.parent/'contract.json').read_bytes();contract=json.loads(contract_raw)
    if report.get('contract_sha256')!=replay.sha(contract_raw):raise ValueError('contract digest mismatch')
    if report.get('status')!='completed' or report.get('m1_qualified') is not False or report.get('protected_access') is not False:raise ValueError('invalid replay status/scope')
    if contract.get('schema')!='gamma.compact-variants.runtime-replay.v1' or contract.get('baseline_loader_sha256')!=replay.sha(Path(replay.b.__file__).read_bytes()) or contract.get('supply_code_sha256')!=replay.supply.pins():raise ValueError('supply/loader identity drift')
    supply_contract,sources=replay.supply.load(inputs,Path(contract['prepared']),node_path,regenerate=True)
    if contract.get('supply_contract_sha256')!=replay.sha(replay.encoded(supply_contract)) or contract.get('sources')!=supply_contract['sources'] or contract.get('cohort')!=163 or contract.get('unsupported')!=supply_contract['unsupported']:raise ValueError('source supply evidence drift')
    for pid,source in sources.items():
        if (report_path.parent/f'{pid}.js').read_bytes()!=source:raise ValueError('qualified source bytes drift')
    loaded,hashes,input_manifest=replay.load_inputs(inputs,list(sources))
    if contract.get('ids')!=list(loaded) or contract.get('input_hashes')!=hashes or contract.get('input_manifest_sha256')!=input_manifest:raise ValueError('input population/identity mismatch')
    if (contract.get('runner_sha256')!=replay.sha(Path(replay.__file__).read_bytes()) or
        contract.get('host_judge_sha256')!=replay.sha(Path(replay.host_judge.__file__).read_bytes()) or
        contract.get('sandbox_sha256')!=replay.sha(Path(replay.sandbox.__file__).read_bytes()) or
        contract.get('runtime_adapter_sha256')!=replay.sha(Path(replay.pinned_runtime.__file__).read_bytes()) or
        contract.get('batch_cases')!=32 or contract.get('protected_access') is not False):raise ValueError('runner/oracle/sandbox contract drift')
    replay.pinned_runtime.validate_manifest(contract['runtime'])
    historical=json.loads((replay.LIT/'name-search-v1/contract.json').read_text())['code_hashes']
    for name,digest in contract['historical_code_sha256'].items():
        if name not in ('harness.cjs','harness-exact-integer.cjs','qualify_rules.py'):raise ValueError('unexpected historical code')
        if digest!=historical['admission500-v1/'+name] or replay.sha((replay.LIT/'admission500-v1'/name).read_bytes())!=digest:raise ValueError('historical code drift')
    if set(contract['historical_code_sha256'])!={'harness.cjs','harness-exact-integer.cjs','qualify_rules.py'}:raise ValueError('incomplete historical code')
    rules=replay.module('baseline_verification_rules',replay.LIT/'admission500-v1/qualify_rules.py')
    rows=report.get('rows',[])
    if len(rows)!=len(loaded) or [row.get('id') for row in rows]!=list(loaded):raise ValueError('incomplete/duplicate result population')
    checks=executions=0
    eligible=[];failed=[]
    for row,(pid,data) in zip(rows,loaded.items()):
        cases=json.loads(data['cases']);baseline=json.loads(data['baseline'])
        if len(cases)!=len(baseline) or row.get('cases')!=len(cases):raise ValueError('incomplete row case coverage')
        offsets=list(range(0,len(cases),32))
        if len(row['calls'])!=len(offsets):raise ValueError('incomplete executions')
        row_checks=0;failures=[]
        for offset,call in zip(offsets,row['calls']):
            stem=f'{pid}-{offset}'
            if call.get('stem')!=stem or type(call.get('exit_code')) is not int or type(call.get('timed_out')) is not bool:raise ValueError('invalid execution metadata')
            stdout=(report_path.parent/(stem+'.stdout')).read_bytes();stderr=(report_path.parent/(stem+'.stderr')).read_bytes()
            if replay.sha(stdout)!=call.get('stdout_sha256') or replay.sha(stderr)!=call.get('stderr_sha256'):raise ValueError('observation digest mismatch')
            batch=cases[offset:offset+32]
            try:
                if call['exit_code']!=0 or call['timed_out']:raise RuntimeError('sandbox process failed')
                records=replay.parse(stdout,len(batch))
                for i,(case,record) in enumerate(zip(batch,records)):
                    valid,observed=rules.judge_case(case,record);parity=replay.exact(observed,baseline[offset+i])
                    row_checks+=int(valid and parity)
                    if not valid or not parity:failures.append({'case_index':offset+i,'oracle':valid,'historical_effect_type_parity':parity,'error':record.get('error')})
            except Exception as error:failures.append({'offset':offset,'execution_or_protocol':type(error).__name__+': '+str(error)})
            executions+=1
        passed=row_checks==len(cases) and not failures
        if row.get('checks_passed')!=row_checks or row.get('passed') is not passed or row.get('failures')!=failures:raise ValueError('independent oracle/parity replay differs from receipt')
        checks+=row_checks
        (eligible if passed else failed).append(pid)
    if report.get('qualified')!=len(eligible) or report.get('candidate_executions')!=executions or report.get('checks_passed')!=checks or report.get('cases')!=sum(len(json.loads(d['cases'])) for d in loaded.values()):raise ValueError('aggregate coverage mismatch')
    if failed and not allow_failed:raise ValueError('complete replay retains failed problems; no full-pass qualification')
    return {'verified':True,'cohort':163,'unsupported_ids':sorted(map(int,supply_contract['unsupported'])),'problems':len(loaded),'qualified':len(eligible),'eligible_ids':eligible,'failed_ids':failed,'checks':checks,'executions':executions,'report_sha256':replay.sha(raw),'m1_qualified':False,'protected_access':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--ids');p.add_argument('--allow-failed',action='store_true');p.add_argument('--parser-node',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(a.inputs,a.report,None if a.ids is None else [int(x) for x in a.ids.split(',')],a.allow_failed,a.parser_node),sort_keys=True))
