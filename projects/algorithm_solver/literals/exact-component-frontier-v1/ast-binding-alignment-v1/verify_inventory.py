"""Host-only completeness/identity verifier; never opens source or case payloads."""
import argparse,collections,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));import run_js_global as owner
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def unique(items):
 out={}
 for k,v in items:
  if k in out:raise ValueError('duplicate field')
  out[k]=v
 return out

def verify(directory):
 freeze=json.loads((directory/'native-freeze-v2.json').read_bytes());supervisor=json.loads((directory/'native-v2/supervisor.json').read_bytes());resources=json.loads((directory/'resources-v2.json').read_bytes())
 if supervisor['exit_code']!=0 or supervisor['wall_timeout'] or supervisor['error_type'] or supervisor['termination_signals'] or not supervisor['no_executing_owned_processes_observed']:raise ValueError('native process/ownership failure')
 if resources['exit_code']!=0 or resources['peak_rss_KiB']>freeze['RSS_acceptance_max_KiB']:raise ValueError('process/RSS acceptance failed (RSS is not hard RAM cap)')
 rows=[json.loads(line,object_pairs_hook=unique)for line in (directory/'native-v2/worker.log').read_bytes().splitlines()]
 if len(rows)!=877 or rows[-1]!={'done':875,'fit_problems':300,'candidate_executions':0,'transformed_sources_produced':0,'qualification':False}:raise ValueError('complete875 protocol required')
 controls=rows[0]['numeric_index_controls'];names=['loop_counter','parameter_index','unknown_initializer','unknown_write','numeric_reassignment','preinitialization_read','mutual_numeric_invariant','unknown_dependency','literal_index'];wanted=[True,False,False,False,True,False,True,False,True]
 if controls!=[{'name':n,'observed':v,'expected':v}for n,v in zip(names,wanted)]:raise ValueError('numeric index controls failed')
 base=owner.pinned(owner.BASE,owner.BASE_SHA);variants=rows[1:-1]
 if [r['key']for r in variants]!=sorted(base['source_rows']) or {r['problem_id']for r in variants}!=set(base['references']):raise ValueError('fixed source/owner denominator mismatch')
 for r in variants:
  k=r['key']
  if r['source_sha256']!=base['source_rows'][k]['sha256'] or r['problem_id']!=base['owners'][k] or r['qualification']is not False:raise ValueError('row source identity/qualification drift')
  if 'parse_or_analysis_error' not in r:
   if type(r['static_subset'])is not bool or type(r['research_candidate'])is not bool or r['research_candidate']!=(r['static_subset'] and r['index_proof']['all_computed_indices_inductively_numeric']):raise ValueError('eligibility consistency failure')
   if r['index_proof']['all_computed_indices_inductively_numeric']!=all(x['proven_numeric']for x in r['index_proof']['indices']):raise ValueError('index proof consistency failure')
 selected=[r for r in variants if r['research_candidate']]
 return {'schema':'gamma.current875.ast-inventory-verification.v1','verified':True,'fit_problems':300,'variants':875,'parsed':sum('parse_or_analysis_error'not in r for r in variants),'static_subset_count':sum(r.get('static_subset',False)for r in variants),'research_candidates':len(selected),'research_candidate_owners':len({r['problem_id']for r in selected}),'numeric_index_controls':9,'rejection_counts':dict(collections.Counter(x for r in variants for x in r.get('rejection_reasons',[]))),'exact_candidates':[{'problem_id':r['problem_id'],'key':r['key'],'source_sha256':r['source_sha256'],'resolution_sha256':r['resolution_sha256'],'computed_index_occurrences':len(r['index_proof']['indices']),'numeric_binding_count':len(r['index_proof']['numeric_binding_ids'])}for r in selected],'input_packet_sha256':freeze['code_and_input_sha256'][str(directory/'inputs.private.json')],'native_freeze_sha256':sha(directory/'native-freeze-v2.json'),'native_log_sha256':sha(directory/'native-v2/worker.log'),'supervisor_sha256':sha(directory/'native-v2/supervisor.json'),'resources':resources,'source_pool_freeze_sha256':owner.BASE_SHA,'all_original_fallbacks_preserved':True,'candidate_execution':False,'transformed_sources':0,'independently_audited_admission':False,'qualification':False,'scope':'Synthetic/index static evidence only; exact-source independent numeric domain/no-reflection/effect audit remains required.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=verify(a.directory)
 if a.output.exists():raise ValueError('preserve prior result')
 a.output.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps({k:r[k]for k in ('verified','variants','parsed','research_candidates','static_subset_count','numeric_index_controls')}))
