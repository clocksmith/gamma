"""Freeze direct-entry candidates from independently verified adapted sources."""
import argparse,importlib.util,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'paired-authoring-v1'))
import verify_adapted
b=verify_adapted.b

def pins():
 paths=[HERE/n for n in ('lower.mjs','supply.py','qualify.py','verify.py','CONTRACT.md')]+[LIT/'role-canonical-v1/parser.mjs',LIT/'paired-authoring-v1/verify_adapted.py',LIT/'paired-authoring-v1/baseline_replay.py']
 return {str(p.relative_to(LIT)):b.sha(p.read_bytes()) for p in paths}

def generate(sources,node_path):
 result=subprocess.run([str(node_path),str(HERE/'lower.mjs')],input=b.encoded({'sources':sources}),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,check=True)
 rows=json.loads(result.stdout)
 if set(rows)!=set(sources):raise ValueError('lowering changed source population')
 for pid,row in rows.items():
  if type(row.get('ok')) is not bool:raise ValueError('missing lowering status')
  if row['ok']:
   if row.get('ast_verified') is not True or row.get('helpers_verbatim') is not True or row.get('strict_directive_added') is not True or row.get('candidate_executions')!=0 or not isinstance(row.get('source'),str) or row.get('source_bytes')!=len(sources[pid].encode()) or row.get('lowered_bytes')!=len(row['source'].encode()):raise ValueError('invalid lowering receipt')
  elif not isinstance(row.get('error'),str):raise ValueError('missing retained lowering error')
 return rows

def evidence(inputs,report_path):
 proof=verify_adapted.verify(inputs,report_path)
 # This source-supply revision is bound to the existing complete166 pool, not
 # silently expanded by future authored inventory or pass flags.
 if proof['report_sha256']!='231a81fb8ce59cfebd5c1778bd07aa15479902d2114030f56cafd0f0e11cbf94' or len(proof['alternatives'])!=166:raise ValueError('unexpected adapted source cohort')
 sources={str(r['id']):(report_path.parent/r['path']).read_text() for r in proof['alternatives']}
 return proof,sources

def prepare(inputs,report_path,node_path,output):
 if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private supply must stay outside repository')
 proof,sources=evidence(inputs,report_path);rows=generate(sources,node_path)
 output.mkdir(parents=True,exist_ok=False)
 b.write(output/'lowering.json',rows)
 produced={};unsupported={}
 for pid,row in rows.items():
  if row['ok']:
   source=row['source'].encode();(output/(pid+'.js')).write_bytes(source);produced[pid]={'path':pid+'.js','sha256':b.sha(source),'bytes':len(source),'original_sha256':b.sha(sources[pid].encode()),'original_bytes':len(sources[pid].encode())}
  else:unsupported[pid]=row['error']
 contract={'schema':'gamma.direct-entry.supply.v1','ids':sorted(map(int,sources)),'cohort':166,'adapted_report':str(report_path),'adapted_report_sha256':proof['report_sha256'],'lowering_sha256':b.sha(b.encoded(rows)),'sources':produced,'unsupported':unsupported,'code_sha256':pins(),'protected_access':False,'m1_qualified':False,'candidate_executions':0,'eligibility':'requires fresh isolated qualification and independent evidence replay'}
 b.write(output/'contract.json',contract);return contract

def load(inputs,prepared,node_path=None,regenerate=False):
 contract=json.loads((prepared/'contract.json').read_text())
 if contract.get('schema')!='gamma.direct-entry.supply.v1' or contract.get('code_sha256')!=pins() or contract.get('cohort')!=166 or contract.get('protected_access') is not False:raise ValueError('direct-entry supply contract drift')
 proof,originals=evidence(inputs,Path(contract['adapted_report']))
 if contract.get('ids')!=sorted(map(int,originals)) or contract.get('adapted_report_sha256')!=proof['report_sha256']:raise ValueError('source supply cohort drift')
 rows=json.loads((prepared/'lowering.json').read_text())
 if b.sha(b.encoded(rows))!=contract['lowering_sha256'] or set(rows)!=set(originals):raise ValueError('lowering evidence drift')
 if regenerate:
  if node_path is None:raise ValueError('trusted parser runtime required')
  if generate(originals,node_path)!=rows:raise ValueError('independent AST lowering regeneration differs')
 sources={};unsupported={}
 for pid,row in rows.items():
  if row['ok']:
   value=row['source'].encode();descriptor={'path':pid+'.js','sha256':b.sha(value),'bytes':len(value),'original_sha256':b.sha(originals[pid].encode()),'original_bytes':len(originals[pid].encode())}
   if contract['sources'].get(pid)!=descriptor or (prepared/(pid+'.js')).read_bytes()!=value:raise ValueError('exact lowered source drift')
   sources[int(pid)]=value
  else:unsupported[pid]=row['error']
 if set(contract['sources'])!={str(i) for i in sources} or contract.get('unsupported')!=unsupported or not sources:raise ValueError('incomplete source/unsupported accounting')
 return contract,dict(sorted(sources.items()))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--adapted-report',type=Path,required=True);p.add_argument('--node-path',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 c=prepare(a.inputs,a.adapted_report,a.node_path,a.output);print(json.dumps({'cohort':166,'produced':len(c['sources']),'unsupported':len(c['unsupported']),'candidate_executions':0,'m1_qualified':False}))
