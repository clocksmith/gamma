"""Public intrinsic fixtures through unchanged approved isolated native judge."""
import argparse,hashlib,json,math,os,signal,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R4=HERE.parent;sys.path.insert(0,str(R4/'six-role-replay-v1'));import qualify as q
KEYS=('ordinary','signed_zero','nan','infinities','empty','argument_order','direct_descriptors','native_intrinsics','extrema_unchanged','iterator_identity','iterator_alias','iterator_holes','native_iterator')
HARNESSES=('harness.cjs','harness-exact-integer.cjs')
STOP=[]
def handler(s,f):STOP.append(s)
def check(deadline,reserve=0):
 if STOP or not math.isfinite(deadline)or time.monotonic()+reserve>=deadline:raise TimeoutError('bounded control deadline/cancel')
def pins():
 result=q.pins();result.update({str(p):q.b.sha(p.read_bytes())for p in(HERE/'control.py',HERE/'public-control.js')});return result
def packet():return q.b.encoded({'entry':'solve','calls':[{'args':[]}for _ in range(3)]})
def expected_observed():return {'result':dict.fromkeys(KEYS,True),'result_type':'object','args_before':[],'args_after':[],'alias_edges':[],'error':None}
def inspect(stdout):
 records=q.b.parse(stdout,3);rules=q.b.module('extrema_public_original_oracle',q.LIT/'admission500-v1/qualify_rules.py')
 for rec in records:
  ok,observed=rules.judge_case({'args':[],'expected':dict.fromkeys(KEYS,True)},rec)
  if not ok or not q.b.exact(observed,expected_observed()):raise ValueError('public control typed/effect mismatch')
 return len(records)
def load_freeze(path,digest):
 raw=q.safe_read(path);c=json.loads(raw)
 if q.b.sha(raw)!=digest or c['code_sha256']!=pins()or c['limits']!=q.LIMITS or c['node_args']!=q.NODE_ARGS or c['harnesses']!=list(HARNESSES)or c['packet_sha256']!=q.b.sha(packet()):raise ValueError('runtime control freeze mismatch')
 return c
def prepare(a):
 historical=json.loads((q.LIT/'name-search-v1/contract.json').read_bytes())['code_hashes']
 for name in (*HARNESSES,'qualify_rules.py'):
  if q.b.sha((q.LIT/'admission500-v1'/name).read_bytes())!=historical['admission500-v1/'+name]:raise ValueError('historical harness/oracle drift')
 c={'schema':'gamma.extrema-public-runtime-control.freeze.v1','code_sha256':pins(),'runtime':q.b.pinned_runtime.freeze_runtime(a.node_path),'limits':q.LIMITS,'node_args':q.NODE_ARGS,'harnesses':list(HARNESSES),'packet_sha256':q.b.sha(packet()),'public_fixture_sha256':q.b.sha((HERE/'public-control.js').read_bytes()),'calls':2,'checks':6,'flags_per_check':13,'work_wall_seconds':45,'corpus_access':False,'algorithm_admission':False,'supervisor_freeze_sha256':'06ac77aa8ec31cdb842c55ed1e5615e384eb83adc58944e57b2533e97da5c5b5'}
 a.output.mkdir(mode=0o700,parents=True,exist_ok=False);q.b.write(a.output/'contract.json',c);print(json.dumps({'freeze_sha256':q.b.sha(q.b.encoded(c))}))
def run(a):
 deadline=time.monotonic()+45;check(deadline);c=load_freeze(a.freeze,a.freeze_sha256);raw=q.safe_read(a.review);review=json.loads(raw)
 if review.get('freeze_sha256')!=a.freeze_sha256 or review.get('independent_review')is not True or review.get('root_execution_authorized')is not True:raise ValueError('independent/root control review required')
 if q.b.pinned_runtime.freeze_runtime(a.node_path)!=c['runtime']:raise ValueError('exact fresh runtime mismatch')
 a.output.mkdir(mode=0o700,parents=True,exist_ok=False);report={'schema':'gamma.extrema-public-runtime-control.result.v1','freeze_path':str(a.freeze),'freeze_sha256':a.freeze_sha256,'review_sha256':q.b.sha(raw),'status':'running','calls':[],'algorithm_admission':False,'corpus_access':False};(a.output/'review.json').write_bytes(raw)
 try:
  for i,name in enumerate(HARNESSES):
   check(deadline,8);call={'index':i,'harness':name,'status':'attempted'};report['calls'].append(call);q.b.write(a.output/'report.json',report)
   result=q.b.pinned_runtime.run_node(a.node_path,manifest=c['runtime'],files={'program.js':(HERE/'public-control.js').read_bytes(),'harness.cjs':(q.LIT/'admission500-v1'/name).read_bytes(),'inputs.json':packet()},limits=q.b.sandbox.Limits(**q.LIMITS),node_args=q.NODE_ARGS)
   (a.output/f'{i}.stdout').write_bytes(result.stdout);(a.output/f'{i}.stderr').write_bytes(result.stderr);call.update(status='returned',exit_code=result.exit_code,timed_out=result.timed_out,output_limit_exceeded=result.output_limit_exceeded,stdout_sha256=q.b.sha(result.stdout),stderr_sha256=q.b.sha(result.stderr))
   if not result.ok:raise ValueError('public native control failure')
   call['checks']=inspect(result.stdout);q.b.write(a.output/'report.json',report)
  report['status']='completed'
 except Exception as e:report['status']='failed';report['error_type']=type(e).__name__
 finally:q.b.write(a.output/'report.json',report)
 if report['status']!='completed':raise SystemExit(1)
 print(json.dumps({'status':'completed','calls':2,'checks':6,'algorithm_admission':False}))
def verify(a):
 raw=q.safe_read(a.report);r=json.loads(raw);c=load_freeze(Path(r['freeze_path']),r['freeze_sha256']);reviewraw=q.safe_read(a.report.parent/'review.json');review=json.loads(reviewraw)
 if r['status']!='completed'or r['corpus_access']is not False or r['algorithm_admission']is not False or len(r['calls'])!=2 or q.b.sha(reviewraw)!=r['review_sha256']or review.get('freeze_sha256')!=r['freeze_sha256']or review.get('independent_review')is not True or review.get('root_execution_authorized')is not True:raise ValueError('complete reviewed public control required')
 for i,call in enumerate(r['calls']):
  if call['index']!=i or call['harness']!=HARNESSES[i]or call['status']!='returned'or call['exit_code']!=0 or call['timed_out']or call['output_limit_exceeded']:raise ValueError('public control transport')
  out=q.safe_read(a.report.parent/f'{i}.stdout');err=q.safe_read(a.report.parent/f'{i}.stderr')
  if q.b.sha(out)!=call['stdout_sha256']or q.b.sha(err)!=call['stderr_sha256']or inspect(out)!=call['checks']:raise ValueError('public control raw verification')
 result={'schema':'gamma.extrema-public-runtime-control.verified.v1','verified':True,'report_sha256':q.b.sha(raw),'freeze_sha256':r['freeze_sha256'],'runtime':c['runtime'],'code_sha256':c['code_sha256'],'checks':6,'public_isolated_executions':2,'corpus_executions':0,'algorithm_admission':False,'scope':'Observed public intrinsic/iterator controls under two exact historical harnesses and pinned fresh runtime. Requires source-specific no-mutation/escape proof plus unchanged harness for composition, not arbitrary future-source guarantee.'};print(json.dumps(result,sort_keys=True))
if __name__=='__main__':
 os.umask(0o077)
 for s in(signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(s,handler)
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True);x=sub.add_parser('prepare');x.add_argument('--node-path',type=Path,required=True);x.add_argument('--output',type=Path,required=True)
 x=sub.add_parser('run')
 for n in('freeze','review','node-path','output'):x.add_argument('--'+n,type=Path,required=True)
 x.add_argument('--freeze-sha256',required=True);x=sub.add_parser('verify');x.add_argument('--report',type=Path,required=True);a=p.parse_args();{'prepare':prepare,'run':run,'verify':verify}[a.command](a)
