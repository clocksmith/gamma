"""Exact separate repair variants: pre-execution freeze, isolated run and raw replay."""
import argparse,json,sys
from pathlib import Path
from dataclasses import asdict
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import qualify as q
import oracles as o
IDS=(1219,1254,1271)

def cases(statements,baseline):
 data=q.load_cases(statements,baseline['statement_pins']);data={i:data[i]for i in IDS}
 # Small exact state exploration, and a legal sparse maximum-size matrix.
 grid=[[0]*15 for _ in range(15)]
 for r in range(0,10,2):
  for c in range(0,10,2):grid[r][c]=100
 data[1219]+=[{'args':[grid],'expected':100,'category':'maximum-sparse-isolated-gold'}]
 for grid in [[[0]],[[1]],[[1,0,1],[0,0,0],[1,0,1]],[[1,2,0],[0,3,4],[5,0,6]]]:
  data[1219]+=[{'args':[grid],'expected':o.expected(1219,[grid]),'category':'independent-immutability-path-control'}]
 return data

def freeze(a):
 baseline=json.loads(a.baseline.read_bytes());data=cases(a.statements,baseline)
 assert q.artifacts()==baseline['artifact_hashes']
 report=json.loads(a.baseline_report.read_bytes());assert len(report['programs'])==80
 sources={f'{pid}-{lang}':{'problem_id':pid,'language':lang,'relative_path':str((HERE/(f'{pid}-v2.js'if lang=='javascript'else f'{pid}.py')).relative_to(q.ROOT)),'sha256':q.sha((HERE/(f'{pid}-v2.js'if lang=='javascript'else f'{pid}.py')).read_bytes())}for pid in IDS for lang,ext in [('python','py'),('javascript','js')]}
 contract={'schema':'gamma.downloaded-batch09-repairs.v2','baseline_freeze_sha256':q.sha(a.baseline.read_bytes()),'baseline_report_sha256':q.sha(a.baseline_report.read_bytes()),'baseline_artifact_hashes':q.artifacts(),'runtime':q.runtime(),'helper_sha256':q.sha(Path(__file__).read_bytes()),'cases_sha256':q.sha(q.encoded(data)),'case_counts':{str(k):len(v)for k,v in data.items()},'batch_plan':{str(k):list(q.batches(v))for k,v in data.items()},'limits':asdict(q.LIMITS),'argv':q.ARGV,'sources':sources,'scope':'Separate solve-source identities; originals preserved. 1271 stays normative-definition blocked; no official wrapper or catalogue admission qualification.'}
 q.write(a.contract,contract);print('REPAIRS_FROZEN',q.sha(a.contract.read_bytes()),flush=True)

def read(a):
 raw=a.contract.read_bytes();c=json.loads(raw);b=json.loads(a.baseline.read_bytes());d=cases(a.statements,b)
 assert q.sha(a.baseline.read_bytes())==c['baseline_freeze_sha256']and q.artifacts()==c['baseline_artifact_hashes']
 assert q.sha(Path(__file__).read_bytes())==c['helper_sha256']and q.sha(q.encoded(d))==c['cases_sha256']
 assert {str(k):list(q.batches(v))for k,v in d.items()}==c['batch_plan']and asdict(q.LIMITS)==c['limits']and q.ARGV==c['argv']
 for row in c['sources'].values():assert q.sha((q.ROOT/row['relative_path']).read_bytes())==row['sha256']
 return raw,c,d

def summary(pid,language,c,values,total,failures):
 return {'problem_id':pid,'language':language,'source_sha256':c['sources'][f'{pid}-{language}']['sha256'],'distinct_cases':len(values),'attempted_calls':total,'failures':failures,'passed':not failures,'qualified':not failures and pid not in o.DEFINITION_BLOCKED,'definition_gate_failure':'Official public definition unavailable; provisional semantics cannot qualify'if pid in o.DEFINITION_BLOCKED else None,'official_wrapper_execution_qualified':False,'immutable_input_static_review':'Owned visited mask/seen container; no assignments through caller input references'}

def report(raw,rows):return {'contract_sha256':q.sha(raw),'programs':rows,'passed':all(r['passed']for r in rows),'canonical_admission_changed':False}

def execute(a):
 raw,c,d=read(a);assert q.sha(raw)==a.contract_sha256 and q.runtime()==c['runtime'];a.output.mkdir(parents=True,exist_ok=False)
 q.write(a.output/'identity.json',{'contract_sha256':q.sha(raw),'sources':c['sources']});rows=[]
 for pid in IDS:
  for lang,ext,harness in [('python','py','harness.py'),('javascript','js','harness.cjs')]:
   failures=[];calls=0
   for index,indices in enumerate(c['batch_plan'][str(pid)]):
    stem=f'{pid}-{lang}-{index:03d}';packet={'entry':'solve','calls':[{'args':d[pid][j]['args']}for j in indices]}
    q.write(a.output/(stem+'.start.json'),{'indices':indices,'inputs_sha256':q.sha(q.encoded(packet))})
    result=q.sandbox.run(q.ARGV[lang],files={'program.'+ext:(q.ROOT/c['sources'][f'{pid}-{lang}']['relative_path']).read_bytes(),harness:(q.ROOT/q.TRANSPORT/harness).read_bytes(),'inputs.json':q.encoded(packet)},limits=q.LIMITS);m=asdict(result)
    for stream in ('stdout','stderr'):
     payload=m.pop(stream);(a.output/(stem+'.'+stream)).write_bytes(payload);m[stream+'_sha256']=q.sha(payload)
    q.write(a.output/(stem+'.result.json'),m);failures+=q.verdict(pid,lang,d[pid],indices,m,result.stdout);calls+=len(indices)
   row=summary(pid,lang,c,d[pid],calls,failures);rows.append(row);print(json.dumps(row),flush=True)
 q.write(a.output/'report.json',report(raw,rows))

def verify(a):
 raw,c,d=read(a);assert json.loads((a.output/'identity.json').read_bytes())=={'contract_sha256':q.sha(raw),'sources':c['sources']};rows=[];batches=0
 for pid in IDS:
  for lang in ('python','javascript'):
   failures=[];calls=0
   for index,indices in enumerate(c['batch_plan'][str(pid)]):
    stem=f'{pid}-{lang}-{index:03d}';packet={'entry':'solve','calls':[{'args':d[pid][j]['args']}for j in indices]}
    assert json.loads((a.output/(stem+'.start.json')).read_bytes())=={'indices':indices,'inputs_sha256':q.sha(q.encoded(packet))}
    m=json.loads((a.output/(stem+'.result.json')).read_bytes())
    for stream in ('stdout','stderr'):assert q.sha((a.output/(stem+'.'+stream)).read_bytes())==m[stream+'_sha256']
    failures+=q.verdict(pid,lang,d[pid],indices,m,(a.output/(stem+'.stdout')).read_bytes());calls+=len(indices);batches+=1
   rows.append(summary(pid,lang,c,d[pid],calls,failures))
 assert json.loads((a.output/'report.json').read_bytes())==report(raw,rows)
 result={'schema':'gamma.downloaded-batch09-repair-replay.v1','contract_sha256':q.sha(raw),'attempted_calls_replayed':sum(r['attempted_calls']for r in rows),'sandbox_batches_replayed':batches,'programs_passed':sum(r['passed']for r in rows),'programs_qualified':sum(r['qualified']for r in rows),'source_byte_hashes':c['sources'],'raw_artifact_hashes':{p.name:q.sha(p.read_bytes())for p in sorted(a.output.iterdir())if p.is_file()and p.name!='replay.json'}}
 q.write(a.output/'replay.json',result);print(json.dumps({k:v for k,v in result.items()if k!='raw_artifact_hashes'}),flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('operation',choices=('freeze','run','verify'))
 for name in ('statements','baseline','contract'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--baseline-report',type=Path);p.add_argument('--output',type=Path);p.add_argument('--contract-sha256');a=p.parse_args();{'freeze':freeze,'run':execute,'verify':verify}[a.operation](a)
if __name__=='__main__':main()
