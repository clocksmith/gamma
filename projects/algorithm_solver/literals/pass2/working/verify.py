"""Execute all twenty programs decoded directly from the shared7 bit packets."""
import argparse,json,sys,time
from pathlib import Path
from bitpack import decode
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[1]))
from literals import digest,json_bytes
from verify_execution import load_module,strict_object,HARNESS

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--sandbox-module',type=Path,default=ROOT.parents[2]/'algsolve/judge/sandbox.py');args=p.parse_args()
 packages=ROOT/'packages/shared7';manifest=json.loads((packages/'manifest.json').read_bytes());dictionary=(packages/'dictionary.ltd').read_bytes()
 if digest(dictionary)!=manifest['dictionary_sha256']:raise ValueError('dictionary drift')
 checks_raw=(ROOT.parents[1]/'checks.py').read_bytes();pins=json.loads((ROOT.parent/'source_manifest.json').read_bytes())
 if digest(checks_raw)!=pins['checks_sha256']:raise ValueError('checks drift')
 checks=load_module('working_checks',ROOT.parents[1]/'checks.py',checks_raw)
 raw=args.sandbox_module.read_bytes();sandbox=load_module('working_sandbox',args.sandbox_module,raw)
 args.output.mkdir(parents=True,exist_ok=False);observations=args.output/'observations';observations.mkdir();rows=[];calls=0;started=time.perf_counter()
 for key,row in sorted(manifest['programs'].items()):
  packet=(packages/'programs'/f'{key}.ltv').read_bytes()
  if digest(packet)!=row['packet_sha256']:raise ValueError('packet drift')
  source=decode(dictionary,packet)
  if digest(source.encode())!=row['source_sha256'] or row['source_sha256']!=pins['source_hashes'][key+'/'+row['variant']]:raise ValueError('source drift')
  cases=checks.cases_by_problem[int(key)];passed=0;failures=[]
  for offset in range(0,len(cases),256):
   selected=cases[offset:offset+256];payload=json_bytes({'interface':'function','calls':[{'args':c['args']} for c in selected]})
   result=sandbox.run(['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=64','harness.cjs'],files={'program.js':source,'inputs.json':payload,'harness.cjs':HARNESS},limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=4*1024**2))
   name=f'{key}-{offset:05}';(observations/(name+'.stdout')).write_bytes(result.stdout);(observations/(name+'.stderr')).write_bytes(result.stderr)
   (observations/(name+'.native.json')).write_bytes(json_bytes({'ok':result.ok,'exit_code':result.exit_code,'signal':result.signal,'timed_out':result.timed_out,'output_limit_exceeded':result.output_limit_exceeded,'wall_seconds':result.wall_seconds,'notes':result.notes,'source_sha256':digest(source.encode()),'input_sha256':digest(payload),'stdout_sha256':digest(result.stdout),'stderr_sha256':digest(result.stderr)}))
   if not result.ok:raise RuntimeError('native failure '+name)
   records=[json.loads(line,object_pairs_hook=strict_object,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))) for line in result.stdout.splitlines()]
   if len(records)!=len(selected)+1 or records[-1]!={'done':len(selected)} or type(records[-1].get('done')) is not int:raise ValueError('completion')
   for i,record in enumerate(records[:-1]):
    if type(record.get('i')) is not int or record['i']!=i:raise ValueError('order')
    verdict=checks.check_observation(int(key),offset+i,record);passed+=verdict['passed']
    if not verdict['passed']:failures.append({'case':offset+i,'verdict':verdict})
   calls+=1
  rows.append({'problem':key,'source_sha256':row['source_sha256'],'packet_sha256':row['packet_sha256'],'total':len(cases),'passed':passed,'failures':failures})
 report={'schema':'gamma.working-literal-bitpacket-execution.v1','language':'shared7','bits_per_selection':7,'literal_count':manifest['literal_count'],'programs':len(rows),'total_cases':sum(r['total'] for r in rows),'passed_cases':sum(r['passed'] for r in rows),'all_passed':all(r['passed']==r['total'] for r in rows),'sandbox_calls':calls,'rows':rows,'checks_sha256':digest(checks_raw),'sandbox_sha256':digest(raw),'runner_sha256':digest(Path(__file__).read_bytes()),'codec_sha256':digest((ROOT/'bitpack.py').read_bytes()),'dictionary_sha256':digest(dictionary),'harness_sha256':digest(HARNESS.encode()),'expected_in_sandbox':False,'elapsed_seconds':time.perf_counter()-started}
 (args.output/'report.json').write_bytes(json_bytes(report));print(json.dumps({k:report[k] for k in ['programs','total_cases','passed_cases','all_passed']}))
 if not report['all_passed']:raise SystemExit(1)
if __name__=='__main__':main()
