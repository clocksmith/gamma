"""Bounded source-bound development executions. No qualification/admission changes."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import platform
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
COHORTS=('requested-243-370-35-20261028-v1','requested-156-1940-31-20261028-v1')
GATE='projects/algorithm_solver/catalogue/private-recovery-20261026/qualified-sources/owner-artifacts/originals/workspace/shared/gamma-all4081-metadata-v3-20261025-1949/identity-metadata.json'


def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
def load(path):return json.loads(Path(path).read_text())
def stamp():return datetime.now(timezone.utc).isoformat()
def normalize(value):
    if isinstance(value,dict):
        if set(value)=={'$integer'}:return int(value['$integer'])
        return {k:normalize(v) for k,v in value.items()}
    if isinstance(value,list):return [normalize(v) for v in value]
    return value
def equal(actual, expected):
    if type(actual) is bool or type(expected) is bool:return type(actual) is type(expected) and actual==expected
    if isinstance(actual,(int,float)) and isinstance(expected,(int,float)):return math.isfinite(actual) and math.isfinite(expected) and actual==expected
    if isinstance(actual,list) and isinstance(expected,(list,tuple)):return len(actual)==len(expected) and all(equal(a,b) for a,b in zip(actual,expected))
    if isinstance(actual,dict) and isinstance(expected,dict):return set(actual)==set(expected) and all(equal(actual[k],expected[k]) for k in actual)
    return type(actual) is type(expected) and actual==expected


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--only',type=int,nargs='+');args=parser.parse_args()
    declared={int(row['id']) for cohort in COHORTS for row in load(ROOT/'projects/algorithm_solver/catalogue/authored'/cohort/'contracts.json')['problems']}
    if args.only is not None and set(args.only)-declared:raise ValueError('Unknown requested development IDs: '+str(sorted(set(args.only)-declared)))
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
    gate=load(ROOT/GATE);allowed={int(row['problem_id']) for row in gate['rows'] if row['source_access']=='authorized-prospective-source-and-statement-acquisition'}
    policy={'schema':'gamma.development-comparison-policy.v1','startedAt':stamp(),'comparison':'Exact typed JSON under the existing cohort contract; nonunique/float/native discrepancies are failures to investigate, not silently accepted.','candidateEntrypoint':'solve JSON wrapper; native ABI is a separate check','expectedResults':'Retained in controller only, never passed to candidates','budget':{'perCallSeconds':1,'rssBytes':1024**3,'processTimeoutSeconds':3,'nodeHeapMiB':512,'nodeJitless':True},'qualification':'unknown','gateMetadataSha256':digest((ROOT/GATE).read_bytes()),'runtimes':{'python':platform.python_version(),'node':subprocess.check_output(['node','--version'],text=True).strip()},'tools':{p.name:digest(p.read_bytes()) for p in (HERE/'run.py',HERE/'run-case.py',HERE/'run-case.cjs')}}
    (out/'policy.json').write_text(json.dumps(policy,indent=2)+'\n')
    report={'schema':'gamma.author-development-execution.v1','startedAt':policy['startedAt'],'policySha256':digest((out/'policy.json').read_bytes()),'qualification':'unknown','independentQualification':0,'admissions':0,'results':[],'failures':[],'inputs':[]}
    with tempfile.TemporaryDirectory(prefix='gamma-dev66-') as temporary:
        directory=Path(temporary)
        with (out/'calls.jsonl').open('w') as log:
            for cohort in COHORTS:
                base=ROOT/'projects/algorithm_solver/catalogue/authored'/cohort
                cases_spec=importlib.util.spec_from_file_location('development_cases_'+cohort.replace('-','_'),base/'cases.py');cases_module=importlib.util.module_from_spec(cases_spec);cases_spec.loader.exec_module(cases_module)
                contracts=load(base/'contracts.json')['problems']
                for filename in ('contracts.json','oracles.py','cases.py','checks.json'):
                    p=base/filename;report['inputs'].append({'path':str(p.relative_to(ROOT)),'sha256':digest(p.read_bytes())})
                for contract in contracts:
                    pid=int(contract['id'])
                    if args.only and pid not in args.only:continue
                    if pid not in allowed:raise RuntimeError('Source access gate blocks '+str(pid))
                    cases=cases_module.build_cases(pid,include_maximum=True)
                    for language,suffix in [('python','py'),('javascript','js')]:
                        source=base/language/(str(pid)+'.'+suffix);raw=source.read_bytes();source_hash=digest(raw);pinned=directory/(str(pid)+'.'+suffix);pinned.write_bytes(raw)
                        row={'cohort':cohort,'id':pid,'language':language,'source':str(source.relative_to(ROOT)),'sourceSha256':source_hash,'cases':len(cases),'passedCases':0,'failedCases':0,'maxCallSeconds':0,'maxRssBytes':0,'coverage':'Source-defined base and extended cases; not established official domain maxima'}
                        for index,case in enumerate(cases):
                            actual=None;response={};failure=None
                            command=[sys.executable,str(HERE/'run-case.py'),str(pinned)] if language=='python' else ['node','--jitless','--max-old-space-size=512',str(HERE/'run-case.cjs'),str(pinned)]
                            try:
                                process=subprocess.run(command,input=encoded(case['args']),capture_output=True,timeout=policy['budget']['processTimeoutSeconds'])
                                if process.returncode:raise RuntimeError('Candidate process failed: '+process.stderr.decode(errors='replace')[-1000:])
                                response=load_response=json.loads(process.stdout);actual=normalize(response['result'])
                                if response['sourceSha256']!=source_hash:raise RuntimeError('Executed source hash mismatch')
                                if response['exception']:failure='exception'
                                elif not equal(response['argumentsAfter'],case['args']):failure='wrapper-input-mutation'
                                elif not equal(actual,case['expected']):failure='result-mismatch'
                                elif response['elapsedSeconds']>=1:failure='call-time-budget'
                                elif response['rssBytes']>=1024**3:failure='memory-budget'
                            except Exception as error:
                                failure='process-or-protocol: '+str(error)
                            call={'cohort':cohort,'id':pid,'language':language,'case':index,'sourceSha256':source_hash,'argumentsSha256':digest(encoded(case['args'])),'expectedSha256':digest(encoded(case['expected'])),'passed':failure is None,'failure':failure,'elapsedSeconds':response.get('elapsedSeconds'),'rssBytes':response.get('rssBytes')}
                            row['maxCallSeconds']=max(row['maxCallSeconds'],response.get('elapsedSeconds',0));row['maxRssBytes']=max(row['maxRssBytes'],response.get('rssBytes',0))
                            if failure:
                                row['failedCases']+=1;detail={**call,'arguments':case['args'],'expected':case['expected'],'actual':actual,'exception':response.get('exception')};report['failures'].append(detail)
                            else:row['passedCases']+=1
                            log.write(json.dumps(call,ensure_ascii=False)+'\n');log.flush()
                        row['passed']=row['failedCases']==0;report['results'].append(row)
                        print(cohort,pid,language,row['passedCases'],'/',row['cases'],flush=True)
    report.update(finishedAt=stamp(),programsExecuted=len(report['results']),caseCalls=sum(r['cases'] for r in report['results']),passedCaseCalls=sum(r['passedCases'] for r in report['results']),passed=not report['failures'])
    (out/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:report[k] for k in ('programsExecuted','caseCalls','passedCaseCalls','passed')}))
    return 0 if report['passed'] else 1


if __name__=='__main__':sys.exit(main())
