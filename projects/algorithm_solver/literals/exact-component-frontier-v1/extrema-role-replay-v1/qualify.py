"""Exact eight admitted finite-scope original/format/role replay. Native execution only."""
import argparse,hashlib,json,math,os,signal,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;R4=HERE.parent;LIT=R4.parent
sys.path.insert(0,str(R4));sys.path.insert(0,str(LIT/'paired-authoring-v1'))
import run_js_global as owner
import baseline_replay as b
import admission
from projects.algorithm_solver.catalogue.public_batch_adapter import bounded_regular_read
def safe_read(path,maximum=4*1024**2):return bounded_regular_read(str(Path(path).absolute()),maximum_bytes=maximum)
IDS=[123,55,1014,1121,1375,1725,1732,2873]
LIMITS={'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1024**3,'max_output_bytes':4*1024**2}
NODE_ARGS=['--jitless','--single-threaded','--max-old-space-size=64','harness.cjs']
STOP=[]
def handler(signum,frame):STOP.append(signum)
def check(deadline,reserve=0):
 if STOP:raise RuntimeError('termination requested')
 if not math.isfinite(deadline) or time.monotonic()+reserve>=deadline:raise TimeoutError('absolute bounded replay deadline')
def pins():
 paths=[HERE/'qualify.py',HERE/'verify.py',HERE/'verify_transform_v2.py',Path(b.__file__),Path(b.host_judge.__file__),Path(b.sandbox.__file__),Path(b.pinned_runtime.__file__),LIT/'admission500-v1/qualify_rules.py',LIT/'admission500-v1/harness.cjs',LIT/'admission500-v1/harness-exact-integer.cjs']
 # Bind every already-imported repository module plus explicit dynamic loaders.
 # This is a code closure only; no source/case payload discovery or reads.
 repo=R4.parents[3]
 for module in list(sys.modules.values()):
  filename=getattr(module,'__file__',None)
  if filename:
   candidate=Path(filename).absolute()
   if candidate.is_relative_to(repo) and candidate.suffix=='.py':paths.append(candidate)
 paths.extend([Path(owner.__file__),Path(owner.f.__file__),Path(owner.f.seg.__file__),Path(owner.f.codec.__file__),Path(owner.f.base.__file__),LIT/'readable-joint-blocks-v1/transfer.py'])
 return {str(p):b.sha(p.read_bytes())for p in sorted(set(paths))}
def context():
 cfg=owner.pinned(owner.CONFIG,owner.CONFIG_SHA);g=cfg['source_access']['boundary_gate'];gate=owner.pinned(g['path'],g['sha256']);owner.KnownSpecService.from_config(owner.CONFIG,owner.CONFIG_SHA)
 transfer=b.module('extrema8_transfer',LIT/'readable-joint-blocks-v1/transfer.py')
 def authorized(pid):owner.boundary_policy.authorize_before_open('leetcode:'+str(pid),gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='source')
 def read(pid,path,digest):
  authorized(pid);path=Path(path);raw=transfer.read_relative(path.parent,path.name)
  if b.sha(raw)!=digest:raise ValueError('exact eight payload drift')
  return raw
 return transfer,authorized,read

def prepare(a):
 transfer,gate,read=context();spec,manifest=transfer.load_manifest();base=owner.pinned(owner.BASE,owner.BASE_SHA)
 auditraw=safe_read(a.case_audit);audit=json.loads(auditraw)
 accepted=admission.load(a.admission_review,a.admission_review_sha256)
 if b.sha(auditraw)!=admission.FIXED['case_audit'] or audit!=accepted['case_audit']:raise ValueError('trusted exact eight finite audit')
 admission_sha=b.sha(b.encoded(accepted))
 transform_verified=admission.read_pinned(a.transform_verification,a.transform_verification_sha256)
 if transform_verified.get('schema')!='gamma.extrema8.guarded-transform-verification.v1'or transform_verified.get('verified')is not True or transform_verified.get('sources')!=8 or transform_verified.get('variants')!=16 or transform_verified.get('qualified')!=0 or transform_verified.get('candidate_executions')!=0 or not transform_verified.get('cleanup_passed')or transform_verified.get('admission_sha256')!=admission_sha:raise ValueError('verified exact guarded native transform required')
 if audit['ids']!=IDS or audit['case_files_opened']!=8 or not all(x['all_args_numeric_JSON_arrays_scalars']for x in audit['rows']):raise ValueError('finite exact eight audit required')
 traw=safe_read(a.transformed/'transformations.json');transform=json.loads(traw)
 fraw=safe_read(a.formatted/'transformations.json');formatted=json.loads(fraw)
 if formatted['ids']!=list(map(str,IDS)) or formatted['candidate_executions']!=0 or formatted['qualified']!=0:raise ValueError('format control scope')
 if transform['ids']!=list(map(str,IDS)) or transform['candidate_executions']!=0 or transform['qualified']!=0:raise ValueError('parser transform manifest scope')
 if transform_verified['manifest_sha256']!={'format':b.sha(fraw),'role':b.sha(traw)}:raise ValueError('native verified exact transform manifests')
 reviewraw=safe_read(a.admission_review);review=accepted
 if transform.get('admission_sha256')!=admission_sha or formatted.get('admission_sha256')!=admission_sha:raise ValueError('transform manifests not bound to trusted composite admission')
 root=Path(base['source_rows']['123:original']['path']).parents[2]
 for pid in IDS:gate(pid)
 receipt=json.loads(transfer.read_relative(root,'transfer-receipt.json'));metadata_raw=transfer.read_relative(root,'population400/manifest.json')
 if receipt['manifest_sha256']!=manifest or receipt['filtered_metadata_sha256']!=b.sha(metadata_raw):raise ValueError('original filtered metadata commitment')
 metadata={x['id']:x for x in json.loads(metadata_raw)['rows']};rows=[]
 for pid in IDS:
  row=next(x for x in audit['rows']if x['problem_id']==pid);t=next(x for x in transform['rows']if x['problem_id']==str(pid));ad=next(x for x in review['audits']if int(x['problem_id'])==pid);original=base['source_rows'][str(pid)+':original']
  if t['original_sha256']!=original['sha256'] or ad['source_sha256']!=original['sha256'] or ad['cases_sha256']!=row['cases_sha256'] or ad['effects_sha256']!=row['effects_sha256'] or not all(ad.get(k)is True for k in ('independent_review','finite_contract_numeric_arguments','numeric_index_and_array_access_review','no_reflection_or_coercion','fresh_unmodified_intrinsics')):raise ValueError('exact independently reviewed source/domain/effect binding')
  files={x['kind']:x for x in spec['files']if x.get('id')==pid}
  if row['cases_sha256']!=files['cases']['sha256'] or row['original_baseline_sha256']!=files['baseline']['sha256']:raise ValueError('original manifest binding drift')
  cases=json.loads(read(pid,row['cases_path'],row['cases_sha256']));baseline=json.loads(read(pid,row['original_baseline_path'],row['original_baseline_sha256']))
  if len(cases)!=len(baseline) or len(cases)!=row['cases'] or len(cases)!=metadata[pid]['cases']:raise ValueError('full original case/effect denominator')
  ft=next(x for x in formatted['rows']if x['problem_id']==str(pid))
  if ft['original_sha256']!=original['sha256'] or ft['mode']!='format' or t['mode']!='role' or ft['changed_bindings']!=0:raise ValueError('matched pure formatting control')
  original_bytes=read(pid,original['path'],original['sha256']);role_bytes=read(pid,a.transformed/f'{pid}.js',t['role_sha256']);format_bytes=read(pid,a.formatted/f'{pid}.js',ft['format_sha256'])
  if len(format_bytes)!=ft['format_bytes'] or not ft['ast_verified'] or not ft['occurrence_resolution_verified'] or len(role_bytes)!=t['role_bytes'] or len(original_bytes)!=t['original_bytes'] or not t['ast_verified'] or not t['occurrence_resolution_verified']:raise ValueError('exact AST output identity')
  rows.append({'id':pid,'transport':metadata[pid]['transport'],'cases':len(cases),'calls_per_arm':(len(cases)+31)//32,'cases_path':row['cases_path'],'cases_sha256':row['cases_sha256'],'baseline_path':row['original_baseline_path'],'baseline_sha256':row['original_baseline_sha256'],'original':{'path':original['path'],'sha256':original['sha256'],'bytes':len(original_bytes)},'format':{'path':str((a.formatted/f'{pid}.js').resolve()),'sha256':ft['format_sha256'],'bytes':len(format_bytes)},'role':{'path':str((a.transformed/f'{pid}.js').resolve()),'sha256':t['role_sha256'],'bytes':len(role_bytes)},'typed_contract_sha256':row['typed_contract_sha256'],'effects_sha256':row['effects_sha256'],'runtime_sha256':row['runtime_sha256'],'semantic_owner':row['semantic_owner']})
 historical=json.loads((LIT/'name-search-v1/contract.json').read_bytes())['code_hashes']
 for n in ('harness.cjs','harness-exact-integer.cjs','qualify_rules.py'):
  if b.sha((LIT/'admission500-v1'/n).read_bytes())!=historical['admission500-v1/'+n]:raise ValueError('original harness/oracle drift')
 c={'schema':'gamma.extrema8-role-alignment.matched-freeze.v1','ids':IDS,'arms':['original','format','role'],'rows':rows,'cases_per_arm':sum(x['cases']for x in rows),'calls_per_arm':sum(x['calls_per_arm']for x in rows),'input_manifest_sha256':manifest,'source_pool_freeze_sha256':owner.BASE_SHA,'service_config':{'path':owner.CONFIG,'sha256':owner.CONFIG_SHA},'case_audit_sha256':b.sha(auditraw),'admission_review_sha256':b.sha(reviewraw),'admission_review_path':str(a.admission_review.resolve()),'transform_admission_sha256':admission_sha,'runtime_control_freeze_sha256':admission.RUNTIME_FREEZE,'transform_verification_path':str(a.transform_verification.resolve()),'transform_verification_sha256':a.transform_verification_sha256,'transform_manifest_sha256':b.sha(traw),'format_manifest_sha256':b.sha(fraw),'code_sha256':pins(),'runtime':b.pinned_runtime.freeze_runtime(a.node_path),'limits':LIMITS,'node_args':NODE_ARGS,'batch_cases':32,'work_wall_seconds':780,'supervisor_freeze_sha256':'06ac77aa8ec31cdb842c55ed1e5615e384eb83adc58944e57b2533e97da5c5b5','pass_rule':'Unchanged historical judge_case AND exact normalized historical typed result/args-before/args-after/alias/error parity for EVERY original case, all three matched arms','scope':'Exact eight finite admitted research contracts only; no normative promotion','fit_owners':300,'original_qualified_variants_retained':875,'automatic_promotion':False,'protected_access':False,'candidate_executions':0}
 if c['runtime']!=accepted['runtime']:raise ValueError('matched replay differs from attested fresh runtime')
 a.output.mkdir(mode=0o700,parents=True,exist_ok=False);b.write(a.output/'contract.json',c)
 print(json.dumps({'freeze_sha256':b.sha(b.encoded(c)),'cases_per_arm':c['cases_per_arm'],'calls_per_arm':c['calls_per_arm'],'total_calls':3*c['calls_per_arm']}))

def load_frozen(path,digest):
 raw=safe_read(path/'contract.json')
 if b.sha(raw)!=digest:raise ValueError('operator freeze pin')
 c=json.loads(raw)
 if c.get('service_config')!={'path':owner.CONFIG,'sha256':owner.CONFIG_SHA}:raise ValueError('exact service context drift')
 if [r.get('id')for r in c.get('rows',[])]!=IDS or c.get('protected_access')is not False or c.get('fit_owners')!=300 or c.get('original_qualified_variants_retained')!=875 or c.get('source_pool_freeze_sha256')!=owner.BASE_SHA:raise ValueError('exact research source/fit scope required')
 if c['ids']!=IDS or c['arms']!=['original','format','role'] or c['code_sha256']!=pins() or c['limits']!=LIMITS or c['node_args']!=NODE_ARGS or c['batch_cases']!=32 or c['work_wall_seconds']!=780:raise ValueError('frozen runtime/code/scope drift')
 accepted=admission.load(Path(c['admission_review_path']),c['admission_review_sha256'])
 if b.sha(b.encoded(accepted))!=c['transform_admission_sha256']or c['runtime']!=accepted['runtime']or c['runtime_control_freeze_sha256']!=admission.RUNTIME_FREEZE:raise ValueError('trusted admission/runtime chain drift')
 tv=admission.read_pinned(Path(c['transform_verification_path']),c['transform_verification_sha256'])
 if tv.get('verified')is not True or tv.get('admission_sha256')!=c['transform_admission_sha256']or tv.get('manifest_sha256')!={'format':c['format_manifest_sha256'],'role':c['transform_manifest_sha256']}:raise ValueError('native transform verification chain drift')
 transfer,gate,read=context();loaded={}
 for row in c['rows']:
  pid=row['id'];loaded[pid]={'cases':json.loads(read(pid,row['cases_path'],row['cases_sha256'])),'baseline':json.loads(read(pid,row['baseline_path'],row['baseline_sha256']))}
  for arm in c['arms']:loaded[pid][arm]=read(pid,row[arm]['path'],row[arm]['sha256'])
  if len(loaded[pid]['cases'])!=row['cases'] or len(loaded[pid]['baseline'])!=row['cases']:raise ValueError('frozen full cases drift')
 # Snapshot each actual harness once and verify the exact buffers later executed.
 loaded['_harnesses']={}
 for name in ('harness.cjs','harness-exact-integer.cjs'):
  hp=LIT/'admission500-v1'/name;raw=safe_read(hp)
  if b.sha(raw)!=c['code_sha256'][str(hp)]:raise ValueError('actual frozen harness byte drift')
  loaded['_harnesses'][name]=raw
 return c,loaded

def run(a):
 deadline=time.monotonic()+780;check(deadline);c,loaded=load_frozen(a.freeze,a.freeze_sha256);check(deadline)
 reviewraw=safe_read(a.review);review=json.loads(reviewraw)
 if review.get('freeze_sha256')!=a.freeze_sha256 or review.get('independent_review')is not True or review.get('root_execution_authorized')is not True or not review.get('reviewer'):raise ValueError('fresh independent/root replay review required')
 if b.pinned_runtime.freeze_runtime(a.node_path)!=c['runtime']:raise ValueError('runtime drift')
 rules=b.module('extrema8_original_rules',LIT/'admission500-v1/qualify_rules.py')
 a.output.mkdir(mode=0o700,parents=True,exist_ok=False);b.write(a.output/'contract.json',{'freeze':str(a.freeze.resolve()),'freeze_sha256':a.freeze_sha256,'review_sha256':b.sha(reviewraw),'schema':'gamma.extrema8-role-alignment.matched-run.v1','runtime':c['runtime'],'limits':LIMITS,'work_wall_seconds':780});(a.output/'review.json').write_bytes(reviewraw)
 report={'contract_sha256':b.sha((a.output/'contract.json').read_bytes()),'schema':'gamma.extrema8-role-alignment.matched-run.v1','status':'running','rows':[],'candidate_executions':0,'qualified_arms':0,'checks_passed':0,'automatic_promotion':False,'protected_access':False}
 try:
  for arm in c['arms']:
   for frozen in c['rows']:
    pid=frozen['id'];data=loaded[pid];row={'id':pid,'arm':arm,'source_sha256':frozen[arm]['sha256'],'cases':frozen['cases'],'calls':[],'failures':[],'checks_passed':0,'passed':False};report['rows'].append(row)
    harness_name='harness-exact-integer.cjs'if frozen['transport']=='exact-integer'else'harness.cjs';harness=loaded['_harnesses'][harness_name]
    for offset in range(0,len(data['cases']),32):
     check(deadline,8);batch=data['cases'][offset:offset+32];packet=b.encoded({'entry':'solve','calls':[{'args':b.tag(x['args'],pid==633)if frozen['transport']=='exact-integer'else x['args']}for x in batch]});stem=f'{arm}-{pid}-{offset}';call={'stem':stem,'status':'attempted','packet_sha256':b.sha(packet),'harness_sha256':b.sha(harness)};row['calls'].append(call);report['candidate_executions']+=1;b.write(a.output/'report.json',report);check(deadline,8)
     result=b.pinned_runtime.run_node(a.node_path,manifest=c['runtime'],files={'program.js':data[arm],'harness.cjs':harness,'inputs.json':packet},limits=b.sandbox.Limits(**LIMITS),node_args=NODE_ARGS)
     (a.output/(stem+'.stdout')).write_bytes(result.stdout);(a.output/(stem+'.stderr')).write_bytes(result.stderr);call.update(status='returned',exit_code=result.exit_code,timed_out=result.timed_out,output_limit_exceeded=result.output_limit_exceeded,stdout_sha256=b.sha(result.stdout),stderr_sha256=b.sha(result.stderr))
     try:
      if not result.ok:raise RuntimeError('native process failed')
      records=b.parse(result.stdout,len(batch))
      for index,(case,record)in enumerate(zip(batch,records)):
       valid,observed=rules.judge_case(case,record);parity=b.exact(observed,data['baseline'][offset+index]);row['checks_passed']+=int(valid and parity)
       if not(valid and parity):row['failures'].append({'case_index':offset+index,'oracle':valid,'historical_effect_type_parity':parity})
     except Exception as e:row['failures'].append({'offset':offset,'error_type':type(e).__name__})
     b.write(a.output/'report.json',report)
    row['passed']=row['checks_passed']==row['cases'] and not row['failures'];report['qualified_arms']+=int(row['passed']);report['checks_passed']+=row['checks_passed'];b.write(a.output/'report.json',report)
  report['status']='completed'
 except Exception as e:report['status']='stopped';report['error_type']=type(e).__name__
 finally:b.write(a.output/'report.json',report)
 print(json.dumps({k:report[k]for k in ('status','candidate_executions','qualified_arms','checks_passed')}))
 if report['status']!='completed' or report['qualified_arms']!=24:raise SystemExit(1)
if __name__=='__main__':
 os.umask(0o077)
 for sig in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):signal.signal(sig,handler)
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True);a=sub.add_parser('prepare')
 for n in ('case-audit','transformed','formatted','admission-review','transform-verification','node-path','output'):a.add_argument('--'+n,type=Path,required=True)
 a.add_argument('--admission-review-sha256',required=True)
 a.add_argument('--transform-verification-sha256',required=True)
 a=sub.add_parser('run')
 for n in ('freeze','review','node-path','output'):a.add_argument('--'+n,type=Path,required=True)
 a.add_argument('--freeze-sha256',required=True);a=p.parse_args();(prepare if a.command=='prepare'else run)(a)
