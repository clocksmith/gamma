"""Bounded development execution; host-only expected values, exact decoded source."""
import argparse,json,sys,time,hashlib,importlib.util
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--generated',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ids',nargs='*',type=int);a=p.parse_args();root=Path(__file__).resolve().parent;contract=json.loads((root/'contract.json').read_text());a.output.mkdir(exist_ok=False);(a.output/'observations').mkdir()
 sys.path[:0]=[str(a.pilot),str(a.pilot/'pass2/working'),str(a.pilot.parent)]
 from literals import dictionary_bytes
 from bitpack import encode,decode
 from algsolve.judge import sandbox
 # Load only the already-public original20 host checks and harness.
 old=load('cluster_old_checks',a.pilot/'checks.py');new=load('cluster_new_checks',root/'checks.py');h=load('cluster_harness',a.pilot/'verify_execution.py')
 manifest=json.loads((a.generated/'manifest.json').read_text());rows=[];start=time.monotonic();original_observations={}
 byid={i:sorted([r for r in manifest['rows'] if r['id']==i],key=lambda r:r['variant']!='original') for i in sorted({r['id'] for r in manifest['rows']})}
 if a.ids:byid={i:rows for i,rows in byid.items() if i in a.ids}
 for i,variants in byid.items():
  cases=old.cases_by_problem[i] if i in old.METHODS else new.make_cases(i)
  for row in variants:
   if time.monotonic()-start>180:raise TimeoutError('qualification budget')
   source=(a.generated/row['file']).read_text();assert sha(source.encode())==row['sha256'];vocab=sorted(set(source));packet=encode(vocab,[vocab.index(c) for c in source],8);decoded=decode(dictionary_bytes(vocab),packet);assert decoded==source
   passes=mutations=equiv=0;failures=[];calls=[];observed=[]
   for offset in range(0,len(cases),256):
    batch=cases[offset:offset+256];payload=json.dumps({'interface':'class' if row['variant']=='original' else 'function','method':row['method'],'calls':[{'args':c['args']} for c in batch]},ensure_ascii=False).encode()
    result=sandbox.run(['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'],files={'program.js':decoded,'inputs.json':payload,'harness.cjs':h.HARNESS},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2))
    stem=f"{i:04d}-{row['variant']}-{offset:05d}";(a.output/'observations'/(stem+'.stdout')).write_bytes(result.stdout);(a.output/'observations'/(stem+'.stderr')).write_bytes(result.stderr);calls.append({'exit_code':result.exit_code,'timeout':result.timed_out,'wall_seconds':result.wall_seconds,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr)})
    if not result.ok:failures.append({'offset':offset,'reason':'sandbox_failure'});continue
    try:
     records=[json.loads(line,object_pairs_hook=h.strict_object,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))) for line in result.stdout.splitlines()];assert len(records)==len(batch)+1 and records[-1]=={'done':len(batch)}
     for k,rec in enumerate(records[:-1]):
      assert type(rec.get('i')) is int and rec['i']==k;case=cases[offset+k];preserved=rec.get('args_before')==rec.get('args_after');mutations+=not preserved
      if i in old.METHODS:valid=old.check_observation(i,offset+k,rec)['passed']
      else:valid='error' not in rec and rec.get('args_before')==case['args'] and new.output_ok(i,case['args'],rec.get('result'),case['expected']) and (rec.get('args_after')==[rec.get('result')] if i in [832,922] else rec.get('args_after')==[sorted(case['args'][0])] if i==976 else preserved)
      observation={key:rec.get(key) for key in ['result','args_after','error']};observed.append(observation)
      if row['variant']!='original':same=observation==original_observations[i][offset+k];equiv+=same;valid=valid and same
      passes+=bool(valid)
      if not valid:failures.append({'case':offset+k,'reason':'oracle_or_input_or_baseline_equivalence'})
    except Exception as error:failures.append({'offset':offset,'reason':'protocol_or_comparison','detail':str(error)})
   if row['variant']=='original':original_observations[i]=observed
   rows.append({**row,'checks_passed':passes,'checks_total':len(cases),'observed_input_mutations':mutations,'exact_original_behavior_matches':equiv if row['variant']!='original' else None,'passed':passes==len(cases) and not failures,'failures':failures,'calls':calls})
  print(i,[(r['variant'],r['checks_passed'],r['checks_total']) for r in rows if r['id']==i],flush=True)
 report={'schema':'gamma.cluster-qualification.v1','phase':manifest['phase'],'source_count':len(rows),'passed_sources':sum(r['passed'] for r in rows),'checks_passed':sum(r['checks_passed'] for r in rows),'checks_total':sum(r['checks_total'] for r in rows),'distinct_reference_cases':sum(len(old.cases_by_problem[i]) if i in old.METHODS else len(new.make_cases(i)) for i in byid),'elapsed_seconds':time.monotonic()-start,'checks_sha256':sha((root/'checks.py').read_bytes()),'old_checks_sha256':sha((a.pilot/'checks.py').read_bytes()),'generated_manifest_sha256':sha((a.generated/'manifest.json').read_bytes()),'rows':rows,'scope':'Development oracle checks and exact result/input-mutation parity across variants. No corpus admission, protected evaluation, formal equivalence or autonomous synthesis.'};(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['source_count','passed_sources','checks_passed','checks_total','distinct_reference_cases','elapsed_seconds']}))
if __name__=='__main__':main()
