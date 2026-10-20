"""Qualify only generated pilot sources, reconstructed through counted packets."""
import argparse,hashlib,json,sys,time,importlib.util
from pathlib import Path

def digest(raw):return hashlib.sha256(raw).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

def main():
 p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--generated',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False)
 sys.path[:0]=[str(a.pilot),str(a.pilot/'pass2/working'),str(a.pilot.parent)]
 from literals import dictionary_bytes
 from bitpack import encode,decode
 from verify_execution import HARNESS,strict_object
 from algsolve.judge import sandbox
 checks_raw=(a.pilot/'checks.py').read_bytes();assert digest(checks_raw)==json.loads((a.pilot/'checks_manifest.json').read_text())['checks_sha256'];checks=load('pass3_development_checks',a.pilot/'checks.py')
 manifest=json.loads((a.generated/'manifest.json').read_text());rows=[];start=time.perf_counter();rawdir=a.output/'observations';rawdir.mkdir()
 for problem,variants in sorted(manifest['variants'].items()):
  for name,row in sorted(variants.items()):
   source=(a.generated/row['file']).read_text();assert digest(source.encode())==row['sha256'];dictionary=sorted(set(source));packet=encode(dictionary,[dictionary.index(c) for c in source],8);reconstructed=decode(dictionary_bytes(dictionary),packet);assert reconstructed==source
   cases=checks.cases_by_problem[int(problem)];passed=mutations=0;failures=[];calls=[]
   for offset in range(0,len(cases),256):
    batch=cases[offset:offset+256];payload=json.dumps({'interface':'function','calls':[{'args':c['args']} for c in batch]},ensure_ascii=False).encode();result=sandbox.run(['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'],files={'program.js':reconstructed,'inputs.json':payload,'harness.cjs':HARNESS},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2));stem=f'{problem}-{name}-{offset:05d}';(rawdir/(stem+'.stdout')).write_bytes(result.stdout);(rawdir/(stem+'.stderr')).write_bytes(result.stderr)
    native={'exit_code':result.exit_code,'timed_out':result.timed_out,'output_limit_exceeded':result.output_limit_exceeded,'wall_seconds':result.wall_seconds,'input_sha256':digest(payload),'stdout_sha256':digest(result.stdout),'stderr_sha256':digest(result.stderr)};calls.append(native)
    if not result.ok:failures.append({'offset':offset,'reason':'sandbox_failure'});continue
    try:
     records=[json.loads(line,object_pairs_hook=strict_object,parse_constant=lambda value:(_ for _ in ()).throw(ValueError(value))) for line in result.stdout.splitlines()]
     assert len(records)==len(batch)+1 and records[-1]=={'done':len(batch)} and type(records[-1]['done']) is int
     for index,record in enumerate(records[:-1]):
      assert type(record.get('i')) is int and record['i']==index
      verdict=checks.check_observation(int(problem),offset+index,record);passed+=bool(verdict['passed']);mutations+=not verdict['input_preserved']
      if not verdict['passed']:failures.append({'case':offset+index,'verdict':verdict})
    except Exception as error:failures.append({'offset':offset,'reason':'protocol_error','detail':str(error)})
   rows.append({'problem':problem,'variant':name,'source_sha256':row['sha256'],'passed':passed==len(cases) and not failures,'checks_passed':passed,'checks_total':len(cases),'input_mutations':mutations,'failures':failures,'calls':calls,'packet_sha256':digest(packet),'reconstruction':'Exact per-source character dictionary through existing LTV1 decoder; search packets verified separately.'})
  print(problem, sum(r['passed'] for r in rows if r['problem']==problem),'qualified variants',flush=True)
 report={'schema':'gamma.functional-literals-qualification.v1','rows':rows,'source_count':len(rows),'passed_sources':sum(r['passed'] for r in rows),'checks_passed':sum(r['checks_passed'] for r in rows),'checks_total':sum(r['checks_total'] for r in rows),'elapsed_seconds':time.perf_counter()-start,'checks_sha256':digest(checks_raw),'generator_manifest_sha256':digest((a.generated/'manifest.json').read_bytes()),'verifier_sha256':digest(Path(__file__).read_bytes()),'python':sys.version,'scope':'Same 20 known development problems; no protected cases, corpus admission, formal equivalence or autonomous synthesis.'};(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['source_count','passed_sources','checks_passed','checks_total','elapsed_seconds']}))
if __name__=='__main__':main()
