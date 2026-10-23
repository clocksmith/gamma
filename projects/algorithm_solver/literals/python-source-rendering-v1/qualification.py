"""Fresh strict item31 observations, with replayable per-batch exit receipts."""
import json
from pathlib import Path
import sys
from common import LIT,sha,write,finite_seconds
sys.path.insert(0,str(LIT.parent))
from algsolve.judge import sandbox
from algsolve.judge.judge import FunctionalTest,_matches

def strict(pairs):
    out={}
    for key,value in pairs:
        if key in out:raise ValueError('duplicate JSON key')
        out[key]=value
    return out

def parse(data,n):
    rows=[json.loads(line,object_pairs_hook=strict,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON'))) for line in data.splitlines()]
    assert len(rows)==n+1 and rows[-1]=={'done':n}
    assert all(type(row.get('i')) is int and row['i']==i for i,row in enumerate(rows[:-1]))
    return [{k:v for k,v in row.items() if k!='i'} for row in rows[:-1]]

def inputs(spec):
    raw=Path(spec['tests_file']).read_bytes();assert sha(raw)==spec['tests_sha256']
    tests=json.loads(raw);base=[]
    for call in spec['baseline_calls']:
        raw=Path(call['file']).read_bytes();assert sha(raw)==call['sha256']
        base.extend(parse(raw,call['cases']))
    assert len(base)==len(tests)==spec['cases']
    return tests,base

def observations(tests,base,raw,ok,offset):
    failures=[];passed=0
    try:
        assert ok,'sandbox process failed'
        rows=parse(raw,len(tests))
        for i,(test,row) in enumerate(zip(tests,rows)):
            valid=not row['error'] and _matches(FunctionalTest(args=test['args'],expected=test['expected'],compare=test.get('compare','return')),
                                               {'result':row['result'],'args':row['args_after']})
            same=json.dumps(row,sort_keys=True)==json.dumps(base[i],sort_keys=True)
            passed+=bool(valid and same)
            if not valid or not same:failures.append({'case':offset+i,'oracle':bool(valid),'parity':same})
    except (AssertionError,ValueError,KeyError,TypeError) as error:
        failures.append({'offset':offset,'reason_type':type(error).__name__})
    return passed,failures

def finish(spec,source,batches,passed,failures):
    return {'id':str(spec['id']),'source_sha256':sha(source.encode()),'tests_sha256':spec['tests_sha256'],
            'cases':spec['cases'],'checks_passed':passed,'passed':passed==spec['cases'] and not failures,
            'batches':batches,'failures':failures}

def qualify_one(job,c):
    spec,text,folder=job['spec'],job['source'],Path(job['folder']);folder.mkdir(parents=True)
    tests,base=inputs(spec);passed=0;failures=[];batches=[];limits=c['limits']
    for offset in range(0,len(tests),limits['qualification_batch_cases']):
        batch=tests[offset:offset+limits['qualification_batch_cases']]
        result=sandbox.run([c['python_bin'],'harness.py'],files={'harness.py':(LIT/'python-name-v1/harness.py').read_bytes(),
            'candidate.py':text,'inputs.json':json.dumps({'entry':spec['entry'],'calls':[{'args':t['args']} for t in batch]})},
            limits=sandbox.Limits(cpu_seconds=limits['qualification_cpu_seconds'],wall_seconds=limits['qualification_wall_seconds'],
                memory_bytes=limits['qualification_memory_bytes'],max_output_bytes=limits['qualification_output_bytes']))
        (folder/f'{offset}.stdout').write_bytes(result.stdout);(folder/f'{offset}.stderr').write_bytes(result.stderr)
        record={'offset':offset,'cases':len(batch),'ok':result.ok,'exit_code':result.exit_code,'timed_out':result.timed_out,
                'output_limit_exceeded':result.output_limit_exceeded,
                'wall_seconds':result.wall_seconds,
                'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr)}
        batches.append(record)
        n,bad=observations(batch,base[offset:offset+len(batch)],result.stdout,result.ok,offset)
        passed+=n;failures.extend(bad)
        write(folder/'progress.json',finish(spec,text,batches,passed,failures))
    receipt=finish(spec,text,batches,passed,failures);write(folder/'receipt.json',receipt)
    return receipt

def replay(folder,spec,source,c):
    """Read the exact consumed cases and observations; do not execute a candidate."""
    receipt=json.loads((folder/'receipt.json').read_text());tests,base=inputs(spec)
    passed=0;failures=[];batches=receipt['batches'];size=c['limits']['qualification_batch_cases']
    assert len(batches)==(len(tests)+size-1)//size
    for record,offset in zip(batches,range(0,len(tests),size)):
        batch=tests[offset:offset+size]
        assert record['offset']==offset and record['cases']==len(batch)
        finite_seconds(record['wall_seconds'],c['limits']['qualification_seconds']+c['timing_receipt_tolerance_seconds'])
        assert all(type(record[key]) is bool for key in ('ok','timed_out','output_limit_exceeded'))
        raw=(folder/f'{offset}.stdout').read_bytes();err=(folder/f'{offset}.stderr').read_bytes()
        assert sha(raw)==record['stdout_sha256'] and sha(err)==record['stderr_sha256']
        assert record['ok']==(record['exit_code']==0 and not record['timed_out'] and not record['output_limit_exceeded'])
        n,bad=observations(batch,base[offset:offset+len(batch)],raw,record['ok'],offset)
        passed+=n;failures.extend(bad)
    expected=finish(spec,source,batches,passed,failures);assert receipt==expected
    return expected
