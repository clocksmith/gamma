"""Host-only full original/format/role typed-effect revalidation; no execution."""
import argparse,json
from pathlib import Path
import qualify as q

def verify(path):
 raw=q.safe_read(path);report=json.loads(raw);runraw=q.safe_read(path.parent/'contract.json');run=json.loads(runraw)
 if report.get('schema')!='gamma.six-role-alignment.matched-run.v1' or report.get('status')!='completed' or report.get('automatic_promotion')is not False or report.get('protected_access')is not False:raise ValueError('complete research report required')
 if report.get('contract_sha256')!=q.b.sha(runraw):raise ValueError('run contract binding mismatch')
 c,loaded=q.load_frozen(Path(run['freeze']),run['freeze_sha256']);reviewraw=q.safe_read(path.parent/'review.json');review=json.loads(reviewraw)
 if q.b.sha(reviewraw)!=run['review_sha256'] or review.get('freeze_sha256')!=run['freeze_sha256'] or review.get('independent_review')is not True or review.get('root_execution_authorized')is not True:raise ValueError('review chain drift')
 if run['runtime']!=c['runtime'] or run['limits']!=q.LIMITS or run['work_wall_seconds']!=540:raise ValueError('runtime scope drift')
 if [(r['arm'],r['id'])for r in report['rows']]!=[(arm,pid)for arm in c['arms']for pid in q.IDS]:raise ValueError('complete three-arm/six-source denominator')
 rules=q.b.module('six_role_verify_rules',q.LIT/'admission500-v1/qualify_rules.py');checks=calls=qualified=0;outcomes=[]
 for row in report['rows']:
  arm,pid=row['arm'],row['id'];frozen=next(r for r in c['rows']if r['id']==pid);data=loaded[pid];offsets=list(range(0,len(data['cases']),32))
  if row['source_sha256']!=frozen[arm]['sha256'] or row['cases']!=len(data['cases']) or len(row['calls'])!=len(offsets):raise ValueError('exact source/case/call identity')
  passed=0;failures=[]
  for offset,call in zip(offsets,row['calls']):
   stem=f'{arm}-{pid}-{offset}';batch=data['cases'][offset:offset+32]
   if call['stem']!=stem or call['status']!='returned' or type(call['exit_code'])is not int or type(call['timed_out'])is not bool or type(call['output_limit_exceeded'])is not bool:raise ValueError('complete call protocol')
   stdout=q.safe_read(path.parent/(stem+'.stdout'),4*1024**2);stderr=q.safe_read(path.parent/(stem+'.stderr'),4*1024**2)
   packet=q.b.encoded({'entry':'solve','calls':[{'args':q.b.tag(x['args'],pid==633)if frozen['transport']=='exact-integer'else x['args']}for x in batch]})
   if q.b.sha(stdout)!=call['stdout_sha256'] or q.b.sha(stderr)!=call['stderr_sha256'] or q.b.sha(packet)!=call['packet_sha256']:raise ValueError('raw observation/packet hash drift')
   calls+=1
   try:
    if call['exit_code']!=0 or call['timed_out'] or call['output_limit_exceeded']:raise RuntimeError('native process failed')
    records=q.b.parse(stdout,len(batch))
    for index,(case,record)in enumerate(zip(batch,records)):
     valid,observed=rules.judge_case(case,record);parity=q.b.exact(observed,data['baseline'][offset+index]);passed+=int(valid and parity)
     if not(valid and parity):failures.append({'case_index':offset+index,'oracle':valid,'historical_effect_type_parity':parity})
   except Exception as e:failures.append({'offset':offset,'error_type':type(e).__name__})
  good=passed==row['cases'] and not failures
  if row['checks_passed']!=passed or row['failures']!=failures or row['passed']is not good:raise ValueError('independent typed/effect parity differs')
  checks+=passed;qualified+=good;outcomes.append({'id':pid,'arm':arm,'source_sha256':row['source_sha256'],'cases':row['cases'],'passed':good})
 if (calls,checks,qualified)!=(report['candidate_executions'],report['checks_passed'],report['qualified_arms']):raise ValueError('aggregate independent counts differ')
 return {'schema':'gamma.six-role-alignment.matched-independent-verification.v1','verified':True,'report_sha256':q.b.sha(raw),'run_contract_sha256':q.b.sha(runraw),'freeze_sha256':run['freeze_sha256'],'review_sha256':q.b.sha(reviewraw),'isolated_executions':calls,'checks':checks,'qualified_arms':qualified,'outcomes':outcomes,'original_variants_retained':875,'fit_owners':300,'scope':'Finite original admitted typed return/mutation/alias parity only; exact research variants, not canonical replacement or normative promotion','automatic_promotion':False,'protected_access':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args();print(json.dumps(verify(a.report),sort_keys=True))
