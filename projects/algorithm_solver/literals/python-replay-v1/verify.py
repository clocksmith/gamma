"""Recompute Python eligibility from every hash-bound raw output, never flags."""
import argparse,json,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('python_replay_qualification',HERE/'qualify.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)

def verify(inputs,report_path):
    raw=report_path.read_bytes();r=json.loads(raw);cr=(report_path.parent/'contract.json').read_bytes();c=json.loads(cr)
    if r.get('contract_sha256')!=q.sha(cr) or r.get('status')!='completed' or r.get('schema')!='gamma.python.runtime-replay.v1' or r.get('protected_access') is not False or r.get('m1_qualified') is not False:raise ValueError('report status/identity/scope invalid')
    if c.get('schema')!=r['schema'] or c.get('code_sha256')!=q.pins() or c.get('python_runtime_sha256')!=q.sha(Path('/usr/bin/python3').read_bytes()) or c.get('protected_access') is not False or c.get('m1_qualified') is not False or c.get('batch_cases')!=32 or c.get('limits')!={'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1024**3,'max_output_bytes':4*1024**2}:raise ValueError('runtime/code/limits drift')
    sc,sources=q.load_freeze(Path(c['source_freeze']))
    if c['source_freeze_sha256']!=q.sha(q.encoded(sc)) or c['ids']!=sc['ids']:raise ValueError('source identity mismatch')
    loaded,hashes,mhash=q.b.load_inputs(inputs,c['ids'])
    if c['input_hashes']!=hashes or c['input_manifest_sha256']!=mhash:raise ValueError('input identity drift')
    if [row.get('id') for row in r['rows']]!=list(loaded):raise ValueError('incomplete population')
    eligible=[];failed=[];blocked=[];checks=executions=0
    for row,(pid,data) in zip(r['rows'],loaded.items()):
        cases=json.loads(data['cases']);base=json.loads(data['baseline'])
        if row['cases']!=len(cases) or len(cases)!=len(base):raise ValueError('case denominator mismatch')
        if pid in q.BLOCKED:
            if row.get('blocked')!='unresolved alternative-domain contract' or row.get('calls')!=[] or row.get('checks_passed')!=0 or row.get('passed') is not False or row.get('failures')!=[]:raise ValueError('blocked row drift')
            blocked.append(pid);continue
        if row.get('blocked'):raise ValueError('unexpected blocker')
        offsets=list(range(0,len(cases),32))
        if len(offsets)!=len(row['calls']):raise ValueError('incomplete execution coverage')
        count=0;failures=[]
        for off,call in zip(offsets,row['calls']):
            stem=f'{pid}-{off}'
            if call['stem']!=stem or type(call['exit_code']) is not int or type(call['timed_out']) is not bool or type(call['output_limit_exceeded']) is not bool:raise ValueError('invalid execution metadata')
            stdout=(report_path.parent/(stem+'.stdout')).read_bytes();stderr=(report_path.parent/(stem+'.stderr')).read_bytes()
            if q.sha(stdout)!=call['stdout_sha256'] or q.sha(stderr)!=call['stderr_sha256']:raise ValueError('observation drift')
            n,f=q.check_batch(cases[off:off+32],base[off:off+32],call,stdout,off);count+=n;failures.extend(f);executions+=1
        passed=count==len(cases) and not failures
        if row['checks_passed']!=count or row['failures']!=failures or row['passed'] is not passed:raise ValueError('independent replay differs')
        checks+=count;(eligible if passed else failed).append(pid)
    if r['qualified']!=len(eligible) or r['checks_passed']!=checks or r['candidate_executions']!=executions:raise ValueError('aggregate mismatch')
    return {'schema':'gamma.python.independent-verification.v1','verified':True,'eligible_ids':eligible,'failed_ids':failed,'blocked_ids':blocked,'programs':len(loaded),'qualified':len(eligible),'checks':checks,'executions':executions,'report_sha256':q.sha(raw),'m1_population':500,'m1_qualified':False,'protected_access':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();print(json.dumps(verify(a.inputs,a.report),sort_keys=True))
