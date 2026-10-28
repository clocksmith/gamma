"""Freeze, isolate and replay five separate repaired source identities."""
import argparse,json,sys
from pathlib import Path
from dataclasses import asdict
from itertools import product
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import qualify as q
import oracles as o
SLOTS=((1477,'python'),(1477,'javascript'),(1488,'python'),(1488,'javascript'),(1578,'javascript'))
def cases(statements,baseline):
 all_data=q.load_cases(statements,baseline['statement_pins']);data={i:all_data[i][:]for i in (1477,1488,1578)};seen={i:{q.encoded(v['args'])for v in a}for i,a in data.items()}
 def add(pid,args):
  key=q.encoded(args)
  if key not in seen[pid]:seen[pid].add(key);data[pid].append({'args':args,'expected':o.expected(pid,args),'category':'independent-exhaustive-repair-regression'})
 for n in range(1,6):
  for arr in product((1,2,3),repeat=n):
   for target in range(1,9):add(1477,[list(arr),target])
 for n in range(1,7):
  for arr in product((0,1,2),repeat=n):add(1488,[list(arr)])
 for arr in [[1,2,3,0,0,1,0,2,3],[1,2,3,0,1,2,3],[0,1,0,2,0,1,2],[1,0,0,1,1]]:add(1488,[arr])
 for n in range(1,5):
  for s in product('ab',repeat=n):
   for costs in product((1,3),repeat=n):add(1578,[''.join(s),list(costs)])
 return data

def freeze(a):
 baseline=json.loads(a.baseline.read_bytes());data=cases(a.statements,baseline);assert q.artifacts()==baseline['artifact_hashes'];original=json.loads(a.baseline_report.read_bytes());assert len(original['programs'])==62
 sources={f'{pid}-{lang}':{'problem_id':pid,'language':lang,'relative_path':str((HERE/f'{pid}.{"py"if lang=="python"else"js"}').relative_to(q.ROOT)),'sha256':q.sha((HERE/f'{pid}.{"py"if lang=="python"else"js"}').read_bytes())}for pid,lang in SLOTS}
 c={'schema':'gamma.downloaded-batch11-repairs.v1','baseline_freeze_sha256':q.sha(a.baseline.read_bytes()),'baseline_report_sha256':q.sha(a.baseline_report.read_bytes()),'baseline_artifact_hashes':q.artifacts(),'runtime':q.runtime(),'helper_sha256':q.sha(Path(__file__).read_bytes()),'cases_sha256':q.sha(q.encoded(data)),'case_counts':{str(i):len(v)for i,v in data.items()},'batch_plan':{str(i):list(q.batches(v))for i,v in data.items()},'limits':asdict(q.LIMITS),'argv':q.ARGV,'sources':sources,'scope':'Separate five solve variants; original failures retained; no shared/original/catalogue/promotion changes; static immutable input reviewed.'}
 q.write(a.contract,c);print('REPAIRS_FROZEN',q.sha(a.contract.read_bytes()),flush=True)
def read(a):
 raw=a.contract.read_bytes();c=json.loads(raw);b=json.loads(a.baseline.read_bytes());data=cases(a.statements,b)
 assert q.sha(a.baseline.read_bytes())==c['baseline_freeze_sha256']and q.artifacts()==c['baseline_artifact_hashes']
 assert q.sha(Path(__file__).read_bytes())==c['helper_sha256']and q.sha(q.encoded(data))==c['cases_sha256']
 assert {str(i):list(q.batches(v))for i,v in data.items()}==c['batch_plan']and asdict(q.LIMITS)==c['limits']and q.ARGV==c['argv']
 for source in c['sources'].values():assert q.sha((q.ROOT/source['relative_path']).read_bytes())==source['sha256']
 return raw,c,data
def row(pid,lang,c,values,calls,failures):return {'problem_id':pid,'language':lang,'source_sha256':c['sources'][f'{pid}-{lang}']['sha256'],'distinct_cases':len(values),'attempted_calls':calls,'failures':failures,'passed':not failures,'qualified':not failures,'official_wrapper_execution_qualified':False,'static_immutable_review':'Caller reads only; writes confined to owned shortest/parent/answer arrays or primitive locals'}
def report(raw,rows):return {'contract_sha256':q.sha(raw),'programs':rows,'passed':all(r['passed']for r in rows),'canonical_admission_changed':False}
def execute(a):
 raw,c,data=read(a);assert q.sha(raw)==a.contract_sha256 and q.runtime()==c['runtime'];a.output.mkdir(parents=True,exist_ok=False);q.write(a.output/'identity.json',{'contract_sha256':q.sha(raw),'sources':c['sources']});rows=[]
 for pid,lang in SLOTS:
  ext,harness=('py','harness.py')if lang=='python'else('js','harness.cjs');failures=[];calls=0
  for b,indices in enumerate(c['batch_plan'][str(pid)]):
   stem=f'{pid}-{lang}-{b:03d}';packet={'entry':'solve','calls':[{'args':data[pid][i]['args']}for i in indices]};q.write(a.output/(stem+'.start.json'),{'indices':indices,'inputs_sha256':q.sha(q.encoded(packet))})
   result=q.sandbox.run(q.ARGV[lang],files={'program.'+ext:(q.ROOT/c['sources'][f'{pid}-{lang}']['relative_path']).read_bytes(),harness:(q.ROOT/q.TRANSPORT/harness).read_bytes(),'inputs.json':q.encoded(packet)},limits=q.LIMITS);m=asdict(result)
   for stream in ('stdout','stderr'):
    payload=m.pop(stream);(a.output/(stem+'.'+stream)).write_bytes(payload);m[stream+'_sha256']=q.sha(payload)
   q.write(a.output/(stem+'.result.json'),m);failures+=q.verdict(pid,lang,data[pid],indices,m,result.stdout);calls+=len(indices)
  summary=row(pid,lang,c,data[pid],calls,failures);rows.append(summary);print(json.dumps(summary),flush=True)
 q.write(a.output/'report.json',report(raw,rows))
def verify(a):
 raw,c,data=read(a);assert json.loads((a.output/'identity.json').read_bytes())=={'contract_sha256':q.sha(raw),'sources':c['sources']};rows=[];batches=0
 for pid,lang in SLOTS:
  failures=[];calls=0
  for b,indices in enumerate(c['batch_plan'][str(pid)]):
   stem=f'{pid}-{lang}-{b:03d}';packet={'entry':'solve','calls':[{'args':data[pid][i]['args']}for i in indices]};assert json.loads((a.output/(stem+'.start.json')).read_bytes())=={'indices':indices,'inputs_sha256':q.sha(q.encoded(packet))};m=json.loads((a.output/(stem+'.result.json')).read_bytes())
   for stream in ('stdout','stderr'):assert q.sha((a.output/(stem+'.'+stream)).read_bytes())==m[stream+'_sha256']
   failures+=q.verdict(pid,lang,data[pid],indices,m,(a.output/(stem+'.stdout')).read_bytes());calls+=len(indices);batches+=1
  rows.append(row(pid,lang,c,data[pid],calls,failures))
 assert json.loads((a.output/'report.json').read_bytes())==report(raw,rows)
 v={'schema':'gamma.downloaded-batch11-repair-replay.v1','contract_sha256':q.sha(raw),'attempted_calls_replayed':sum(r['attempted_calls']for r in rows),'sandbox_batches_replayed':batches,'programs_passed':sum(r['passed']for r in rows),'programs_qualified':sum(r['qualified']for r in rows),'source_byte_hashes':c['sources'],'raw_artifact_hashes':{p.name:q.sha(p.read_bytes())for p in sorted(a.output.iterdir())if p.is_file()and p.name!='replay.json'}};q.write(a.output/'replay.json',v);print(json.dumps({k:v for k,v in v.items()if k!='raw_artifact_hashes'}),flush=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('operation',choices=('freeze','run','verify'))
 for name in ('statements','baseline','contract'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--baseline-report',type=Path);p.add_argument('--output',type=Path);p.add_argument('--contract-sha256');a=p.parse_args();{'freeze':freeze,'run':execute,'verify':verify}[a.operation](a)
if __name__=='__main__':main()
