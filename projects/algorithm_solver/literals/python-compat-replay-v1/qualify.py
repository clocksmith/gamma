"""Source-frozen Python-only replay of authorized independent frozen cases."""
import argparse,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'paired-authoring-v1'))
import baseline_replay as b
from baseline_replay import sha,encoded,write,sandbox
RULES=b.module('python_frozen_rules',LIT/'admission500-v1/qualify_rules.py')
BLOCKED=set()

def pins():
    paths=[HERE/n for n in ('qualify.py','harness.py','verify.py','CONTRACT.md')]
    paths += [Path(b.__file__),Path(sandbox.__file__),Path(b.host_judge.__file__),LIT/'admission500-v1/qualify_rules.py']
    paths += [Path(b.host_judge.__file__).with_name(n) for n in ('declared_comparison.py','functional_semantics.py')]
    paths += [LIT/'readable-joint-blocks-v1/transfer.py']
    return {str(p.relative_to(LIT.parent)):sha(p.read_bytes()) for p in paths}

def compare(case,record,baseline):
    """Independent oracle plus explicit language-type/effect bridge."""
    if record.get('error') or baseline.get('error') or 'result' not in record:
        return False,False
    norm=RULES.normalize
    actual=norm(record['result']); expected=norm(case['expected'])
    kind=record.get('result_type'); old=baseline.get('result_type')
    if old=='boolean':typed=kind=='bool' and type(actual) is bool
    elif old=='string':typed=kind=='str' and type(actual) is str
    elif old=='bigint':typed=kind=='int' and type(actual) is int
    elif old=='number':typed=kind in ('int','float') and type(actual) in (int,float)
    elif old=='object':
        value=norm(baseline.get('result'))
        typed=(kind=='NoneType' and actual is None) if value is None else (type(actual)==type(value) and type(actual) in (list,dict) and kind not in ('tuple','set','generator','bool','int','float','str','NoneType'))
        if type(value) is dict and set(value) in ({'__list_node__'},{'__tree_node__'}):
            typed=typed and kind not in ('dict','list')
        elif type(value) is dict:typed=typed and kind=='dict'
        elif type(value) is list:typed=typed and kind=='list'
    else:typed=False
    if type(expected) is int and abs(expected)>2**53-1:
        typed=typed and kind=='int' and type(actual) is int
    valid=typed and bool(b.host_judge._matches(b.host_judge.FunctionalTest(args=case['args'],expected=expected,compare=case.get('compare','return')),{'result':actual}))
    parity=typed and all(k in record and k in baseline and b.exact(norm(record[k]),norm(baseline[k])) for k in ('result','args_before','args_after','alias_edges'))
    return bool(valid),bool(parity)

def freeze(output,source_root):
    spec,_=b.module('python_devval_transfer',LIT/'readable-joint-blocks-v1/transfer.py').load_manifest()
    manifest_raw=(source_root/'manifest.json').read_bytes();manifest=json.loads(manifest_raw)
    partition=manifest.get('partition');ids=manifest.get('ids')
    if partition not in ('dev_fit','dev_val') or type(ids) is not list or not ids or ids!=sorted(set(ids)) or not set(ids)<=set(spec['partition'][partition]):raise ValueError('compatibility subset outside permitted named partition')
    if manifest.get('schema')!='gamma.python.reference-compatibility.sources.v1' or manifest.get('protected_access') is not False or manifest.get('candidate_executions')!=0 or manifest.get('qualified')!=0 or manifest.get('evidence_class')!='extra-contract-reference-compatibility-probe' or manifest.get('normative_domain_resolved') is not False:raise ValueError('compatibility authoring scope/identity invalid')
    inventory={r['id']:r for r in manifest['sources']}
    if len(inventory)!=len(manifest['sources']) or set(inventory)!=set(ids):raise ValueError('incomplete source-only100 inventory')
    if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private source freeze required')
    sources={};payload={}
    for pid in ids:
        row=inventory[pid]
        if row['path']!=f'python/{pid:04}.py' or row['semantics_path']!=f'python/{pid:04}.semantics.json' or row['entry_point']!='solve':raise ValueError('noncanonical source path/entry')
        raw=(source_root/row['path']).read_bytes();sem=(source_root/row['semantics_path']).read_bytes();declaration=json.loads(sem)
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes'] or sha(sem)!=row['semantics_sha256'] or declaration.get('entry_point')!='solve' or declaration.get('problem_id')!=pid or declaration.get('language')!='python':raise ValueError('source/semantic identity drift')
        sources[str(pid)]={'path':f'{pid}.py','sha256':sha(raw),'bytes':len(raw),'semantics_sha256':sha(sem),'method':'solve','reference_source_sha256':row['reference_source_sha256']};payload[pid]=(raw,sem)
    contract={'schema':'gamma.python.compatibility-source-freeze.v1','ids':ids,'sources':sources,'code_sha256':pins(),'population':500,'permitted_population':400,'partition':partition,'authoring_manifest_sha256':sha(manifest_raw),'authoring_inputs':manifest.get('authoring_inputs',{}),'source_frozen_before_replay':True,'evidence_class':'extra-contract-reference-compatibility-probe','normative_domain_resolved':False,'dictionary_fitting_allowed':False,'protected_access':False,'m1_qualified':False}
    output.mkdir(parents=True,exist_ok=False)
    for pid,(raw,sem) in payload.items():(output/f'{pid}.py').write_bytes(raw);(output/f'{pid}.semantics.json').write_bytes(sem)
    (output/'authoring-manifest.json').write_bytes(manifest_raw);write(output/'contract.json',contract);return contract

def load_freeze(path):
    c=json.loads((path/'contract.json').read_bytes())
    if c.get('schema')!='gamma.python.compatibility-source-freeze.v1' or c.get('code_sha256')!=pins() or c.get('protected_access') is not False or c.get('m1_qualified') is not False:raise ValueError('source freeze/code drift')
    spec,_=b.module('python_scope',LIT/'readable-joint-blocks-v1/transfer.py').load_manifest()
    ids=c['ids']
    if c.get('partition') not in ('dev_fit','dev_val'):raise ValueError('invalid compatibility partition')
    if not ids or len(ids)!=len(set(ids)) or not set(ids)<=set(spec['partition'][c['partition']]) or set(c['sources'])!={str(i) for i in ids}:raise ValueError('scope drift')
    if c.get('dictionary_fitting_allowed') is not False or c.get('source_frozen_before_replay') is not True or c.get('evidence_class')!='extra-contract-reference-compatibility-probe' or c.get('normative_domain_resolved') is not False or sha((path/'authoring-manifest.json').read_bytes())!=c['authoring_manifest_sha256']:raise ValueError('compatibility freeze boundary drift')
    authoring={r['id']:r for r in json.loads((path/'authoring-manifest.json').read_bytes())['sources']}
    if set(authoring)!=set(ids):raise ValueError('authoring population drift')
    sources={}
    for pid in ids:
        row=c['sources'][str(pid)];raw=(path/f'{pid}.py').read_bytes();sem=(path/f'{pid}.semantics.json').read_bytes()
        if row['path']!=f'{pid}.py' or sha(raw)!=row['sha256'] or len(raw)!=row['bytes'] or sha(sem)!=row['semantics_sha256'] or json.loads(sem)['entry_point'].split('.')[-1]!=row['method']:raise ValueError('source/entry drift')
        if row['sha256']!=authoring[pid]['sha256'] or row['semantics_sha256']!=authoring[pid]['semantics_sha256'] or row['reference_source_sha256']!=authoring[pid]['reference_source_sha256']:raise ValueError('authoring provenance drift')
        sources[pid]=raw
    return c,sources

def run(root,output,frozen,max_wall=1800):
    if not 1<=max_wall<=3600:raise ValueError('invalid wall budget')
    if output.resolve().is_relative_to(HERE.parents[3]):raise ValueError('private output outside repository required')
    sc,sources=load_freeze(frozen);loaded,hashes,mhash=b.load_inputs(root,sc['ids'])
    for pid,data in loaded.items():
        if sha(data['source'])!=sc['sources'][str(pid)]['reference_source_sha256']:raise ValueError('frozen reference provenance mismatch')
    output.mkdir(parents=True,exist_ok=False)
    contract={'schema':'gamma.python.compatibility-runtime-replay.v1','ids':sc['ids'],'source_freeze':str(frozen),'source_freeze_sha256':sha(encoded(sc)),'input_hashes':hashes,'input_manifest_sha256':mhash,'code_sha256':pins(),'python_runtime_sha256':sha(Path('/usr/bin/python3').read_bytes()),'batch_cases':32,'limits':{'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1024**3,'max_output_bytes':4*1024**2},'max_wall_seconds':max_wall,'protected_access':False,'m1_qualified':False,'population':500,'permitted_population':400}
    write(output/'contract.json',contract)
    report={'schema':contract['schema'],'contract_sha256':sha(encoded(contract)),'status':'running','rows':[],'candidate_executions':0,'qualified':0,'compatible':0,'normative_domain_resolved':False,'evidence_class':'extra-contract-reference-compatibility-probe','checks_passed':0,'m1_qualified':False,'protected_access':False};start=time.monotonic()
    try:
        for pid,data in loaded.items():
            cases=json.loads(data['cases']);base=json.loads(data['baseline'])
            if len(cases)!=len(base) or len(cases)!=data['metadata']['cases']:raise ValueError('case coverage mismatch')
            row={'id':pid,'cases':len(cases),'checks_passed':0,'passed':False,'failures':[],'calls':[]};report['rows'].append(row)
            if pid in BLOCKED:
                row['blocked']='unresolved alternative-domain contract';continue
            for offset in range(0,len(cases),32):
                if time.monotonic()-start>max_wall:raise TimeoutError('replay wall budget exceeded')
                batch=cases[offset:offset+32]
                if any(c.get('kwargs') or c.get('validator') or c.get('compare','return') not in ('return','return:unordered_outer') for c in batch):raise ValueError('unsupported case contract')
                result=sandbox.run(['/usr/bin/python3','-I','-S','harness.py'],files={'program.py':sources[pid],'harness.py':(HERE/'harness.py').read_bytes(),'inputs.json':encoded({'method':sc['sources'][str(pid)]['method'],'calls':[{'args':c['args']} for c in batch]})},limits=sandbox.Limits(**contract['limits']))
                report['candidate_executions']+=1;stem=f'{pid}-{offset}'
                (output/(stem+'.stdout')).write_bytes(result.stdout);(output/(stem+'.stderr')).write_bytes(result.stderr)
                row['calls'].append({'stem':stem,'exit_code':result.exit_code,'timed_out':result.timed_out,'output_limit_exceeded':result.output_limit_exceeded,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr)})
                count,failures=check_batch(batch,base[offset:offset+32],row['calls'][-1],result.stdout,offset)
                row['checks_passed']+=count;row['failures'].extend(failures)
            row['passed']=row['checks_passed']==len(cases) and not row['failures'];report['compatible']+=int(row['passed']);report['checks_passed']+=row['checks_passed'];write(output/'report.json',report)
            print(json.dumps({k:row[k] for k in ('id','passed','cases','checks_passed')}),flush=True)
        report['status']='completed'
    except Exception as error:report['status']='blocked' if isinstance(error,sandbox.SandboxUnavailable) else 'failed';report['error']=type(error).__name__+': '+str(error)
    finally:report['elapsed_seconds']=time.monotonic()-start;write(output/'report.json',report)
    return report

def check_batch(cases,baseline,call,stdout,offset):
    count=0;failures=[]
    try:
        if call['exit_code']!=0 or call['timed_out'] or call['output_limit_exceeded']:raise RuntimeError('sandbox process failed')
        records=b.parse(stdout,len(cases))
        for i,(case,record,base) in enumerate(zip(cases,records,baseline)):
            valid,parity=compare(case,record,base);count+=int(valid and parity)
            if not valid or not parity:failures.append({'case_index':offset+i,'oracle':valid,'effect_type_parity':parity,'error':record.get('error')})
    except Exception as error:failures.append({'offset':offset,'execution_or_protocol':type(error).__name__+': '+str(error)})
    return count,failures

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--sources',type=Path,required=True)
    r=sub.add_parser('run');r.add_argument('--inputs',type=Path,required=True);r.add_argument('--freeze',type=Path,required=True);r.add_argument('--max-wall',type=int,default=1800)
    for x in (f,r):x.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='freeze':print(json.dumps({'frozen_ids':freeze(a.output,a.sources)['ids']}))
    else:
        result=run(a.inputs,a.output,a.freeze,a.max_wall);print(json.dumps({k:result[k] for k in ('status','compatible','qualified','checks_passed','candidate_executions')}));raise SystemExit(0 if result['status']=='completed' else 2)
