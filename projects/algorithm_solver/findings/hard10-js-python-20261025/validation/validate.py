"""Replay the supplied, deterministic local corpus in JS and Python.

Run: python validation/validate.py
This is a local validation harness, NOT Gamma's bubblewrap judge. Candidate
workers receive only IDs and positional inputs; host-side code owns the oracle.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
ATTEMPT='attempt-001'
ARTIFACTS=ROOT/'validation'/ATTEMPT
if ARTIFACTS.exists():
    suffix=2
    while (ROOT/'validation'/f'attempt-{suffix:03}').exists():
        suffix+=1
    ATTEMPT=f'attempt-{suffix:03}'
    ARTIFACTS=ROOT/'validation'/ATTEMPT
ARTIFACTS.mkdir(parents=True)
assignment=json.loads((ROOT/'assignment.json').read_text())
node=shutil.which('node')
if not node:
    raise SystemExit('Node.js is required; no automatic installation is performed.')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(command,**kwargs):
    return subprocess.run(command,text=True,capture_output=True,timeout=90,**kwargs)

report={
 'schema':'chatgpt.gamma-local-candidate-validation.v1','attempt':ATTEMPT,
 'gamma_qualification':False,'gamma_independent_tests_executed':0,
 'protected_test_access':False,'training':False,'repository_writes':False,
 'oracle_status':'Self-authored separate reference algorithms and closed-form stress expectations; not an external independent Gamma verifier.',
 'environment':{'python':sys.version,'node':run([node,'--version']).stdout.strip(),
                'platform':platform.platform(),'python_executable_sha256':sha(sys.executable),
                'node_executable_sha256':sha(node),'node_flags':[],
                'isolation':'Separate ordinary local processes; NOT Gamma pinned Linux/bubblewrap isolation.'},
 'syntax':[],'problems':[],'failures':[],
}
for problem in assignment['problems']:
    stem=f"{problem['id']:04}"
    for language,source,command in (
      ('javascript',ROOT/'javascript'/f'{stem}.js',[node,'--check',str(ROOT/'javascript'/f'{stem}.js')]),
      ('python',ROOT/'python'/f'{stem}.py',[sys.executable,'-m','py_compile',str(ROOT/'python'/f'{stem}.py')])):
        check=run(command)
        row={'problem_id':problem['id'],'language':language,'source_sha256':sha(source),
             'passed':check.returncode==0,'stdout':check.stdout,'stderr':check.stderr}
        report['syntax'].append(row)
        if check.returncode:
            report['failures'].append({'stage':'syntax',**row})

if report['failures']:
    (ARTIFACTS/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit('Syntax check failed; retained report, no test outputs fabricated.')

for problem in assignment['problems']:
    pid=problem['id']; stem=f'{pid:04}'
    case_path=ROOT/'validation'/'cases'/f'{stem}.jsonl'
    cases=[json.loads(line) for line in case_path.read_text().splitlines()]
    # Only inputs travel into the worker. Never send expected values.
    payload=''.join(json.dumps({'case_id':case['case_id'],'args':case['args']},separators=(',',':'))+'\n' for case in cases)
    outputs={}; runtimes={}
    for language,command in (
      ('javascript',[node,str(ROOT/'validation'/'run_javascript.cjs'),str(pid)]),
      ('python',[sys.executable,str(ROOT/'validation'/'run_python.py'),str(pid)])):
        started=time.perf_counter()
        result=run(command,input=payload)
        runtimes[language]=time.perf_counter()-started
        (ARTIFACTS/f'{stem}-{language}.jsonl').write_text(result.stdout)
        (ARTIFACTS/f'{stem}-{language}.stderr.txt').write_text(result.stderr)
        if result.returncode:
            report['failures'].append({'problem_id':pid,'language':language,
              'stage':'worker','exit_code':result.returncode,'stderr':result.stderr})
        try:
            rows=[json.loads(line) for line in result.stdout.splitlines()]
            if len(rows)!=len(cases) or [row['case_id'] for row in rows]!=[case['case_id'] for case in cases]:
                raise ValueError('worker result identity/count mismatch')
            outputs[language]=rows
        except Exception as error:
            report['failures'].append({'problem_id':pid,'language':language,'stage':'result_parse','error':str(error)})
            outputs[language]=[]
    good=0; mutation_checks=0; cross_language=0
    for index,case in enumerate(cases):
        accepted=True
        expected=case['expected']
        wanted_py=type(expected).__name__
        wanted_js={'bool':'boolean','int':'number','str':'string'}[wanted_py]
        for language,expected_type in [('javascript',wanted_js),('python',wanted_py)]:
            if len(outputs[language])!=len(cases):
                accepted=False
                continue
            row=outputs[language][index]
            for entrypoint in ('solve','native'):
                result=row['results'][entrypoint]
                correct=(result.get('ok') and result.get('type')==expected_type and
                         result.get('value')==expected and not result.get('input_changed') and
                         not result.get('container_identity_changed') and
                         (language!='javascript' or expected_type!='number' or result.get('safe_integer')))
                mutation_checks+=1
                if not correct:
                    accepted=False
                    report['failures'].append({'problem_id':pid,'case_id':case['case_id'],
                      'language':language,'entrypoint':entrypoint,'expected':expected,'result':result})
        if all(len(outputs[lang])==len(cases) for lang in outputs):
            a=outputs['javascript'][index]['results']['solve']
            b=outputs['python'][index]['results']['solve']
            if a.get('ok') and b.get('ok') and a.get('value')==b.get('value'):
                cross_language+=1
        good+=accepted
    categories=dict(Counter(case['category'] for case in cases))
    item={'problem_id':pid,'title':problem['title'],'cases':len(cases),'passed':good,
          'categories':categories,'normative_cases':len(cases)-categories.get('outside_domain_extension',0),
          'input_integrity_checks':mutation_checks,'cross_language_agreements':cross_language,
          'entrypoints_per_language':2,'candidate_invocations':4*len(cases),
          'cases_sha256':sha(case_path),'worker_wall_seconds':runtimes,
          'source_sha256':{lang:sha(ROOT/lang/f'{stem}.{ext}') for lang,ext in [('javascript','js'),('python','py')]}}
    report['problems'].append(item)
    print(f'{stem}: {good}/{len(cases)} paired cases; four entry-point calls per case',flush=True)

report['summary']={
 'unique_problems':len(report['problems']),
 'implementations':len(report['syntax']),
 'syntax_checks_passed':sum(row['passed'] for row in report['syntax']),
 'paired_cases':sum(row['cases'] for row in report['problems']),
 'paired_cases_passed':sum(row['passed'] for row in report['problems']),
 'normative_cases':sum(row['normative_cases'] for row in report['problems']),
 'candidate_invocations':sum(row['candidate_invocations'] for row in report['problems']),
 'input_integrity_checks':sum(row['input_integrity_checks'] for row in report['problems']),
 'cross_language_agreements':sum(row['cross_language_agreements'] for row in report['problems']),
 'failures':len(report['failures']),
}
(ROOT/'validation'/'latest-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
(ARTIFACTS/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(report['summary'],indent=2))
raise SystemExit(bool(report['failures']))
