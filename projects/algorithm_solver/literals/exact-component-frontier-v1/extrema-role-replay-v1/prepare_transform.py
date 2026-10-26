"""Prepare inert exact8 packet ONLY after externally pinned composite review."""
import argparse,hashlib,json,os
from pathlib import Path
import admission

def main(a):
 os.umask(0o077);accepted=admission.load(a.review,a.review_sha256);q=admission.original_owner;base=q.owner.pinned(q.owner.BASE,q.owner.BASE_SHA);_,_,read=q.context();variants=[]
 for audit in accepted['audits']:
  pid=audit['problem_id'];row=base['source_rows'][str(pid)+':original']
  if row['sha256']!=audit['source_sha256']:raise ValueError('exact original source admission')
  source=read(pid,row['path'],row['sha256']);variants.append({'key':str(pid)+':original','problem_id':str(pid),'source_sha256':row['sha256'],'source':source.decode()})
 if len(variants)!=8 or sum(len(v['source'].encode())for v in variants)!=1053:raise ValueError('exact8 source mass')
 a.output.mkdir(mode=0o700,parents=True,exist_ok=False);raw=q.b.encoded(accepted);(a.output/'admission.json').write_bytes(raw);packet=q.b.encoded({'schema':'gamma.extrema8.transform-input.v1','admission_sha256':q.b.sha(raw),'variants':variants});(a.output/'inputs.private.json').write_bytes(packet)
 q.b.write(a.output/'preparation.json',{'admission_sha256':q.b.sha(raw),'independent_review_sha256':a.review_sha256,'inputs_sha256':q.b.sha(packet),'source_opens_after_live_gates':8,'source_bytes':1053,'candidate_execution':False,'transformations':0})
 print(json.dumps({'admission_sha256':q.b.sha(raw),'inputs_sha256':q.b.sha(packet),'sources':8,'candidate_execution':False}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--review',type=Path,required=True);p.add_argument('--review-sha256',required=True);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
