"""Source-only, pinned compact transformation of qualified direct-entry variants."""
import argparse,importlib.util,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'paired-authoring-v1'))
import baseline_replay as b
spec=importlib.util.spec_from_file_location('compact_parent_verifier',LIT/'direct-entry-v1/verify.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
REPORT=Path('/workspace/shared/gamma-dot-diagnostics/direct-entry-20261025-1551/report.json')
REPORT_HASH='e234e33790b63dfabbc4c8ef1b7aabe95d2568d8dd221195e97003773688689f'
NODE=Path('/workspace/shared/gamma-dot-diagnostics/node')
def pins():
 paths=[HERE/n for n in ('canonicalize.mjs','supply.py','qualify.py','verify.py','CONTRACT.md')]
 paths += [LIT/'role-canonical-v1'/n for n in ('parser.mjs','bindings.mjs')]
 paths += [LIT/'direct-entry-v1'/n for n in ('verify.py','qualify.py','supply.py')]
 return {str(p.relative_to(LIT)):b.sha(p.read_bytes()) for p in paths}
def originals(inputs,node):
 proof=prior.verify(inputs,REPORT,node_path=node,allow_failed=False)
 if proof['report_sha256']!=REPORT_HASH or proof['qualified']!=163:raise ValueError('qualified cohort changed')
 return {str(i):(REPORT.parent/f'{i}.js').read_text() for i in proof['eligible_ids']}
def generate(sources,node):
 r=subprocess.run([str(node),str(HERE/'canonicalize.mjs')],input=b.encoded({'sources':sources,'mode':'compact'}),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,check=True)
 rows=json.loads(r.stdout)
 if set(rows)!=set(sources):raise ValueError('transform cohort mismatch')
 for row in rows.values():
  if type(row.get('ok')) is not bool:raise ValueError('missing status')
  if row['ok'] and (row.get('mode')!='compact' or row.get('ast_verified') is not True or row.get('candidate_executions')!=0):raise ValueError('invalid transform proof')
 return rows
def prepare(inputs,node,output):
 sources=originals(inputs,node);rows=generate(sources,node);output.mkdir(parents=True,exist_ok=False);b.write(output/'transformations.json',rows)
 produced={};unsupported={}
 for pid,row in rows.items():
  if row['ok']:
   raw=row['source'].encode();(output/f'{pid}.js').write_bytes(raw);produced[pid]={'path':f'{pid}.js','sha256':b.sha(raw),'bytes':len(raw),'original_sha256':b.sha(sources[pid].encode()),'original_bytes':len(sources[pid].encode())}
  else:unsupported[pid]=row['error']
 c={'schema':'gamma.compact-variants.supply.v1','cohort':163,'ids':sorted(map(int,sources)),'sources':produced,'unsupported':unsupported,'transformations_sha256':b.sha(b.encoded(rows)),'parent_report_sha256':REPORT_HASH,'code_sha256':pins(),'protected_access':False,'m1_qualified':False,'candidate_executions':0};b.write(output/'contract.json',c);return c
def load(inputs,prepared,node_path=None,regenerate=False):
 c=json.loads((prepared/'contract.json').read_bytes())
 if c['schema']!='gamma.compact-variants.supply.v1' or c['code_sha256']!=pins() or c['cohort']!=163 or c['protected_access'] is not False:raise ValueError('compact contract drift')
 source=originals(inputs,node_path or NODE);rows=json.loads((prepared/'transformations.json').read_bytes())
 if c['ids']!=sorted(map(int,source)) or c['parent_report_sha256']!=REPORT_HASH or b.sha(b.encoded(rows))!=c['transformations_sha256'] or set(rows)!=set(source):raise ValueError('cohort/evidence drift')
 if regenerate and generate(source,node_path or NODE)!=rows:raise ValueError('transform regeneration differs')
 output={};unsupported={}
 for pid,row in rows.items():
  if not row['ok']:unsupported[pid]=row['error'];continue
  raw=row['source'].encode();expected={'path':f'{pid}.js','sha256':b.sha(raw),'bytes':len(raw),'original_sha256':b.sha(source[pid].encode()),'original_bytes':len(source[pid].encode())}
  if c['sources'].get(pid)!=expected or (prepared/f'{pid}.js').read_bytes()!=raw:raise ValueError('exact bytes changed')
  output[int(pid)]=raw
 if c['unsupported']!=unsupported or set(c['sources'])!={str(i) for i in output}:raise ValueError('missing accounting')
 return c,dict(sorted(output.items()))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--node',type=Path,default=NODE);p.add_argument('--output',type=Path,required=True);a=p.parse_args();c=prepare(a.inputs,a.node,a.output);print(json.dumps({'produced':len(c['sources']),'unsupported':len(c['unsupported']),'before_bytes':sum(r['original_bytes'] for r in c['sources'].values()),'after_bytes':sum(r['bytes'] for r in c['sources'].values())}))
