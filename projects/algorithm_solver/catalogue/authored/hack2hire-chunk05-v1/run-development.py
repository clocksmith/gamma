"""Actual bounded local executions against the author-frozen references, not a judge."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import importlib.util
import json
import platform
import resource
import subprocess
import sys
import tempfile
import time
from cases import build_cases

HERE = Path(__file__).resolve().parent
MAX_SAFE = 2**53-1


def wire(value):
    if type(value) is int and abs(value) > MAX_SAFE:
        return str(value)
    if isinstance(value, list):
        return [wire(v) for v in value]
    if isinstance(value, dict):
        return {k: wire(v) for k, v in value.items()}
    return value


def main():
    frozen = json.loads((HERE/'pre-source-reference-freeze.json').read_text())
    for name, digest in frozen['files'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == digest, 'Frozen source changed: '+name
    rows = json.loads((HERE/'contracts.json').read_text())['problems']
    report = {'schema':'gamma.author-local-development.v1','started_at':datetime.now(timezone.utc).isoformat(),'qualification_status':'unknown','independent_qualification':0,'scope':'Author-local executions against author-frozen inferred practice contracts; no protected cases, official-variant confirmation or independent judge','python':platform.python_version(),'results':[],'blocked':[{k:row[k] for k in ('uid','title','reason')} for row in rows if row['key'] is None]}
    cache = {}
    try:
        with tempfile.TemporaryDirectory(prefix='gamma-chunk05-') as td:
            for row in rows:
                key, variant = row['key'], row['variant_id']
                if key is None:
                    continue
                if key not in cache:
                    cache[key] = build_cases(key)
                cases = cache[key]
                source = HERE/'python'/f'{variant}.py'
                spec = importlib.util.spec_from_file_location('chunk05_'+variant, source)
                module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
                max_seconds = 0
                for index, case in enumerate(cases):
                    args = copy.deepcopy(case['args']); before = copy.deepcopy(args); start = time.perf_counter()
                    actual = module.solve(*args)
                    elapsed = time.perf_counter()-start; max_seconds = max(max_seconds, elapsed)
                    if wire(actual) != wire(case['expected']) or args != before:
                        raise AssertionError({'variant':variant,'language':'python','case':index,'args':case['args'],'actual':wire(actual),'expected':wire(case['expected']),'input_mutation':args != before})
                    assert elapsed < 1, ('python case exceeded one second', variant, index, elapsed)
                if row['inferred_interface']['kind'] == 'function':
                    native = getattr(module,row['inferred_interface']['name'])
                    assert wire(native(*copy.deepcopy(cases[0]['args']))) == wire(cases[0]['expected'])
                    alias = getattr(module.Solution(),row['inferred_interface']['name'])
                    assert wire(alias(*copy.deepcopy(cases[0]['args']))) == wire(cases[0]['expected'])
                else:
                    assert hasattr(module,row['inferred_interface']['classname'])
                rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                rss_bytes = rss if sys.platform == 'darwin' else rss*1024
                assert rss_bytes < 1024**3
                packet = Path(td)/(key+'.json'); packet.write_text(json.dumps(wire(cases),ensure_ascii=False))
                js_source = HERE/'javascript'/f'{variant}.js'
                process = subprocess.run(['node','--jitless','--max-old-space-size=512',str(HERE/'run-javascript.cjs'),str(js_source),str(packet),json.dumps(row['inferred_interface'])],capture_output=True,text=True,timeout=30)
                if process.returncode:
                    raise AssertionError({'variant':variant,'language':'javascript','returncode':process.returncode,'output':process.stdout[-3500:],'stderr':process.stderr[-700:]})
                js = json.loads(process.stdout)
                report['results'].append({'id':row['uid'],'key':key,'python_cases':len(cases),'javascript_cases':js['cases'],'python_max_case_seconds':max_seconds,'python_peak_rss_bytes':rss_bytes,'javascript':js,'source_hashes':{'python':hashlib.sha256(source.read_bytes()).hexdigest(),'javascript':hashlib.sha256(js_source.read_bytes()).hexdigest()}})
                print(variant,key,len(cases),'per language',flush=True)
    except Exception as error:
        report['passed'] = False; report['failure'] = str(error); report['finished_at'] = datetime.now(timezone.utc).isoformat()
        failure = HERE/('checks-failed-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json')
        failure.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        print(report['failure'],file=sys.stderr)
        raise
    report.update(passed=True,finished_at=datetime.now(timezone.utc).isoformat(),completed_pairs=len(report['results']),cases_per_language=sum(row['python_cases'] for row in report['results']),native_wrappers_checked=True)
    (HERE/'checks.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:report[k] for k in ('passed','completed_pairs','cases_per_language','qualification_status')}))


if __name__ == '__main__':
    main()
