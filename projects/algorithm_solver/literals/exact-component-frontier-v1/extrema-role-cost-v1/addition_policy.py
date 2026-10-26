"""Source-hash deduplication and explicit storage accounting; no execution."""
import hashlib
sha=lambda text:hashlib.sha256(text.encode('utf8')).hexdigest()
def make_additions(texts,groups,qualified):
 existing={(pid,sha(texts[k]))for pid,keys in groups.items()for k in keys};out={'format':{},'role':{}};duplicates=[];seen=set()
 for arm,pid,text,digest in qualified:
  if arm not in out or pid not in groups or sha(text)!=digest or (arm,pid)in seen:raise ValueError('qualified owner/source identity')
  seen.add((arm,pid))
  if(pid,digest)in existing:
   duplicates.append({'problem_id':pid,'arm':arm,'sha256':digest});continue
  key=pid+':~extrema-'+arm+'-'+digest
  if not all(old<key for old in groups[pid]):raise ValueError('explicit stable old-source tie order')
  out[arm][pid]={'key':key,'source':text,'sha256':digest}
 return out,duplicates
def storage(texts,groups,additions):
 result={}
 for label,arms in(('original_pool',()),('plus_format',('format',)),('plus_role',('role',)),('plus_both',('format','role'))):
  values=list(texts.values())+[r['source']for a in arms for r in additions[a].values()];unique={sha(v):len(v.encode())for v in values}
  result[label]={'registry_source_entries':len(values),'registry_utf8_bytes':sum(len(v.encode())for v in values),'unique_content_blobs':len(unique),'unique_content_utf8_bytes':sum(unique.values()),'storage_scope':'Logical source registry vs hypothetical content-addressed deduplicated blobs; no storage rewrite performed.'}
 return result
