"""Metadata-only rejection mass. No source/case bytes opened, parsed or executed."""
import argparse, collections, hashlib, json, pathlib, stat
BASE=pathlib.Path('/workspace/shared/gamma-character-basis-freeze-20261025-1820/contract.json')
BASE_SHA='fdc0ba6f1c35a4231d9981fd2353ca3b51a394f61fa4021c8971f1cf060305ff'
LOG=pathlib.Path('/workspace/shared/gamma-current875-ast-inventory-20261025-2222/native-v3/worker.log')
LOG_SHA='30bfb5b2054751caeca1d2802abc23e1b104b205f65ea994645632b309177f96'
def pinned(p,d):
 raw=p.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=d:raise ValueError('metadata hash drift')
 return raw

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 base=json.loads(pinned(BASE,BASE_SHA));lines=[json.loads(s)for s in pinned(LOG,LOG_SHA).splitlines()];rows=[r for r in lines if 'key'in r]
 if len(rows)!=875 or len({r['key']for r in rows})!=875 or {r['key']for r in rows}!=set(base['source_rows']):raise ValueError('scope mismatch')
 sizes={};stat_only=0
 for key,r in base['source_rows'].items():
  path=pathlib.Path(r['path'])
  if any(q.is_symlink()for q in(path,*path.parents)):raise ValueError('metadata path symlink')
  st=path.stat()
  if not stat.S_ISREG(st.st_mode):raise ValueError('not regular')
  if 'bytes'in r and st.st_size!=r['bytes']:raise ValueError('pinned byte length drift')
  sizes[key]=st.st_size;stat_only+=int('bytes'not in r)
 if sum(sizes.values())!=379939:raise ValueError('independent fullpool source byte total drift')
 for r in rows:
  if r['source_sha256']!=base['source_rows'][r['key']]['sha256'] or r['problem_id']!=base['owners'][r['key']]:raise ValueError('AST/source identity mismatch')
 def agg(rs):return {'variants':len(rs),'owners':len({r['problem_id']for r in rs}),'source_bytes':sum(sizes[r['key']]for r in rs)}
 reasons=sorted({v for r in rows for v in r.get('rejection_reasons',[])})
 families=[dict(reason=k,**agg([r for r in rows if k in r.get('rejection_reasons',[])]))for k in reasons]
 combos=collections.defaultdict(list)
 for r in rows:combos[tuple(sorted(r.get('rejection_reasons',[])))].append(r)
 grouped=[dict(reasons=list(k),**agg(v))for k,v in combos.items()]
 removable={'unsupported_CallExpression','non_length_named_property','unresolved_global_reference'}
 potential=[r for r in rows if set(r.get('rejection_reasons',[])) and set(r['rejection_reasons'])<=removable]
 result={'schema':'gamma.ast-rejection-mass.v1','source_freeze_sha256':BASE_SHA,'native_v2_proof_inventory_sha256':LOG_SHA,'all_variants':agg(rows),'existing_research_candidates':agg([r for r in rows if r['research_candidate']]),'overlapping_rejection_families':sorted(families,key=lambda r:(-r['source_bytes'],r['reason'])),'disjoint_reason_combinations':sorted(grouped,key=lambda r:(-r['source_bytes'],r['reasons'])),'call_member_global_only_rejected_upper_bound':agg(potential),'call_member_global_only_and_current_index_proof_upper_bound':agg([r for r in potential if r['index_proof']['all_computed_indices_inductively_numeric']]),'source_size_provenance':{'freeze_bound_lengths':875-stat_only,'metadata_stat_only_lengths':stat_only,'source_payload_opens':0,'total_matches_independently_reproduced_cost_pool':True,'limitation':'297 lengths are current regular-file stat metadata, not a new content hash check; exact source hashes were checked in the separately reproduced current875 cost run.'},'interpretation':'Families overlap; disjoint combinations partition875. Call/member/global group is only an upper bound on further investigation, not admitted safe Math/local calls. No proof expansion or candidate execution.','M1':'UNMET'}
 a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('overlapping_rejection_families','disjoint_reason_combinations')}));print(json.dumps(result['overlapping_rejection_families'][:5]));print(json.dumps(result['disjoint_reason_combinations'][:5]))
if __name__=='__main__':main()
