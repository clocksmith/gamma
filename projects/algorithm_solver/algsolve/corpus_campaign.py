"""Private normalization ledger. Never imports or executes candidates.

Legacy admission is metadata-only. The opt-in v2 public-order profile also
reads approved host-only test transcripts and rescores them without execution.

Receipt validation binds evidence, not truth: a responsible independent reviewer must
inspect the named artifacts. This ledger is not a solver, judge, or signature system.
"""
from __future__ import annotations
import argparse, collections, contextlib, datetime, fcntl, hashlib, json, os
from pathlib import Path
import tempfile, uuid, re

SCHEMA='algsolve.corpus-campaign.v1'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()

def file_ref(path):
    p=Path(path).resolve(strict=True)
    if not p.is_file(): raise ValueError('Artifact is not a file')
    return {'path':str(p),'sha256':sha_bytes(p.read_bytes())}

def verify(ref):
    if file_ref(ref['path'])['sha256']!=ref['sha256']: raise ValueError('Artifact hash changed: '+ref['path'])

def verify_source(ref):
    if ref is None: return
    if ref['kind']!='corpus-reference': verify(ref); return
    # Corpus producers put key first. Unsupported layouts fail closed rather
    # than decoding unrelated source/statement/example payloads to find a key.
    key=ref['key']
    if not isinstance(key,str) or re.fullmatch(r'[A-Za-z0-9_:./-]+',key) is None:
        raise ValueError('Unsupported approved source identity')
    prefix=re.compile(rb'^\s*\{\s*"key"\s*:\s*"([A-Za-z0-9_:./-]+)"\s*[,}]')
    def unique_fields(pairs):
        row={}
        for name,value in pairs:
            if name in row: raise ValueError('Duplicate JSON field in approved source record')
            row[name]=value
        return row
    found=False
    with Path(ref['path']).open('rb') as f:
        for line in f:
            match=prefix.match(line)
            if match is None or match[1].decode('ascii')!=key: continue
            if found: raise ValueError('Duplicate approved source identity')
            row=json.loads(line,object_pairs_hook=unique_fields)
            if row.get('key')!=key: raise ValueError('Approved source identity changed')
            references=row.get('references')
            if not isinstance(references,list) or not references:
                raise ValueError('Approved Python reference missing')
            candidate=next((x for x in references if x.get('validated')),references[0])
            if candidate['uid']!=ref['uid'] or sha_bytes(candidate['code'].encode())!=ref['sha256']:
                raise ValueError('Approved Python reference changed')
            found=True
    if not found: raise ValueError('Approved Python reference missing')

def save(path, data):
    path=Path(path)
    fd,name=tempfile.mkstemp(prefix=path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(data,f,indent=2,allow_nan=False); f.write('\n'); f.flush();os.fsync(f.fileno())
        os.replace(name,path)
        fd=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if os.path.exists(name):os.unlink(name)

@contextlib.contextmanager
def transaction(path, expected_revision):
    path=Path(path)
    with path.with_suffix(path.suffix+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        data=json.loads(path.read_text())
        if data['schema']!=SCHEMA: raise ValueError('Unknown ledger schema')
        if data['revision']!=expected_revision:raise ValueError('Stale ledger revision; reread status')
        if data.get('inputs',{}).get('reservations'):verify(data['inputs']['reservations'])
        yield data
        data['revision']+=1
        save(path,data)

def event(data,entry,action,owner,**details):
    entry['revision']+=1
    data['events'].append({'time':now(),'entry':f"{entry['id']:04d}:{entry['language']}",'action':action,'owner':owner,**details})

def owned(entry,owner,token):
    c=entry['claim']
    if not c or c['owner']!=owner or c['token']!=token: raise ValueError('Claim owner/token mismatch')

def claim(data,key,owner,allow_delivered=False):
    e=data['entries'][key]
    if not owner.strip():raise ValueError('Owner is required')
    if e['claim'] or e['status']=='complete':raise ValueError('Entry is already claimed or complete')
    reservation=e['reservation']
    if reservation and (reservation['state']!='delivered_reconciliation' or not allow_delivered):
        raise ValueError('External reservation preserved; delivered work needs explicit reconciliation flag')
    # Serialize the semantic family across languages/aliases to avoid competing edits.
    if any(x['claim'] and x['family']==e['family'] and x['claim']['owner']!=owner for x in data['entries'].values()):
        raise ValueError('Related family is already claimed by another owner')
    verify_source(e['source'])
    e['claim']={'owner':owner,'token':uuid.uuid4().hex,'time':now()}; e['status']='claimed'
    event(data,e,'claim',owner)
    return e['claim']

def snapshot(root,path):
    ref=file_ref(path);dest=Path(root)/'artifacts'/ref['sha256']
    dest.parent.mkdir(parents=True,exist_ok=True)
    content=Path(ref['path']).read_bytes()
    if sha_bytes(content)!=ref['sha256']:raise ValueError('Artifact changed while snapshotting')
    try:
        with dest.open('xb') as f:f.write(content);f.flush();os.fsync(f.fileno())
    except FileExistsError:
        if sha_bytes(dest.read_bytes())!=ref['sha256']:raise ValueError('Snapshot collision')
    return {'path':str(dest.resolve()),'sha256':ref['sha256'],'origin':ref['path']}

def stage(data,key,owner,token,normalized,contract,standard,root):
    e=data['entries'][key];owned(e,owner,token);verify_source(e['source'])
    if e['attempts'] and e['attempts'][-1]['status']=='staged':raise ValueError('Record or abandon current attempt first')
    c=json.loads(Path(contract).read_text())
    if c.get('schema') not in ('algsolve.campaign-contract.v1','algsolve.campaign-contract.v2','algsolve.campaign-contract.v3') or c.get('entry')!=key:raise ValueError('Wrong contract identity')
    source_sha=e['source']['sha256'] if e['source'] else None
    normalized_sha=file_ref(normalized)['sha256']
    if c.get('source_sha256')!=source_sha or c.get('normalized_sha256')!=normalized_sha:raise ValueError('Contract source binding mismatch')
    if c.get('independent_sets')!=e['independent_sets']:raise ValueError('Contract must preserve all frozen independent sets')
    from . import campaign_uint1024_dispatch as integer_profile
    runtime_refs=[]
    if c['schema']=='algsolve.campaign-contract.v3':
        from .campaign_public_contracts import requires_profile as requires_public_profile
        if requires_public_profile(data,e):raise ValueError('Combined public/runtime admission is unsupported')
        _,_,runtime_refs=integer_profile.profile(data,e,c)
        if file_ref(standard)['sha256']!=c['standard_sha256']:raise ValueError('Alternate runtime standard changed')
    else:
        integer_profile.reject_legacy(data,e,c)
        if c.get('interface')!='exact-public-adapter':raise ValueError('Interface contract weakened')
    profile_refs=[]
    if c['schema']=='algsolve.campaign-contract.v1':
        from .campaign_public_contracts import requires_profile
        if requires_profile(data,e):raise ValueError('Coordinator policy requires versioned public comparison admission')
        if c.get('comparison')!='unchanged' or any(k in c for k in ('public_comparison','independent_comparison')):raise ValueError('Legacy comparison contract changed')
    elif c['schema']=='algsolve.campaign-contract.v2':
        from .campaign_public_contracts import profile
        _,_,_,profile_refs=profile(data,e,c)
    if type(c.get('public_tests')) is not int or c['public_tests']<1:raise ValueError('Public example count required')
    if not c.get('mutation_contract') or not c.get('alias_contract'):raise ValueError('Mutation and alias contracts required')
    attempt={'number':len(e['attempts'])+1,'owner':owner,'created':now(),'status':'staged','source_sha256':source_sha,
             'normalized':snapshot(root,normalized),'contract':snapshot(root,contract),'standard':snapshot(root,standard),'receipts':[]}
    if runtime_refs:attempt['runtime_profile']=[snapshot(root,ref['path']) for ref in runtime_refs]
    if profile_refs:attempt['public_profile']=[snapshot(root,ref['path']) for ref in profile_refs]
    e['attempts'].append(attempt);e['status']='staged';event(data,e,'stage',owner,attempt=attempt['number'])
    return attempt

def receipt_check(receipt,attempt,key,kind):
    required={'schema':'algsolve.campaign-evidence.v1','entry':key,'kind':kind,
              'normalized_sha256':attempt['normalized']['sha256'],'contract_sha256':attempt['contract']['sha256'],
              'source_sha256':attempt['source_sha256'],'status':'passed'}
    if any(k not in receipt or receipt[k]!=v for k,v in required.items()):raise ValueError('Wrong or failed '+kind+' evidence binding')
    artifacts=receipt.get('artifacts')
    if not isinstance(artifacts,list) or not artifacts:raise ValueError('Evidence needs underlying artifacts')
    for ref in artifacts:verify(ref)

def record(data,key,owner,token,evidence_path,root):
    e=data['entries'][key];owned(e,owner,token);verify_source(e['source'])
    if not e['attempts'] or e['attempts'][-1]['status']!='staged':raise ValueError('No staged attempt')
    a=e['attempts'][-1]
    for field in ('normalized','contract','standard'):verify(a[field])
    bundle=json.loads(Path(evidence_path).read_text())
    if set(bundle)!= {'standard','execution','review'}:raise ValueError('Completion requires standard, execution and independent review receipts')
    receipts={}
    for kind,ref in bundle.items():
        verify(ref);receipt=json.loads(Path(ref['path']).read_text());receipt_check(receipt,a,key,kind);receipts[kind]=receipt
    c=json.loads(Path(a['contract']['path']).read_text())
    from . import campaign_uint1024_dispatch as integer_profile
    if c['schema']!='algsolve.campaign-contract.v3':integer_profile.reject_legacy(data,e,c,*receipts.values())
    st=receipts['standard']
    if st.get('standard_sha256')!=a['standard']['sha256'] or st.get('errors')!=[] or st.get('idempotent') is not True:
        raise ValueError('Standard checks failed or unbound')
    c=json.loads(Path(a['contract']['path']).read_text());execution=receipts['execution']
    expected=sum(t['tests'] for t in e['independent_sets'])
    if execution.get('independent_sets')!=e['independent_sets'] or execution.get('independent_total')!=expected or execution.get('independent_passed')!=expected:
        raise ValueError('Incomplete unchanged independent evidence')
    for field in ('independent_total','independent_passed','public_total','public_passed','infrastructure_errors'):
        if type(execution.get(field)) is not int:raise ValueError('Execution count must be an integer: '+field)
    for field in ('mutation_passed','alias_passed','sandboxed','expected_outputs_in_sandbox'):
        if type(execution.get(field)) is not bool:raise ValueError('Execution flag must be boolean: '+field)
    for field,value in {'public_total':c['public_tests'],'public_passed':c['public_tests'],'mutation_passed':True,'alias_passed':True,'sandboxed':True,'infrastructure_errors':0,'expected_outputs_in_sandbox':False}.items():
        if execution.get(field)!=value:raise ValueError('Execution evidence failed: '+field)
    review=receipts['review']
    if not review.get('reviewer') or review['reviewer']==a['owner'] or review.get('semantic_role_mapping_reviewed') is not True or review.get('complexity_reviewed') is not True or review.get('unresolved')!=[]:
        raise ValueError('Independent semantic/complexity review required')
    if c['schema']=='algsolve.campaign-contract.v3':
        if not integer_profile.distinct(review.get('reviewer'),a['owner']):raise ValueError('Independent named reviewer distinct from staging owner required')
        for ref in a.get('runtime_profile',[]):verify(ref)
        _,_,current_refs=integer_profile.profile(data,e,c)
        if [r['sha256'] for r in current_refs]!=[r['sha256'] for r in a.get('runtime_profile',[])]:raise ValueError('Staged exact integer policy changed')
        if st.get('runtime_profile')!=c['runtime_profile']:raise ValueError('Standard runtime profile mismatch')
        integer_profile.execution_profile(data,e,c,execution,review)
    elif c['schema']=='algsolve.campaign-contract.v2':
        from .campaign_public_contracts import execution_profile,profile
        for ref in a.get('public_profile',[]):verify(ref)
        _,_,_,current_refs=profile(data,e,c)
        if [r['sha256'] for r in current_refs]!=[r['sha256'] for r in a.get('public_profile',[])]:raise ValueError('Staged public policy changed')
        execution_profile(data,e,c,execution,review)
    else:
        from .campaign_public_contracts import requires_profile
        if requires_profile(data,e):raise ValueError('Coordinator policy requires versioned public comparison admission')
        if any(k in execution for k in ('public_comparison','semantic_qualification','independent_comparison')):
            raise ValueError('Semantic evidence cannot be relabeled legacy unchanged')
    # Preserve receipts and every underlying artifact by content hash, not just paths.
    frozen=[]
    for kind,ref in bundle.items():
        frozen.append({'kind':kind,'receipt':snapshot(root,ref['path']),'artifacts':[snapshot(root,x['path']) for x in receipts[kind]['artifacts']]})
    a.update(status='passed',receipts=frozen,finished=now());e['normalized']=a['normalized'];e['receipts']=frozen;e['status']='complete';e['blockers']=[];e['claim']=None
    event(data,e,'complete',owner,attempt=a['number'])

def fail(data,key,owner,token,evidence_path,reason,root):
    e=data['entries'][key];owned(e,owner,token)
    if not reason.strip():raise ValueError('Failure reason required')
    if not e['attempts'] or e['attempts'][-1]['status']!='staged':raise ValueError('No staged attempt')
    a=e['attempts'][-1]
    ref=snapshot(root,evidence_path)
    try:failure=json.loads(Path(evidence_path).read_text())
    except (ValueError,UnicodeError):failure={}
    preserved=[]
    if isinstance(failure,dict):
        for artifact in failure.get('artifacts',[]):
            verify(artifact);preserved.append(snapshot(root,artifact['path']))
    a.update(status='failed',failure_evidence=ref,failure_artifacts=preserved,reason=reason,finished=now())
    e['status']='blocked';e['blockers']=[reason];e['claim']=None
    event(data,e,'failed',owner,attempt=a['number'],reason=reason)


def release(data,key,owner,token,reason,blocked=False):
    e=data['entries'][key];owned(e,owner,token)
    if not reason.strip():raise ValueError('Release reason is required')
    if e['attempts'] and e['attempts'][-1]['status']=='staged':e['attempts'][-1].update(status='abandoned',reason=reason,finished=now())
    e['claim']=None;e['status']='blocked' if blocked else 'pending';e['blockers']=[reason] if blocked else []
    event(data,e,'release',owner,reason=reason)

def summary(data):
    entries=list(data['entries'].values())
    return {'revision':data['revision'],'eligible_problems':len({e['id'] for e in entries}),'entries':len(entries),'status':dict(collections.Counter(e['status'] for e in entries)),
            'baseline_qualified':dict(collections.Counter(e['language'] for e in entries if e['baseline'])),
            'normalized_complete':dict(collections.Counter(e['language'] for e in entries if e['status']=='complete')),
            'reservations':dict(collections.Counter(e['reservation']['state'] for e in entries if e['reservation']))}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ledger',type=Path,required=True)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('status');show=sub.add_parser('show');show.add_argument('entry')
    todo=sub.add_parser('next');todo.add_argument('--limit',type=int,default=10);todo.add_argument('--language',choices=['python','javascript']);todo.add_argument('--include-delivered',action='store_true')
    for name in ('claim','stage','record','release','fail'):
        s=sub.add_parser(name);s.add_argument('entry');s.add_argument('--owner',required=True);s.add_argument('--revision',required=True,type=int)
        if name!='claim':s.add_argument('--token',required=True)
        if name=='claim':s.add_argument('--reconcile-delivered',action='store_true')
        if name=='stage':
            for opt in ('normalized','contract','standard'):s.add_argument('--'+opt,required=True,type=Path)
        if name in ('record','fail'):s.add_argument('--evidence',type=Path,required=True)
        if name in ('release','fail'):s.add_argument('--reason',required=True)
        if name=='release':s.add_argument('--blocked',action='store_true')
    args=p.parse_args()
    try:
        if args.command in ('status','next','show'):
            data=json.loads(args.ledger.read_text())
            if args.command=='status':result=summary(data)
            elif args.command=='show':result=data['entries'][args.entry]
            else:
                result=[]
                for key,e in data['entries'].items():
                    if e['status']!='pending' or e['claim'] or (args.language and e['language']!=args.language):continue
                    if e['reservation'] and not(args.include_delivered and e['reservation']['state']=='delivered_reconciliation'):continue
                    if any(x['claim'] and x['family']==e['family'] for x in data['entries'].values()):continue
                    result.append({'entry':key,'baseline_qualified':bool(e['baseline']),'source_present':bool(e['source']),'reservation':e['reservation']})
                    if len(result)>=args.limit:break
        else:
            with transaction(args.ledger,args.revision) as data:
                if args.command=='claim':result=claim(data,args.entry,args.owner,args.reconcile_delivered)
                elif args.command=='stage':result=stage(data,args.entry,args.owner,args.token,args.normalized,args.contract,args.standard,args.ledger.parent)
                elif args.command=='record':record(data,args.entry,args.owner,args.token,args.evidence,args.ledger.parent);result={'status':'complete'}
                elif args.command=='fail':fail(data,args.entry,args.owner,args.token,args.evidence,args.reason,args.ledger.parent);result={'status':'blocked'}
                else:release(data,args.entry,args.owner,args.token,args.reason,args.blocked);result={'status':data['entries'][args.entry]['status']}
            result={**result,'ledger_revision':data['revision']}
        print(json.dumps(result,indent=2))
    except (ValueError,KeyError,OSError,json.JSONDecodeError) as exc:p.exit(2,str(exc)+'\n')
if __name__=='__main__':main()
