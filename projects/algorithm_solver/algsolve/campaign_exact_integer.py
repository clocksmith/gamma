"""Coordinator-gated LC670 uint20 admission. Host replay only; no candidate imports.

Narrow first profile: JavaScript670 only. Decimal codecs below are trusted intake
validation, independently implemented rather than imported from author artifacts.
Legacy schemas cannot silently gain this alternate argument/result type contract.
"""
import dataclasses,hashlib,json,math,re,os,sys
from pathlib import Path
from algsolve import records,validate,values
from algsolve.judge import judge,sandbox,functional_semantics,declared_comparison
PROFILE='lc670-uint20-number-bigint-v1'
INTERFACE='exact-public-spelling:uint20-number-bigint.v1'
DOMAIN={'minimum':'0','maximum':'99999999999999999999','maximum_decimal_digits':20}
TAG='__gamma_uint_decimal_v1__'
SAFE=2**53-1
MAXIMUM=10**20-1
RUNTIME={name:Path(module.__file__).resolve() for name,module in {'records.py':records,'validate.py':validate,'values.py':values,'judge/judge.py':judge,'judge/sandbox.py':sandbox,'judge/functional_semantics.py':functional_semantics,'judge/declared_comparison.py':declared_comparison}.items()}
BINDINGS=('freeze','packet','host_tests','qualification','technical_review','number_failure','standard','runtime_contract','controls','evidence_index','toolchain_manifest','execution_seal','toolchain_before','toolchain_after_controls','toolchain_after')
RESERVED={'runtime_profile','runtime_profile_is_alternate','javascript_types','numeric_domain','exact_integer_qualification','alternate_runtime','codecs','harnesses','runtime','transport','numeric_domain','toolchain','execution_seal'}
def identity(value):return type(value) is str and bool(value.strip())
def distinct(left,right):return identity(left) and identity(right) and left.strip()!=right.strip()
def need(ok,message):
    if not ok:raise ValueError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ref(path):return {'path':str(Path(path).resolve()),'sha256':sha(path)}
def check(ref):
    need(type(ref) is dict and type(ref.get('path')) is str and sha(ref['path'])==ref.get('sha256'),'Exact integer artifact hash mismatch')
    return json.loads(Path(ref['path']).read_text())
def key(entry):return f"{entry['id']:04d}:{entry['language']}"
def requires_profile(data,entry):
    reference=data.get('inputs',{}).get('exact_integer_policy')
    if reference is None:return False
    policy=check(reference)
    need(policy.get('schema')=='algsolve.exact-integer-admission-policy.v1' and type(policy.get('entries')) is dict,'Wrong exact integer coordinator policy')
    return key(entry) in policy['entries']
def reject_legacy(data,entry,*documents):
    need(not requires_profile(data,entry),'Coordinator policy requires version3 exact integer admission; downgrade forbidden')
    for document in documents:
        need(not any(k in RESERVED or k.startswith('exact_integer_') or k.startswith('runtime_') or k.startswith('toolchain_') for k in document),'Legacy schema cannot carry alternate runtime evidence')
def profile(data,entry,contract):
    need(key(entry)=='0670:javascript' and entry['key']=='lc:maximum-swap','Only explicitly supported670JavaScript profile is implemented')
    need(contract.get('schema')=='algsolve.campaign-contract.v3' and contract.get('interface')==INTERFACE and contract.get('comparison')=='unchanged','Unsupported alternate runtime interface/comparison')
    need(not any(x in contract for x in ['public_comparison','independent_comparison']),'Combined comparison/runtime profiles are not supported')
    policy_ref=data.get('inputs',{}).get('exact_integer_policy');policy=check(policy_ref)
    need(policy.get('schema')=='algsolve.exact-integer-admission-policy.v1' and policy.get('status')=='approved','Coordinator runtime policy not approved')
    author=contract.get('source_author');approver=policy.get('approved_by')
    need(distinct(author,approver),'Independent coordinator runtime approval required')
    allowed=policy.get('entries',{}).get(key(entry));need(type(allowed) is dict,'Entry lacks explicit language-specific runtime policy')
    need(allowed.get('profile')==PROFILE and allowed.get('numeric_domain')==DOMAIN and allowed.get('source_author')==author,'Unsupported numeric domain/profile/author')
    need(allowed.get('normalized_sha256')==contract['normalized_sha256'],'Coordinator candidate hash differs')
    from . import campaign_toolchain
    need(allowed.get('admission_validator_sha256')==sha(Path(__file__)) and allowed.get('admission_toolchain_validator_sha256')==sha(Path(campaign_toolchain.__file__)),'Coordinator admission validator changed')
    need(contract.get('standard_sha256')==allowed['standard']['sha256'],'Contract standard differs from approved frozen policy')
    refs=[policy_ref];bound={}
    for name in BINDINGS:bound[name]=check(allowed.get(name));refs.append(allowed[name])
    runtime=allowed.get('runtime');need(type(runtime) is dict and set(runtime)==set(RUNTIME),'Missing trusted intake judge runtime')
    for name,path in RUNTIME.items():need(sha(path)==runtime[name],'Trusted exact integer judge runtime drift');refs.append(ref(path))
    packet=bound['packet'];need(packet.get('uid')=='lcd:670' and packet.get('source_id')=='670' and packet.get('entry')=={'class':'Solution','method':'maximumSwap'},'Wrong pinned670packet')
    need(len(entry['independent_sets'])==1 and entry['independent_sets'][0]['uid']==packet['uid'] and entry['independent_sets'][0]['path']==packet.get('hidden_tests_path') and packet.get('params')==[['num','int']],'Pinned packet test/interface identity mismatch')
    need(type(contract.get('public_tests')) is int and contract['public_tests']==len(packet['public_tests'])==2,'Public examples mismatch')
    frozen=bound['freeze'];need(frozen.get('schema')=='algsolve.exact-integer-toolchain-freeze.v2' and frozen.get('runtime_profile')==PROFILE and frozen.get('candidate_execution_started') is False and frozen.get('controls_execution_started') is False,'Missing pre-execution profile freeze')
    need(frozen.get('expected_outputs_in_sandbox') is False and frozen.get('limits')=={'parallelism':1,'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1073741824,'cases_per_chunk':1},'Freeze isolation/limits mismatch')
    folder=Path(allowed['freeze']['path']).parent.resolve();files=frozen.get('sources');need(type(files) is dict and bool(files),'Missing frozen profile sources')
    required=['codec.py','harness.cjs','harness.py','run.py','normalized/0670.js','normalized/0670.js.bindings.json','normalized/0670.js.semantics.json','contract.json','controls.json','checker-delta.json','policy.json','checker/corpus_standard.py','checker/corpus_standard_js.cjs']
    need(all(name in files for name in required),'Incomplete frozen codec/harness/checker/source profile')
    for rel,want in files.items():
        path=(folder/rel).resolve();need(path.is_relative_to(folder) and sha(path)==want,'Frozen exact integer file drift');refs.append(ref(path))
    for path,want in frozen.get('dependencies',{}).items():need(sha(path)==want,'Frozen runner dependency drift');refs.append(ref(path))
    need(files['normalized/0670.js']==contract['normalized_sha256'] and files['policy.json']==allowed['standard']['sha256'] and files['contract.json']==allowed['runtime_contract']['sha256'] and files['0670-packet.json']==allowed['packet']['sha256'],'Policy source/standard/contract/packet differs from execution freeze')
    runtime_contract=bound['runtime_contract'];need(runtime_contract.get('runtime_profile')==PROFILE and runtime_contract.get('domain')==DOMAIN and runtime_contract.get('independent_sets')==entry['independent_sets'],'Runtime domain/test contract mismatch')
    technical=bound['technical_review'];need(technical.get('schema')=='algsolve.exact-integer-profile-independent-review.v2' and technical.get('runtime_qualification_status')=='passed' and technical.get('runtime_profile')==PROFILE and technical.get('author')==author and distinct(technical.get('reviewer'),author),'Independent technical runtime review required')
    need(technical.get('freeze',{}).get('sha256')==allowed['freeze']['sha256'],'Technical review freeze mismatch')
    for name in ['controls','evidence_index','toolchain_manifest','execution_seal','toolchain_before','toolchain_after_controls','toolchain_after']:
        need(any(x.get('sha256')==allowed[name]['sha256'] and Path(x['path']).resolve()==Path(allowed[name]['path']).resolve() for x in technical.get('evidence',[])),'Control/transcript evidence not bound by independent technical review')
    index=bound['evidence_index'];need(index.get('schema')=='algsolve.hash-bound-evidence-index.v1' and index.get('freeze',{}).get('sha256')==allowed['freeze']['sha256'],'Wrong independently reviewed evidence index')
    reviewed_sources=technical.get('sources',[]);need(any(x.get('sha256')==contract['normalized_sha256'] for x in reviewed_sources),'Technical review does not bind candidate')
    for item in reviewed_sources+technical.get('evidence',[]):need(sha(item['path'])==item['sha256'],'Technical review artifact drift');refs.append(item)
    failure=bound['number_failure'];need(failure.get('entry')=='0670:javascript' and failure.get('status')=='blocked' and type(failure.get('cases')) is int and failure['cases']==121 and type(failure.get('passed')) is int and failure['passed']==118,'Original Number failure must remain explicit')
    need(failure.get('source',{}).get('sha256')!=contract['normalized_sha256'],'Alternate source incorrectly replaces predecessor identity')
    for item in [failure['source']]+failure.get('artifacts',[]):need(sha(item['path'])==item['sha256'],'Number predecessor evidence changed');refs.append(item)
    measured=campaign_toolchain.verify(bound['toolchain_manifest'])
    need(frozen.get('toolchain_manifest_sha256')==allowed['toolchain_manifest']['sha256'] and files.get('toolchain-manifest.json')==allowed['toolchain_manifest']['sha256'],'Manifest was not frozen before new execution')
    seal=bound['execution_seal'];need(seal.get('freeze_sha256')==allowed['freeze']['sha256'] and seal.get('toolchain_manifest_sha256')==allowed['toolchain_manifest']['sha256'] and seal.get('toolchain_before_sha256')==allowed['toolchain_before']['sha256'] and seal.get('cpu_affinity')==bound['toolchain_manifest']['serial_cpu_affinity'] and seal.get('expected_outputs_in_sandbox') is False,'Requalification seal/toolchain mismatch')
    for name in ['toolchain_before','toolchain_after_controls','toolchain_after']:
        proof=bound[name];need(proof.get('schema')=='algsolve.toolchain-verification.v1' and proof.get('passed') is True and proof.get('toolchain_manifest_sha256')==allowed['toolchain_manifest']['sha256'] and proof.get('host_interpreter_matches_sandbox_python') is True and proof.get('complete_dynamic_closure_claimed') is False,'Pre/post execution toolchain verification missing')
    refs += [{'path':item['path'],'sha256':item['sha256']} for item in measured]
    descriptor={'profile':PROFILE,'entry':key(entry),'numeric_domain':DOMAIN,'policy_sha256':policy_ref['sha256'],'bindings':{name:allowed[name]['sha256'] for name in BINDINGS},'runtime':runtime}
    need(contract.get('runtime_profile')==descriptor,'Contract runtime policy descriptor mismatch')
    return descriptor,bound,refs

def compact(value):return json.dumps(value,ensure_ascii=True,separators=(',',':'),allow_nan=False)
def integer(value):
    need(type(value) is dict and set(value)=={TAG} and type(value[TAG]) is str and re.fullmatch(r'(?:0|[1-9][0-9]{0,19})',value[TAG],flags=re.ASCII) is not None,'Malformed exact integer envelope')
    return int(value[TAG])
def decode_stdout(raw,case):
    need(type(raw) is str and len(raw.encode())<=4*1024**2,'Invalid raw transport size')
    lines=raw.splitlines();need(len(lines)==2,'Incomplete/extra raw result records');rows=[]
    for line in lines:
        row=json.loads(line);need(compact(row)==line,'Duplicate-key/noncanonical raw transport');rows.append(row)
    row,done=rows
    need(type(done) is dict and set(done)=={'done'} and type(done['done']) is int and done['done']==1,'Malformed done count')
    fields={'i','result','args_before','args_after','argument_runtime_types','result_runtime_type','input_object_count','returned_input_ids','input_node_values_preserved'}
    need(type(row) is dict and set(row)==fields and type(row['i']) is int and row['i']==0,'Malformed result fields/index')
    need(type(row['input_object_count']) is int and row['input_object_count']==0 and row['returned_input_ids']==[] and row['input_node_values_preserved'] is True,'Primitive alias observation failed')
    out=dict(row);out['result']=integer(row['result'])
    for name in ['args_before','args_after']:
        need(type(row[name]) is list and len(row[name])==1,'Wrong argument shape');out[name]=[integer(row[name][0])]
    need(type(case) is dict and not case.get('kwargs') and type(case.get('args')) is list and len(case['args'])==1 and type(case['args'][0]) is int and 0<=case['args'][0]<=MAXIMUM,'Case outside approveduint20domain')
    need(out['args_before']==case['args'] and out['args_after']==case['args'],'Exact argument binding/mutation failure')
    need(row['argument_runtime_types']==['number' if case['args'][0]<=SAFE else 'bigint'],'Wrong input runtime type')
    need(row['result_runtime_type'] in ['number','bigint'] and (row['result_runtime_type']!='number' or out['result']<=SAFE),'Unsafe/mislabeled result runtime type')
    # This670candidate is stricter than the transport: safe outputs returnNumber.
    need(row['result_runtime_type']==('number' if out['result']<=SAFE else 'bigint'),'670result type contract changed')
    return [out,done]

def controls_check(summary,fixture):
    host_names=['host-roundtrip-'+str(value) for value in fixture['roundtrip']]
    host_names += ['host-reject-'+repr(value) for value in [-1,MAXIMUM+1,True,False,None,1.0,'1']]
    host_names += ['host-'+name for name in ['duplicate-row-key','duplicate-envelope-key','noncanonical-observation','raw-result','bool-done','bool-index','unsafe-number-result','unsafe-number-argument','python-label-in-js','number-label-in-python','input-does-not-match-host','argument-mutated','safe-argument-bigint-label']]
    need(len(host_names)==len(set(host_names))==26 and [row.get('name') for row in summary.get('host_checks',[])]==host_names and all(row.get('passed') is True for row in summary['host_checks']),'Missing/duplicate host codec control identities')
    expected=[]
    for language in ['python','javascript']:
        expected += [(language,'roundtrip-'+str(value),'integer',value,value) for value in fixture['roundtrip']]
        expected += [(language,item['name'],'input-error',None,None) for item in fixture['malformed_inputs']]
        expected += [(language,'invalid-result-'+expression,'output-error',None,None) for expression in fixture['invalid_results'][language]]
        expected += [(language,name,'integer',fixture[name]['input'],fixture[name]['expected']) for name in ['official_swap','boundary_swap']]
    expected.append(('javascript','safe-bigint-output','safe-bigint',1,1))
    rows=summary.get('sandbox_controls',[]);need(len(rows)==len(expected)==96,'Incomplete per-control transcripts')
    for row,(language,name,kind,input_value,output_value) in zip(rows,expected):
        need(row.get('language')==language and row.get('name')==name and row.get('passed') is True and row.get('sandbox_ok') is True,'Control identity/status mismatch')
        need(type(row.get('exit_code')) is int and row['exit_code']==0 and row.get('signal') is None and row.get('timed_out') is False,'Control execution failure')
        wall=row.get('seconds');need(type(wall) in [int,float] and math.isfinite(wall) and 0<=wall<=8,'Control runtime bound failure')
        raw=row.get('stdout');need(type(raw) is str and len(raw.encode())<=4*1024**2,'Control transport missing');parsed=[]
        for line in raw.splitlines():
            item=json.loads(line);need(compact(item)==line,'Control noncanonical/duplicate transport');parsed.append(item)
        if kind=='input-error':
            need(len(parsed)==1 and parsed[0].get('load_error')=='input_validation' and 'SOURCE_EXECUTED' not in raw,'Malformed envelope reached candidate or was accepted')
        elif kind=='output-error':
            need(len(parsed)==2 and parsed[0].get('error')=='candidate_or_output' and parsed[1]=={'done':1} and type(parsed[1]['done']) is int,'Invalid result was accepted')
        else:
            need(len(parsed)==2 and parsed[1]=={'done':1} and type(parsed[1]['done']) is int,'Incomplete successful control')
            result=parsed[0];need(type(result.get('i')) is int and result['i']==0 and integer(result.get('result'))==output_value,'Control exact result mismatch')
            need(result.get('args_before')==[{TAG:str(input_value)}] and result.get('args_after')==[{TAG:str(input_value)}],'Control exact argument mismatch')
            input_type='int' if language=='python' else 'number' if input_value<=SAFE else 'bigint'
            output_type='int' if language=='python' else 'number' if output_value<=SAFE else 'bigint'
            if kind=='safe-bigint':output_type='bigint'
            need(result.get('argument_runtime_types')==[input_type] and result.get('result_runtime_type')==output_type,'Control runtime type mismatch')
            need(type(result.get('input_object_count')) is int and result['input_object_count']==0 and result.get('returned_input_ids')==[] and result.get('input_node_values_preserved') is True,'Control alias observation failed')

def execution_profile(data,entry,contract,execution,review):
    descriptor,bound,refs=profile(data,entry,contract)
    need(execution.get('runtime_profile')==descriptor and review.get('runtime_profile')==descriptor,'Execution/review runtime descriptor mismatch')
    need(review.get('runtime_profile_reviewed') is True and distinct(review.get('reviewer'),contract['source_author']) and review.get('runtime_qualification_sha256')==descriptor['bindings']['qualification'],'Independent admission review required')
    q=bound['qualification'];groups=bound['host_tests']
    need(q.get('schema')=='algsolve.exact-integer-admission-qualification.v2' and q.get('runtime_profile')==PROFILE and q.get('entry')==key(entry) and q.get('normalized_sha256')==contract['normalized_sha256'] and q.get('source_author')==contract['source_author'],'Qualification identity mismatch')
    for name in ['freeze','host_tests','controls','number_failure','technical_review','toolchain_manifest','execution_seal','toolchain_before','toolchain_after_controls','toolchain_after']:need(q.get(name+'_sha256')==descriptor['bindings'][name],'Qualification links mismatch')
    for name in ['expected_outputs_changed','comparisons_changed','expected_outputs_in_sandbox']:need(q.get(name) is False,'Qualification safety declaration mismatch')
    need(q.get('sandboxed') is True and q.get('preserve_prior_number_failure') is True,'Qualification isolation/predecessor declaration mismatch')
    names=['public']+['independent-'+s['uid'].replace(':','-') for s in entry['independent_sets']]
    need(type(groups) is list and [g.get('name') for g in groups]==names and len(set(names))==len(names),'Missing/duplicate test groups')
    need(digest(groups[0].get('tests'))==digest(bound['packet']['public_tests']),'Public tests/comparisons changed')
    for group,testset in zip(groups[1:],entry['independent_sets']):need(type(group.get('tests')) is list and len(group['tests'])==testset['tests'] and digest(group['tests'])==testset['sha256'],'Independent tests/comparisons changed')
    controls=bound['controls'];need(controls.get('toolchain_manifest_sha256')==descriptor['bindings']['toolchain_manifest'] and all(r.get('toolchain_manifest_sha256')==descriptor['bindings']['toolchain_manifest'] for r in controls.get('sandbox_controls',[])),'Controls lack pre-execution toolchain binding');need(controls.get('passed') is True and controls.get('host_count')==26 and controls.get('sandbox_count')==96,'Missing approved profile controls')
    need(len(controls.get('host_checks',[]))==26 and all(r.get('passed') is True for r in controls['host_checks']),'Host codec controls failed')
    need(len(controls.get('sandbox_controls',[]))==96 and all(r.get('passed') is True and r.get('sandbox_ok') is True for r in controls['sandbox_controls']),'Sandbox profile controls failed')
    policy=check(data['inputs']['exact_integer_policy']);freeze_path=policy['entries'][key(entry)]['freeze']['path']
    controls_check(controls,json.loads((Path(freeze_path).parent/'controls.json').read_text()))
    chunks=q.get('transcripts');need(type(chunks) is list and len(chunks)==sum(len(g['tests']) for g in groups),'Incomplete raw transcripts')
    reviewed={(str(Path(r['path']).resolve()),r['sha256']) for r in bound['evidence_index'].get('files',[])}
    need(all((str(Path(r['path']).resolve()),r['sha256']) in reviewed for r in chunks),'Raw transcript not bound by independent technical review')
    passed=public_passed=independent_passed=0;position=0
    for group in groups:
        for offset,case in enumerate(group['tests']):
            chunkref=chunks[position];position+=1;chunk=check(chunkref);refs.append(chunkref);r=chunk.get('receipt',{})
            need(r.get('toolchain_manifest_sha256')==descriptor['bindings']['toolchain_manifest'],'Result lacks measured toolchain binding')
            need(r.get('group')==group['name'] and type(r.get('offset')) is int and r['offset']==offset,'Duplicate/out-of-order observation chunk')
            need(r.get('sandbox_ok') is True and type(r.get('exit_code')) is int and r['exit_code']==0 and r.get('signal') is None and r.get('timed_out') is False and r.get('decode_error') is None and r.get('mutation_alias_ok') is True,'Failed execution flags')
            wall=r.get('seconds');need(type(wall) in [int,float] and math.isfinite(wall) and 0<=wall<=8,'Invalid wall time');need(type(r.get('stderr')) is str and len(r['stderr'].encode())<=4*1024**2 and type(r.get('notes')) is list,'Invalid stderr/notes')
            decoded=decode_stdout(r.get('stdout'),case);need(digest(decoded)==digest(chunk.get('decoded_observations')),'Saved decoded observations differ from raw tagged transport')
            payload=compact({'profile':PROFILE,'entry':'Solution.maximumSwap','calls':[{'args':[{TAG:str(case['args'][0])}]}]})
            need(hashlib.sha256(payload.encode()).hexdigest()==r.get('payload_sha256'),'Sandbox input payload differs from exact host input')
            # The pinned runner records result.ok, which includes !output_limit_exceeded;
            # reconstruction below is justified by that saved true flag, not a new run.
            result=sandbox.SandboxResult(exit_code=0,signal=None,stdout=('\n'.join(json.dumps(v) for v in decoded)+'\n').encode(),stderr=r['stderr'].encode(),wall_seconds=wall,timed_out=False,output_limit_exceeded=False,notes=r['notes'])
            verdict=judge._score_functional(result,validate.functional_tests([case]));need(verdict.passed and verdict.tests_passed==1 and verdict.to_dict()==r.get('verdict'),'Saved observation fails unchanged host judge or claimed score differs')
            passed+=1
            if group['name']=='public':public_passed+=1
            else:independent_passed+=1
    need(execution.get('public_passed')==public_passed and execution.get('independent_passed')==independent_passed and execution.get('decoding_errors')==0 and type(execution.get('decoding_errors')) is int,'Execution score/decode counts mismatch')
    declared=execution.get('artifacts',[])
    for item in refs:need(any(x.get('sha256')==item['sha256'] and Path(x['path']).resolve()==Path(item['path']).resolve() for x in declared),'Missing preserved runtime-profile artifact')
    return refs
