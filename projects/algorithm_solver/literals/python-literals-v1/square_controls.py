"""Independent finite small-domain and algebraic controls; native sandbox only."""
import argparse,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'paired-authoring-v1'))
import baseline_replay as b

def cases():
    representable={a*a+c*c for a in range(33) for c in range(33)}
    rows=[(n,n in representable) for n in range(1024)]
    rows.extend((n*n,True) for n in (2**20+1,2**30-1,2**32-1))
    rows.extend((3*(2**power)**2,False) for power in range(1,31))
    return rows

def run(output):
    if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private output required')
    source=LIT/'paired-authoring-v1/python/0633.py';raw=source.read_bytes();harness=LIT/'python-replay-v1/harness.py'
    tests=cases();output.mkdir(parents=True,exist_ok=False)
    identity={'schema':'gamma.python.square-sum-controls.v1','source_sha256':b.sha(raw),'harness_sha256':b.sha(harness.read_bytes()),'runner_sha256':b.sha(Path(__file__).read_bytes()),'sandbox_sha256':b.sha(Path(b.sandbox.__file__).read_bytes()),'python_runtime_sha256':b.sha(Path('/usr/bin/python3').read_bytes()),'checks':len(tests),'input_expected_sha256':b.sha(b.encoded(tests)),'frozen_cases_opened':False,'m1_qualified':False}
    b.write(output/'contract.json',identity);passed=0;calls=[];failures=[];start=time.monotonic()
    for offset in range(0,len(tests),32):
        if time.monotonic()-start>300:raise TimeoutError('bounded controls wall timeout')
        batch=tests[offset:offset+32]
        result=b.sandbox.run(['/usr/bin/python3','-I','-S','harness.py'],files={'program.py':raw,'harness.py':harness.read_bytes(),'inputs.json':b.encoded({'method':'judgeSquareSum','calls':[{'args':[n]} for n,_ in batch]})},limits=b.sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2))
        stem=str(offset);(output/(stem+'.stdout')).write_bytes(result.stdout);(output/(stem+'.stderr')).write_bytes(result.stderr)
        calls.append({'offset':offset,'exit_code':result.exit_code,'timed_out':result.timed_out,'stdout_sha256':b.sha(result.stdout),'stderr_sha256':b.sha(result.stderr)})
        if not result.ok:failures.append({'offset':offset,'process_failed':True});continue
        for i,(record,(n,expected)) in enumerate(zip(b.parse(result.stdout,len(batch)),batch)):
            good=(record.get('result') is expected and record.get('result_type')=='bool' and b.exact(record.get('args_before'),b.tag([n])) and b.exact(record.get('args_after'),b.tag([n])) and record.get('alias_edges')==[] and not record.get('error'))
            passed+=int(good)
            if not good:failures.append({'index':offset+i})
    report={'contract_sha256':b.sha(b.encoded(identity)),'passed':passed==len(tests) and not failures,'checks_passed':passed,'checks':len(tests),'executions':len(calls),'calls':calls,'failures':failures,'m1_qualified':False}
    b.write(output/'report.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run(a.output);print(json.dumps({k:r[k] for k in ('passed','checks_passed','checks','executions')}));raise SystemExit(0 if r['passed'] else 2)
