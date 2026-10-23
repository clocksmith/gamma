"""Pinned item6 observation protocol, with explicit case hash verification."""
import json
from pathlib import Path
import sys
from backend import HERE,LIT,analyze
sys.path.insert(0,str(LIT.parent))
from algsolve.judge import sandbox
from algsolve.judge.judge import FunctionalTest,_matches

def strict(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('duplicate key')
        out[k]=v
    return out


def parse(data,n):
    rows=[json.loads(line,object_pairs_hook=strict,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))) for line in data.splitlines()]
    assert len(rows)==n+1 and rows[-1]=={'done':n}
    assert all(type(r.get('i')) is int and r['i']==i for i,r in enumerate(rows[:-1]))
    return [{k:v for k,v in r.items() if k!='i'} for r in rows[:-1]]


def qualify_one(job):
    spec,text,folder=job['spec'],job['source'],Path(job['folder']);folder.mkdir(parents=True)
    raw_tests=Path(spec['tests_file']).read_bytes()
    assert analyze.sha(raw_tests)==spec['tests_sha256']
    tests=json.loads(raw_tests);base=[]
    for call in spec['baseline_calls']:
        raw=Path(call['file']).read_bytes();assert analyze.sha(raw)==call['sha256']
        base.extend(parse(raw,call['cases']))
    assert len(base)==len(tests)==spec['cases'];passed=0;failures=[]
    for off in range(0,len(tests),32):
        batch=tests[off:off+32]
        res=sandbox.run(['/usr/bin/python3','harness.py'],files={'harness.py':(LIT/'python-name-v1/harness.py').read_bytes(),'candidate.py':text,
            'inputs.json':json.dumps({'entry':spec['entry'],'calls':[{'args':t['args']} for t in batch]})},
            limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=512*1024**2,max_output_bytes=4*1024**2))
        (folder/f'{off}.stdout').write_bytes(res.stdout);(folder/f'{off}.stderr').write_bytes(res.stderr)
        try:
            assert res.ok,f'sandbox exit={res.exit_code}, timeout={res.timed_out}'
            observations=parse(res.stdout,len(batch))
            for j,(test,o) in enumerate(zip(batch,observations)):
                valid=not o['error'] and _matches(FunctionalTest(args=test['args'],expected=test['expected'],compare=test.get('compare','return')),
                                               {'result':o['result'],'args':o['args_after']})
                same=json.dumps(o,sort_keys=True)==json.dumps(base[off+j],sort_keys=True)
                passed+=bool(valid and same)
                if not valid or not same:failures.append({'case':off+j,'oracle':bool(valid),'parity':same})
        except Exception as e:failures.append({'offset':off,'reason':str(e)})
    return {'passed':passed==len(tests) and not failures,'checks_passed':passed,'cases':len(tests),'failures':failures}
