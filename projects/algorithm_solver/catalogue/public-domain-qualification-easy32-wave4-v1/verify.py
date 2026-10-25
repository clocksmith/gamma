"""Host-only independent revalidation of every public-domain observation."""
import argparse,json
from pathlib import Path
import qualify as q

def verify(report_path):
 raw=report_path.read_bytes();r=json.loads(raw);cr=(report_path.parent/'contract.json').read_bytes();run=json.loads(cr)
 if r.get('schema')!='gamma.public-domain.foundation-easy32-wave4-run.v1'or r.get('status')!='completed'or r.get('contract_sha256')!=q.sha(cr)or r.get('protected_access')is not False or r.get('automatic_promotion')is not False:raise ValueError('invalid completed report')
 freeze=Path(run['freeze']);c,cases,sources=q.load_freeze(freeze);fraw=(freeze/'contract.json').read_bytes();review=(report_path.parent/'review.json').read_bytes()
 if run['freeze_sha256']!=q.sha(fraw)or run['review_sha256']!=q.sha(review):raise ValueError('freeze/review identity mismatch')
 q.review_check(fraw,json.loads(review))
 if run['runtime']!=c['node_runtime']or run['python_runtime_sha256']!=c['python_runtime_sha256']or run['limits']!=q.LIMITS:raise ValueError('runtime/isolation identity mismatch')
 expected_pairs=[(language,pid)for language in c['languages']for pid in q.IDS]
 if [(row['language'],row['id'])for row in r['rows']]!=expected_pairs:raise ValueError('source-language denominator drift')
 checks=calls=passed=0;outcomes=[]
 for row in r['rows']:
  language,pid=row['language'],row['id'];data=cases[str(pid)]
  if row['cases']!=len(data)or row['source_sha256']!=c['sources'][f'{language}:{pid}']['sha256']:raise ValueError('case/source drift')
  segments=list(q.batches(data));offsets=[x[0]for x in segments]
  if len(row['calls'])!=len(offsets):raise ValueError('execution coverage incomplete')
  count=0;failures=[]
  for (offset,batch),call in zip(segments,row['calls']):
   stem=f'{language}-{pid}-{offset}'
   if call['stem']!=stem or type(call['exit_code'])is not int or type(call['timed_out'])is not bool or type(call['output_limit_exceeded'])is not bool:raise ValueError('call metadata invalid')
   stdout=(report_path.parent/(stem+'.stdout')).read_bytes();stderr=(report_path.parent/(stem+'.stderr')).read_bytes()
   if q.sha(stdout)!=call['stdout_sha256']or q.sha(stderr)!=call['stderr_sha256']:raise ValueError('raw observation tamper')
   n,f=q.check_batch(pid,language,batch,call,stdout,offset);count+=n;failures+=f;calls+=1
  good=count==len(data)and not failures
  if row['passed']is not good or row['checks_passed']!=count or row['failures']!=failures:raise ValueError('independent public oracle replay differs')
  passed+=good;checks+=count;outcomes.append({'id':pid,'language':language,'passed':good,'cases':len(data),'source_sha256':row['source_sha256']})
 if r['passed_source_language_pairs']!=passed or r['checks_passed']!=checks or r['candidate_executions']!=calls:raise ValueError('aggregate observation mismatch')
 return {'schema':'gamma.public-domain.foundation-easy32-wave4-independent-verification.v1','verified':True,'report_sha256':q.sha(raw),'freeze_sha256':q.sha(fraw),'review_sha256':q.sha(review),'outcomes':outcomes,'passed_source_language_pairs':passed,'checks':checks,'isolated_executions':calls,'evidence_scope':'prospective public-domain finite output/type/local-effects qualification; pinned-statement-domain and explicit local read-only/fresh-return effects; no universal correctness proof','automatic_promotion':False,'historical_receipts_changed':False,'historical_m1_qualified':False,'protected_access':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args();print(json.dumps(verify(a.report),sort_keys=True))
