"""Host-only verifier for approved native parser probe stdout; no JS execution."""
import json,sys
from pathlib import Path
def verify(raw):
 def unique(pairs):
  out={}
  for k,v in pairs:
   if k in out:raise ValueError('duplicate key')
   out[k]=v
  return out
 rows=[json.loads(x,object_pairs_hook=unique)for x in raw.splitlines()]
 if len(rows)!=18 or rows[-1]!={'done':17}:raise ValueError('complete17control protocol required')
 expected=[('alpha_parameters',True),('swapped_references',False),('shadowed_blocks',True),('closure_capture',True),('capture_changed',False),('unresolved_global_changed',False),('unresolved_global_preserved',True)]
 for row,(name,value)in zip(rows[:7],expected):
  if row!={'kind':'mapping','name':name,'mapping_equal':value}:raise ValueError('mapping control failed: '+name)
 names=['numeric_loop','reflection_call','function_coercion','computed_name','getter','template','global_access','literal_api','callback']
 for row,name in zip(rows[7:16],names):
  if set(row)!={'kind','name','admitted','reasons'} or row['kind']!='subset' or row['name']!=name or row['admitted'] is not (name=='numeric_loop') or bool(row['reasons']) is (name=='numeric_loop'):raise ValueError('subset control failed: '+name)
 if rows[16]!={'kind':'alignment','aligned':True,'bad_hash_rejected':True,'missing_audit_rejected':True}:raise ValueError('alignment guard failure')
 return {'controls':17,'candidate_execution':False,'scope':'parser-only synthetic controls; no corpus admission/qualification'}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1]).read_bytes()),sort_keys=True))
