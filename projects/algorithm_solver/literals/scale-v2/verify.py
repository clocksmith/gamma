"""Execute packed sources, preserving raw observations and independent verdicts."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parent;PILOT=ROOT.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def same_value(value, expected):
    if isinstance(expected, bool):return type(value) is bool and value == expected
    if isinstance(expected, (int,float)):return type(value) in (int,float) and value == expected
    if isinstance(expected, list):return isinstance(value,list) and len(value)==len(expected) and all(same_value(x,y) for x,y in zip(value,expected))
    return type(value) is type(expected) and value == expected

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    sys.path[:0]=[str(PILOT),str(PILOT/'pass2/working'),str(PILOT.parent)]
    from literals import dictionary_bytes
    from bitpack import encode,decode
    from algsolve.judge import sandbox
    old=load('scale_old',PILOT/'checks.py');cluster=load('scale_cluster',PILOT/'clusters-v1/checks.py');new=load('scale_new',ROOT/'checks.py');h=load('scale_harness',PILOT/'verify_execution.py')
    harness=h.HARNESS.replace('packet.interface === "function" ? "solve" : "Solution"','packet.entry')
    manifest=json.loads((ROOT/'generated/manifest.json').read_text());a.output.mkdir(exist_ok=False);(a.output/'observations').mkdir()
    rows=[];started=time.monotonic();original={};cases_count=0
    ids=sorted(set(r['id'] for r in manifest['rows']));additional=set(json.loads((ROOT/'contract.json').read_text())['additional_ids'])
    for i in ids:
        cases=new.make_cases(i) if i in additional else old.cases_by_problem[i] if i in old.METHODS else cluster.make_cases(i)
        cases_count+=len(cases)
        variants=sorted((r for r in manifest['rows'] if r['id']==i),key=lambda r:r['variant']!='original')
        for row in variants:
            if time.monotonic()-started>180:raise TimeoutError('qualification wall budget')
            text=(ROOT/'generated'/row['file']).read_text();assert sha(text.encode())==row['sha256']
            alphabet=sorted(set(text));assert len(alphabet)<=256
            decoded=decode(dictionary_bytes(alphabet),encode(alphabet,[alphabet.index(c) for c in text],8));assert decoded==text
            observed=[];calls=[];failures=[];passed=0;mutations=0
            for offset in range(0,len(cases),256):
                batch=cases[offset:offset+256]
                payload={'interface':'class' if row['interface']=='class' else 'function','entry':row['entry'],'method':row['method'],'calls':[{'args':c['args']} for c in batch]}
                result=sandbox.run(['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'],files={'program.js':decoded,'inputs.json':json.dumps(payload),'harness.cjs':harness},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2))
                stem=f'{i:04d}-{row["variant"]}-{offset}'
                (a.output/'observations'/(stem+'.stdout')).write_bytes(result.stdout);(a.output/'observations'/(stem+'.stderr')).write_bytes(result.stderr)
                calls.append({'exit_code':result.exit_code,'timeout':result.timed_out,'seconds':result.wall_seconds,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr)})
                if not result.ok:failures.append({'offset':offset,'reason':'sandbox_failure'});continue
                try:
                    records=[json.loads(line,object_pairs_hook=h.strict_object,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))) for line in result.stdout.splitlines()]
                    assert len(records)==len(batch)+1 and records[-1]=={'done':len(batch)}
                    for k,rec in enumerate(records[:-1]):
                        assert type(rec.get('i')) is int and rec['i']==k
                        case=cases[offset+k];preserved=rec.get('args_before')==rec.get('args_after');mutations+=not preserved
                        if i in additional:
                            valid='error' not in rec and rec.get('args_before')==case['args'] and same_value(rec.get('result'),case['expected']) and preserved
                        elif i in old.METHODS:valid=old.check_observation(i,offset+k,rec)['passed']
                        else:
                            valid='error' not in rec and rec.get('args_before')==case['args'] and cluster.output_ok(i,case['args'],rec.get('result'),case['expected']) and (rec.get('args_after')==[rec.get('result')] if i in [832,922] else rec.get('args_after')==[sorted(case['args'][0])] if i==976 else preserved)
                        observation={key:rec.get(key) for key in ['result','args_after','error']};observed.append(observation)
                        if row['variant']!='original':valid=valid and observation==original[i][offset+k]
                        passed+=bool(valid)
                        if not valid:failures.append({'case':offset+k,'reason':'oracle_input_or_original_parity'})
                except Exception as e:failures.append({'offset':offset,'reason':'protocol','detail':str(e)})
            if row['variant']=='original':original[i]=observed
            rows.append({**row,'passed':passed==len(cases) and not failures,'checks_passed':passed,'checks_total':len(cases),'mutations':mutations,'failures':failures,'calls':calls})
        print(i,[(r['variant'],r['checks_passed'],r['checks_total']) for r in rows if r['id']==i],flush=True)
    report={'schema':'gamma.literal-scale-qualification.v2','rows':rows,'source_count':len(rows),'passed_sources':sum(r['passed'] for r in rows),'checks_passed':sum(r['checks_passed'] for r in rows),'checks_total':sum(r['checks_total'] for r in rows),'distinct_cases':cases_count,'elapsed_seconds':time.monotonic()-started,'generated_manifest_sha256':sha((ROOT/'generated/manifest.json').read_bytes()),'checks_sha256':{str(p.relative_to(PILOT)):sha(p.read_bytes()) for p in [ROOT/'checks.py',PILOT/'checks.py',PILOT/'clusters-v1/checks.py']},'harness_sha256':sha(harness.encode()),'scope':'Finite development oracle checks plus exact original output/input effect parity. Not official judge, proof, human assembly, or autonomous solving.'}
    (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['rows','checks_sha256','scope']}))

if __name__=='__main__':main()
