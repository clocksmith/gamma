"""Link fresh qualified source choices without fitting or resetting vocabulary."""
import argparse,importlib.util,json,os
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent

def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

direct=module('supply_link_direct_verify',LIT/'direct-entry-v1/verify.py')
role=module('supply_link_role_verify',LIT/'role-canonical-v1/verify.py')
b=direct.replay.b

def add_variant(rows,owners,pid,source,kind,proof):
 owner=str(pid);raw=source.read_bytes();digest=b.sha(raw)
 for key,row in rows.items():
  if owners[key]==owner and row['sha256']==digest:return False
 key=owner+':'+kind+'-'+digest
 if key in rows:raise ValueError('source key collision')
 rows[key]={'label':kind+'-'+digest,'path':str(source),'sha256':digest,'bytes':len(raw),'evidence':proof['report'],'qualification_report_sha256':proof['report_sha256'],'all_helpers_and_adapters_in_complete_source':True}
 if kind=='direct-entry':rows[key]['adapter_bytes']=0
 owners[key]=owner;return True

def prepare(prior_path,inputs,direct_report,format_report,role_report,node_path,output):
 if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private source supply stays outside repository')
 old_raw=prior_path.read_bytes();old=json.loads(old_raw)
 if old.get('schema')!='gamma.incremental-composition-retirement.v2' or old.get('fit_population')!=300 or old.get('protected_access') is not False:raise ValueError('unsupported predecessor source freeze')
 core=LIT/'incremental-merge-v2'
 for name,h in old['code_sha256'].items():
  if b.sha((core/name).read_bytes())!=h:raise ValueError('frozen predecessor code drift')
 ids=set(old['fit_ids'])
 if len(ids)!=300 or set(old['families'])!=ids or set(old['references'])!=ids or set(old['owners'].values())!=ids:raise ValueError('predecessor family/population mismatch')
 rows={k:dict(v) for k,v in old['source_rows'].items()};owners=dict(old['owners']);references=dict(old['references']);families=dict(old['families'])
 for key,row in rows.items():
  if key not in owners or b.sha(Path(row['path']).read_bytes())!=row['sha256']:raise ValueError('prior exact qualified source drift')
 for pid,key in references.items():
  if key not in rows or owners[key]!=pid:raise ValueError('prior reference identity missing')
 evidence=[];added={};duplicates={}
 for kind,path,verifier in [('direct-entry',direct_report,direct),('format',format_report,role),('role',role_report,role)]:
  proof=verifier.verify(inputs,path,allow_failed=True,node_path=node_path)
  # Every source passed before this particular supply freeze. Later failed
  # cohorts cannot silently substitute for the explicitly approved population.
  if proof['failed_ids'] or proof['qualified']!=(163 if kind=='direct-entry' else 32):raise ValueError('incomplete expected new source qualification')
  contract=json.loads((path.parent/'contract.json').read_text())
  if kind!='direct-entry' and contract['mode']!=kind:raise ValueError('AST mode mismatch')
  item={'kind':kind,'report':str(path),'report_sha256':proof['report_sha256'],'qualified_ids':proof['eligible_ids'],'checks':proof['checks'],'executions':proof['executions']}
  evidence.append(item);added[kind]=0;duplicates[kind]=0
  for pid in proof['eligible_ids']:
   if str(pid) not in ids:raise ValueError('new source outside same fixed fit300')
   source=path.parent/f'{pid}.js'
   if add_variant(rows,owners,pid,source,kind,item):added[kind]+=1
   else:duplicates[kind]+=1
 if references!=old['references'] or families!=old['families'] or set(owners.values())!=ids:raise ValueError('source addition changed control or family identities')
 paths=[HERE/'prepare.py',HERE/'CONTRACT.md',LIT/'direct-entry-v1/verify.py',LIT/'direct-entry-v1/qualify.py',LIT/'direct-entry-v1/supply.py',LIT/'direct-entry-v1/lower.mjs',LIT/'direct-entry-v1/CONTRACT.md',LIT/'role-canonical-v1/verify.py',LIT/'role-canonical-v1/qualify.py',LIT/'role-canonical-v1/canonicalize.mjs',LIT/'role-canonical-v1/bindings.mjs',LIT/'role-canonical-v1/parser.mjs',LIT/'role-canonical-v1/FREEZE.md']
 result={'schema':'gamma.incremental-source-supply.v1','predecessor_contract':str(prior_path),'predecessor_contract_sha256':b.sha(old_raw),'predecessor_source_variants':len(old['source_rows']),'source_rows':rows,'owners':owners,'references':references,'families':families,'fit_ids':old['fit_ids'],'fit_population':300,'m1_population':500,'code_sha256':{os.path.relpath(p,LIT):b.sha(p.read_bytes()) for p in paths},'qualification':evidence,'added':added,'deduplicated':duplicates,'source_variants':len(rows),'vocabulary_policy':'no dictionary or fit produced; attach to a separately hash-bound latest accepted continuation state','candidate_executions':0,'protected_access':False,'validation_source_reads':0,'m1_qualified':False}
 output.mkdir(parents=True,exist_ok=False);b.write(output/'contract.json',result);return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prior-contract',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--direct-report',type=Path,required=True);p.add_argument('--format-report',type=Path,required=True);p.add_argument('--role-report',type=Path,required=True);p.add_argument('--node-path',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=prepare(a.prior_contract,a.inputs,a.direct_report,a.format_report,a.role_report,a.node_path,a.output)
 print(json.dumps({k:r[k] for k in ('source_variants','added','deduplicated','candidate_executions','m1_qualified')}))
