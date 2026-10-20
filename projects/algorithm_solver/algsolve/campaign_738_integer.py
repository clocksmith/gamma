"""Coordinator-gated LC738 uint1024 admission. Host replay only; no candidate imports.

Narrow first profile: JavaScript738 only. Decimal codecs below are trusted intake
validation, independently implemented rather than imported from author artifacts.
Legacy schemas cannot silently gain this alternate argument/result type contract.
"""
import dataclasses,hashlib,json,math,re,os,sys
from pathlib import Path
from algsolve import records,validate,values
from algsolve.judge import judge,sandbox,functional_semantics,declared_comparison
PROFILE='lc738-uint1024-number-bigint-v1'
INTERFACE='exact-public-spelling:uint1024-number-bigint.v1'
DOMAIN={'minimum':'0','maximum':'9'*1024,'maximum_decimal_digits':1024}
TAG='__gamma_uint_decimal_v1__'
SAFE=2**53-1
MAXIMUM=10**1024-1
RUNTIME={name:Path(module.__file__).resolve() for name,module in {'records.py':records,'validate.py':validate,'values.py':values,'judge/judge.py':judge,'judge/sandbox.py':sandbox,'judge/functional_semantics.py':functional_semantics,'judge/declared_comparison.py':declared_comparison}.items()}
BINDINGS=('freeze','packet','host_tests','qualification','technical_review','number_failure','standard','runtime_contract','controls','evidence_index','toolchain_manifest','execution_seal','toolchain_before','toolchain_after_controls','toolchain_after','reader_activation','reader_bindings','reader_after','approved_test_load','domain_classification','prior_uint20','summary','historical_reader')
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
    reference=data.get('inputs',{}).get('uint1024_policy')
    if reference is None:return False
    policy=check(reference)
    need(policy.get('schema')=='algsolve.uint1024-admission-policy.v1' and type(policy.get('entries')) is dict,'Wrong exact integer coordinator policy')
    return key(entry) in policy['entries']
def reject_legacy(data,entry,*documents):
    need(not requires_profile(data,entry),'Coordinator policy requires version3 exact integer admission; downgrade forbidden')
    for document in documents:
        need(not any(k in RESERVED or k.startswith('exact_integer_') or k.startswith('runtime_') or k.startswith('toolchain_') for k in document),'Legacy schema cannot carry alternate runtime evidence')
def profile(data,entry,contract):
    need(key(entry)=='0738:javascript' and entry['key']=='lc:monotone-increasing-digits','Only explicitly supported738JavaScript profile is implemented')
    need(contract.get('schema')=='algsolve.campaign-contract.v3' and contract.get('interface')==INTERFACE and contract.get('comparison')=='unchanged','Unsupported alternate runtime interface/comparison')
    need(not any(x in contract for x in ['public_comparison','independent_comparison']),'Combined comparison/runtime profiles are not supported')
    policy_ref=data.get('inputs',{}).get('uint1024_policy');policy=check(policy_ref)
    need(policy.get('schema')=='algsolve.uint1024-admission-policy.v1' and policy.get('status')=='approved','Coordinator runtime policy not approved')
    need(type(policy.get('entries')) is dict and set(policy['entries'])=={'0738:javascript'},'738 policy must contain only0738JavaScript')
    author=contract.get('source_author');approver=policy.get('approved_by')
    need(distinct(author,approver),'Independent coordinator runtime approval required')
    allowed=policy.get('entries',{}).get(key(entry));need(type(allowed) is dict,'Entry lacks explicit language-specific runtime policy')
    need(allowed.get('profile')==PROFILE and allowed.get('numeric_domain')==DOMAIN and allowed.get('source_author')==author,'Unsupported numeric domain/profile/author')
    need(allowed.get('normalized_sha256')==contract['normalized_sha256'],'Coordinator candidate hash differs')
    from . import campaign_toolchain,campaign_uint1024_dispatch,campaign_integer_dispatch,campaign_633_integer,campaign_exact_integer,corpus_campaign,campaign_868_dispatch,campaign_868_integer,campaign_868_transition
    modules={'campaign_868_dispatch.py':Path(campaign_868_dispatch.__file__),'campaign_868_integer.py':Path(campaign_868_integer.__file__),'campaign_868_transition.py':Path(campaign_868_transition.__file__),'campaign_868_replay.py':Path(__file__).with_name('campaign_868_replay.py'),'campaign_738_integer.py':Path(__file__),'campaign_uint1024_dispatch.py':Path(campaign_uint1024_dispatch.__file__),'campaign_integer_dispatch.py':Path(campaign_integer_dispatch.__file__),'campaign_633_integer.py':Path(campaign_633_integer.__file__),'campaign_exact_integer.py':Path(campaign_exact_integer.__file__),'campaign_toolchain.py':Path(campaign_toolchain.__file__),'corpus_campaign.py':Path(corpus_campaign.__file__)}
    need(allowed.get('admission_modules')=={n:sha(p) for n,p in modules.items()},'738 admission module identity drift')
    need(allowed.get('admission_validator_sha256')==sha(Path(__file__)) and allowed.get('admission_toolchain_validator_sha256')==sha(Path(campaign_toolchain.__file__)),'Coordinator admission validator changed')
    need(contract.get('standard_sha256')==allowed['standard']['sha256'],'Contract standard differs from approved frozen policy')
    refs=[policy_ref]+campaign_868_transition.validate(policy,allowed);bound={}
    for name in BINDINGS:bound[name]=check(allowed.get(name)) if name!='historical_reader' else Path(allowed[name]['path']).read_text();need(sha(allowed[name]['path'])==allowed[name]['sha256'],'738 binding drift');refs.append(allowed[name])
    runtime=allowed.get('runtime');need(type(runtime) is dict and set(runtime)==set(RUNTIME),'Missing trusted intake judge runtime')
    for name,path in RUNTIME.items():need(sha(path)==runtime[name],'Trusted exact integer judge runtime drift');refs.append(ref(path))
    packet=bound['packet'];need(packet.get('id')==738 and packet.get('key')==entry['key'] and packet.get('entry')=={'class':'Solution','method':'monotoneIncreasingDigits'},'Wrong pinned738packet')
    need(type(entry.get('independent_sets')) is list and len(entry['independent_sets'])==1 and entry['independent_sets']==packet.get('independent_test_sets') and packet.get('params')==[['n','int']],'Pinned packet test/interface identity mismatch')
    need(type(contract.get('public_tests')) is int and contract['public_tests']==len(packet['public_tests'])==3,'Public examples mismatch')
    frozen=bound['freeze'];need(frozen.get('schema')=='algsolve.exact-integer-toolchain-freeze.v2' and frozen.get('runtime_profile')==PROFILE and frozen.get('candidate_execution_started') is False and frozen.get('controls_execution_started') is False,'Missing pre-execution profile freeze')
    need(frozen.get('expected_outputs_in_sandbox') is False and frozen.get('limits')=={'parallelism':1,'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1073741824,'cases_per_chunk':1},'Freeze isolation/limits mismatch')
    folder=Path(allowed['freeze']['path']).parent.resolve();files=frozen.get('sources');need(type(files) is dict and bool(files),'Missing frozen profile sources')
    required=['codec.py','harness.cjs','harness.py','run.py','normalized/0738.js','normalized/0738.js.bindings.json','normalized/0738.js.semantics.json','contract.json','controls.json','checker-delta.json','policy.json','checker/corpus_standard.py','checker/corpus_standard_js.cjs']
    need(all(name in files for name in required),'Incomplete frozen codec/harness/checker/source profile')
    for rel,want in files.items():
        path=(folder/rel).resolve();need(path.is_relative_to(folder) and sha(path)==want,'Frozen exact integer file drift');refs.append(ref(path))
    for path,want in frozen.get('dependencies',{}).items():need(sha(path)==want,'Frozen runner dependency drift');refs.append(ref(path))
    need(files['normalized/0738.js']==contract['normalized_sha256'] and files['policy.json']==allowed['standard']['sha256'] and files['contract.json']==allowed['runtime_contract']['sha256'] and files['0738-packet.json']==allowed['packet']['sha256'],'Policy source/standard/contract/packet differs from execution freeze')
    runtime_contract=bound['runtime_contract'];need(runtime_contract.get('official_subset')=='0..1000000000' and runtime_contract.get('javascript_argument')=='Number if value<=9007199254740991, BigInt otherwise' and runtime_contract.get('transport_tag')==TAG,'738 runtime input contract differs');need(runtime_contract.get('runtime_profile')==PROFILE and runtime_contract.get('domain')==DOMAIN and runtime_contract.get('independent_sets')==entry['independent_sets'],'Runtime domain/test contract mismatch')
    technical=bound['technical_review'];need(technical.get('schema')=='algsolve.exact-integer-profile-independent-review.v2' and technical.get('runtime_qualification_status')=='passed' and technical.get('runtime_profile')==PROFILE and technical.get('author')==author and distinct(technical.get('reviewer'),author),'Independent technical runtime review required')
    need(technical.get('freeze',{}).get('sha256')==allowed['freeze']['sha256'],'Technical review freeze mismatch')
    for name in ['controls','evidence_index','toolchain_manifest','execution_seal','toolchain_before','toolchain_after_controls','toolchain_after']:
        need(any(x.get('sha256')==allowed[name]['sha256'] and Path(x['path']).resolve()==Path(allowed[name]['path']).resolve() for x in technical.get('evidence',[])),'Control/transcript evidence not bound by independent technical review')
    index=bound['evidence_index'];need(index.get('schema')=='algsolve.hash-bound-evidence-index.v1' and index.get('freeze',{}).get('sha256')==allowed['freeze']['sha256'],'Wrong independently reviewed evidence index')
    reviewed_sources=technical.get('sources',[]);need(any(x.get('sha256')==contract['normalized_sha256'] for x in reviewed_sources),'Technical review does not bind candidate')
    for item in reviewed_sources+technical.get('evidence',[]):need(sha(item['path'])==item['sha256'],'Technical review artifact drift');refs.append(item)
    failure=bound['number_failure'];need(failure.get('entry')=='0738:javascript' and type(failure.get('total_cases')) is int and failure['total_cases']==114 and type(failure.get('passed_cases')) is int and failure['passed_cases']==109,'Original Number failure must remain explicit')
    need(failure.get('normalized_sha256')!=contract['normalized_sha256'],'Alternate source incorrectly replaces predecessor identity')
    for item in [allowed['prior_source']]+failure.get('artifacts',[]):need(sha(item['path'])==item['sha256'],'Number predecessor evidence changed');refs.append(item)
    measured=campaign_toolchain.verify(bound['toolchain_manifest'])
    need(frozen.get('toolchain_manifest_sha256')==allowed['toolchain_manifest']['sha256'] and files.get('toolchain-manifest.json')==allowed['toolchain_manifest']['sha256'],'Manifest was not frozen before new execution')
    seal=bound['execution_seal'];need(seal.get('freeze_sha256')==allowed['freeze']['sha256'] and seal.get('toolchain_manifest_sha256')==allowed['toolchain_manifest']['sha256'] and seal.get('toolchain_before_sha256')==allowed['toolchain_before']['sha256'] and seal.get('cpu_affinity')==bound['toolchain_manifest']['serial_cpu_affinity'] and seal.get('expected_outputs_in_sandbox') is False,'Requalification seal/toolchain mismatch')
    for name in ['toolchain_before','toolchain_after_controls','toolchain_after']:
        proof=bound[name];need(proof.get('schema')=='algsolve.toolchain-verification.v1' and proof.get('passed') is True and proof.get('toolchain_manifest_sha256')==allowed['toolchain_manifest']['sha256'] and proof.get('host_interpreter_matches_sandbox_python') is True and proof.get('complete_dynamic_closure_claimed') is False,'Pre/post execution toolchain verification missing')
    refs += [{'path':item['path'],'sha256':item['sha256']} for item in measured]
    refs+=extra_profile_checks(bound,allowed,entry,contract,Path(corpus_campaign.__file__))
    descriptor={'profile':PROFILE,'entry':key(entry),'numeric_domain':DOMAIN,'policy_sha256':policy_ref['sha256'],'bindings':{name:allowed[name]['sha256'] for name in BINDINGS},'runtime':runtime}
    need(contract.get('runtime_profile')==descriptor,'Contract runtime policy descriptor mismatch')
    return descriptor,bound,refs

def compact(value):return json.dumps(value,ensure_ascii=True,separators=(',',':'),allow_nan=False)
def integer(value):
    need(type(value) is dict and set(value)=={TAG} and type(value[TAG]) is str and re.fullmatch(r'(?:0|[1-9][0-9]{0,1023})',value[TAG],flags=re.ASCII) is not None,'Malformed exact integer envelope')
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
    need(type(case) is dict and not case.get('kwargs') and type(case.get('args')) is list and len(case['args'])==1 and type(case['args'][0]) is int and 0<=case['args'][0]<=MAXIMUM,'Case outside approveduint1024domain')
    need(out['args_before']==case['args'] and out['args_after']==case['args'],'Exact argument binding/mutation failure')
    need(row['argument_runtime_types']==['number' if case['args'][0]<=SAFE else 'bigint'],'Wrong input runtime type')
    need(row['result_runtime_type'] in ['number','bigint'] and (row['result_runtime_type']!='number' or out['result']<=SAFE),'Unsafe/mislabeled result runtime type')
    # This738candidate is stricter than the transport: safe outputs returnNumber.
    need(row['result_runtime_type']==('number' if out['result']<=SAFE else 'bigint'),'738result type contract changed')
    return [out,done]

def controls_check(summary,fixture):
    host_names=['host-roundtrip-'+str(value) for value in fixture['roundtrip']]
    host_names += ['host-reject-'+repr(value) for value in [-1,MAXIMUM+1,True,False,None,1.0,'1']]
    host_names += ['host-'+name for name in ['duplicate-row-key','duplicate-envelope-key','noncanonical-observation','raw-result','bool-done','bool-index','unsafe-number-result','unsafe-number-argument','python-label-in-js','number-label-in-python','input-does-not-match-host','argument-mutated','safe-argument-bigint-label']]
    need(len(host_names)==len(set(host_names))==30 and [row.get('name') for row in summary.get('host_checks',[])]==host_names and all(row.get('passed') is True for row in summary['host_checks']),'Missing/duplicate host codec control identities')
    expected=[]
    for language in ['python','javascript']:
        expected += [(language,'roundtrip-'+str(value),'integer',value,value) for value in fixture['roundtrip']]
        expected += [(language,item['name'],'input-error',None,None) for item in fixture['malformed_inputs']]
        expected += [(language,'invalid-result-'+expression,'output-error',None,None) for expression in fixture['invalid_results'][language]]
        expected += [(language,name,'integer',fixture[name]['input'],fixture[name]['expected']) for name in ['official_swap','boundary_swap']]
        expected += [(language,item['name'],'integer',item['input'],item['expected']) for item in fixture['algorithm_boundaries']]
    expected.append(('javascript','safe-bigint-output','safe-bigint',1,1))
    rows=summary.get('sandbox_controls',[]);need(len(rows)==len(expected)==114,'Incomplete per-control transcripts')
    for row,(language,name,kind,input_value,output_value) in zip(rows,expected):
        need(row.get('language')==language and row.get('name')==name and row.get('passed') is True and row.get('sandbox_ok') is True,'Control identity/status mismatch')
        need(type(row.get('exit_code')) is int and row['exit_code']==0 and row.get('signal') is None and row.get('timed_out') is False,'Control execution failure')
        wall=row.get('seconds');need(type(wall) in [int,float] and math.isfinite(wall) and 0<=wall<=8,'Control runtime bound failure')
        raw=row.get('stdout');need(type(raw) is str and len(raw.encode())<=4*1024**2,'Control transport missing');parsed=[]
        for line in raw.splitlines():
            item=json.loads(line);need(compact(item)==line,'Control noncanonical/duplicate transport');parsed.append(item)
        need(type(row.get('stderr')) is str and 'SOURCE_EXECUTED' not in row['stderr'],'738 control executed sentinel')
        if kind=='input-error':
            need(len(parsed)==1 and type(parsed[0]) is dict and parsed[0].get('load_error')=='input_validation' and 'SOURCE_EXECUTED' not in raw,'Malformed envelope reached candidate or was accepted')
        elif kind=='output-error':
            need(len(parsed)==2 and type(parsed[0]) is dict and parsed[0].get('error')=='candidate_or_output' and 'result' not in parsed[0] and type(parsed[0].get('i')) is int and parsed[0]['i']==0 and parsed[1]=={'done':1} and type(parsed[1]['done']) is int,'Invalid result was accepted')
        else:
            need(len(parsed)==2 and parsed[1]=={'done':1} and type(parsed[1]['done']) is int,'Incomplete successful control')
            result=parsed[0];need(type(result.get('i')) is int and result['i']==0 and integer(result.get('result'))==output_value,'Control exact result mismatch')
            need(result.get('args_before')==[{TAG:str(input_value)}] and result.get('args_after')==[{TAG:str(input_value)}],'Control exact argument mismatch')
            input_type='int' if language=='python' else 'number' if input_value<=SAFE else 'bigint'
            output_type='int' if language=='python' else 'number' if output_value<=SAFE else 'bigint'
            if kind=='safe-bigint':output_type='bigint'
            need(result.get('argument_runtime_types')==[input_type] and result.get('result_runtime_type')==output_type,'Control runtime type mismatch')
            fields={'i','result','args_before','args_after','argument_runtime_types','result_runtime_type','input_object_count','returned_input_ids','input_node_values_preserved'}
            need(set(result)==fields,'738 successful control shape differs')
            decoded=[dict(result,result=output_value,args_before=[input_value],args_after=[input_value]),{'done':1}]
            need(digest(decoded)==digest(row.get('decoded')),'738 control raw and decoded observations differ')
            need(type(result.get('input_object_count')) is int and result['input_object_count']==0 and result.get('returned_input_ids')==[] and result.get('input_node_values_preserved') is True,'Control alias observation failed')

def execution_profile(data,entry,contract,execution,review):
    descriptor,bound,refs=profile(data,entry,contract)
    need(execution.get('runtime_profile')==descriptor and review.get('runtime_profile')==descriptor,'Execution/review runtime descriptor mismatch')
    need(review.get('runtime_profile_reviewed') is True and distinct(review.get('reviewer'),contract['source_author']) and review.get('runtime_qualification_sha256')==descriptor['bindings']['qualification'],'Independent admission review required')
    q=bound['qualification'];groups=bound['host_tests']
    names=['public']+['independent-'+s['uid'].replace(':','-') for s in entry['independent_sets']]
    need(type(groups) is list and [g.get('name') for g in groups]==names and len(set(names))==len(names),'Missing/duplicate test groups')
    need(digest(groups[0].get('tests'))==digest(bound['packet']['public_tests']),'Public tests/comparisons changed')
    for group,testset in zip(groups[1:],entry['independent_sets']):need(type(group.get('tests')) is list and len(group['tests'])==testset['tests'] and digest(group['tests'])==testset['sha256'],'Independent tests/comparisons changed')
    controls=bound['controls'];need(controls.get('toolchain_manifest_sha256')==descriptor['bindings']['toolchain_manifest'] and all(r.get('toolchain_manifest_sha256')==descriptor['bindings']['toolchain_manifest'] for r in controls.get('sandbox_controls',[])),'Controls lack pre-execution toolchain binding');need(controls.get('passed') is True and controls.get('host_count')==30 and controls.get('sandbox_count')==114,'Missing approved profile controls')
    need(len(controls.get('host_checks',[]))==30 and all(r.get('passed') is True for r in controls['host_checks']),'Host codec controls failed')
    need(len(controls.get('sandbox_controls',[]))==114 and all(r.get('passed') is True and r.get('sandbox_ok') is True for r in controls['sandbox_controls']),'Sandbox profile controls failed')
    policy=check(data['inputs']['uint1024_policy']);allowed=policy['entries'][key(entry)];freeze_path=allowed['freeze']['path']
    for row in controls['sandbox_controls']:runtime_observation(row,bound,allowed)
    controls_check(controls,json.loads((Path(freeze_path).parent/'controls.json').read_text()))
    folder=Path(allowed['freeze']['path']).parent
    index_by_path={str(Path(r['path']).resolve()):r for r in bound['evidence_index']['files']}
    chunks=[index_by_path.get(str((folder/'results'/f'0738-javascript-{g["name"]}-{i}.json').resolve())) for g in groups for i in range(len(g['tests']))]
    need(all(type(r) is dict for r in chunks),'738 named transcript missing')
    need(type(chunks) is list and len(chunks)==sum(len(g['tests']) for g in groups),'Incomplete raw transcripts')
    reviewed={(str(Path(r['path']).resolve()),r['sha256']) for r in bound['evidence_index'].get('files',[])}
    need(all((str(Path(r['path']).resolve()),r['sha256']) in reviewed for r in chunks),'Raw transcript not bound by independent technical review')
    passed=public_passed=independent_passed=0;position=0
    for group in groups:
        for offset,case in enumerate(group['tests']):
            chunkref=chunks[position];position+=1;chunk=check(chunkref);refs.append(chunkref);r=chunk.get('receipt',{});runtime_observation(r,bound,allowed)
            need(r.get('toolchain_manifest_sha256')==descriptor['bindings']['toolchain_manifest'],'Result lacks measured toolchain binding')
            need(r.get('group')==group['name'] and type(r.get('offset')) is int and r['offset']==offset,'Duplicate/out-of-order observation chunk')
            need(r.get('sandbox_ok') is True and type(r.get('exit_code')) is int and r['exit_code']==0 and r.get('signal') is None and r.get('timed_out') is False and r.get('decode_error') is None and r.get('mutation_alias_ok') is True,'Failed execution flags')
            wall=r.get('seconds');need(type(wall) in [int,float] and math.isfinite(wall) and 0<=wall<=8,'Invalid wall time');need(type(r.get('stderr')) is str and len(r['stderr'].encode())<=4*1024**2 and type(r.get('notes')) is list,'Invalid stderr/notes')
            need(type(case.get('expected')) is int and 0<=case['expected']<=MAXIMUM and case.get('compare','return')=='return','738 expected type/comparison outside exact contract')
            need(type(r.get('official_admissible')) is bool and r['official_admissible']==(0<=case['args'][0]<=1000000000),'738 official-domain marker differs')
            decoded=decode_stdout(r.get('stdout'),case);need(decoded[0]['result']==case['expected'],'738 exact result mismatch');need(digest(decoded)==digest(chunk.get('decoded_observations')),'Saved decoded observations differ from raw tagged transport')
            payload=compact({'profile':PROFILE,'entry':'Solution.monotoneIncreasingDigits','calls':[{'args':[{TAG:str(case['args'][0])}]}]})
            need(hashlib.sha256(payload.encode()).hexdigest()==r.get('payload_sha256'),'Sandbox input payload differs from exact host input')
            # The pinned runner records result.ok, which includes !output_limit_exceeded;
            # reconstruction below is justified by that saved true flag, not a new run.
            result=sandbox.SandboxResult(exit_code=0,signal=None,stdout=('\n'.join(json.dumps(v) for v in decoded)+'\n').encode(),stderr=r['stderr'].encode(),wall_seconds=wall,timed_out=False,output_limit_exceeded=False,notes=r['notes'])
            verdict=judge._score_functional(result,validate.functional_tests([case]));need(verdict.passed and verdict.tests_passed==1 and digest(verdict.to_dict())==digest(r.get('verdict')),'Saved observation fails unchanged host judge or claimed score differs')
            passed+=1
            if group['name']=='public':public_passed+=1
            else:independent_passed+=1
    need(execution.get('public_passed')==public_passed and execution.get('independent_passed')==independent_passed and execution.get('decoding_errors')==0 and type(execution.get('decoding_errors')) is int,'Execution score/decode counts mismatch')
    extra_execution_checks(bound,allowed,execution,refs)
    declared=execution.get('artifacts',[])
    for item in refs:need(any(x.get('sha256')==item['sha256'] and Path(x['path']).resolve()==Path(item['path']).resolve() for x in declared),'Missing preserved runtime-profile artifact')
    return refs

# These checks expand only the738 boundary; shared670/633 files stay unchanged.
def count(value,want,message):need(type(value) is int and value==want,message)
def same_ref(a,b):return type(a) is dict and type(b) is dict and a.get('sha256')==b.get('sha256') and Path(a.get('path','')).resolve()==Path(b.get('path','')).resolve()
def verification(proof,manifest_sha,with_hash=True):
    need(type(proof) is dict and proof.get('schema')=='algsolve.toolchain-verification.v1' and proof.get('passed') is True and proof.get('host_interpreter_matches_sandbox_python') is True and proof.get('complete_dynamic_closure_claimed') is False,'738 measured runtime verification failed')
    count(proof.get('executable_count'),4,'738 executable count invalid');count(proof.get('measured_identity_count'),59,'738 measured identity count invalid')
    if with_hash:need(proof.get('toolchain_manifest_sha256')==manifest_sha,'738 manifest verification differs')
def runtime_observation(row,bound,allowed):
    need(row.get('reader_activation_sha256')==allowed['reader_activation']['sha256'] and row.get('reader_bindings_sha256')==allowed['reader_bindings']['sha256'] and row.get('toolchain_manifest_sha256')==allowed['toolchain_manifest']['sha256'],'738 observation reader/runtime binding differs')
    for phase in ['runtime_before','runtime_after']:
        proof=row.get(phase);need(type(proof) is dict and proof.get('schema')=='algsolve.pinned-runtime-gate.v1' and proof.get('passed') is True and proof.get('candidate_executed') is False,'738 per-call runtime gate missing')
        need(proof.get('module_sha256')==bound['freeze']['sources']['toolchain.py'] and proof.get('manifest_sha256')==allowed['toolchain_manifest']['sha256'],'738 per-call verifier not pinned')
        verification(proof.get('verification'),allowed['toolchain_manifest']['sha256'],False)
    need('signal' in row and row['signal'] is None and type(row.get('stderr')) is str and len(row['stderr'].encode())<=4*1024**2 and type(row.get('notes')) is list,'738 complete sandbox status required')
    # This pinned runner records SandboxResult.ok, which already includes
    # !output_limit_exceeded. No missing independent flag is guessed clean.
    need(row.get('sandbox_ok') is True and type(row.get('exit_code')) is int and row['exit_code']==0 and row.get('timed_out') is False,'738 sandbox failure')
    wall=row.get('seconds');need(type(wall) in [int,float] and math.isfinite(wall) and 0<=wall<=8,'738 wall time invalid')

def extra_profile_checks(bound,allowed,entry,contract,current_module):
    import ast
    refs=[];frozen=bound['freeze'];files=frozen['sources']
    for name in ['reader-activation.json','reader-bindings.json','approved-test-pins.json','approved_test_loader.py','claimed_row_loader.py','runtime_gate.py','toolchain.py']:
        need(name in files,'738 reader/runtime file not frozen')
    for name in ['reader_activation','reader_bindings']:
        need(frozen.get(name+'_sha256')==allowed[name]['sha256']==files[name.replace('_','-')+'.json'],'738 reader not frozen before execution')
    old=bound['historical_reader'];before='from . import campaign_integer_dispatch as integer_profile';after='from . import campaign_uint1024_dispatch as integer_profile'
    from . import campaign_868_transition
    need(old.count(before)==2 and current_module.read_text()==campaign_868_transition.expected_reader(old.replace(before,after)),'738 combined module differs beyond exact reviewed868 import transition')
    def reader_ast(text):
        nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='verify_source'];need(len(nodes)==1,'738 scoped reader missing/duplicate');return ast.dump(nodes[0],include_attributes=False)
    need(reader_ast(old)==reader_ast(current_module.read_text()),'738 scoped reader changed')
    activation=bound['reader_activation'];reader=bound['reader_bindings'];post=bound['reader_after'];shared=activation.get('shared_reader')
    need(activation.get('schema')=='algsolve.reader-activation.v1' and identity(activation.get('owner')) and activation.get('protected_scoring_authorized') is False and shared.get('sha256')==allowed['historical_reader']['sha256'],'738 historical reader activation differs')
    need(reader.get('schema')=='algsolve.claimed-reader-binding.v1' and same_ref(reader.get('activation'),reader['references'][0]) and reader['activation']['sha256']==allowed['reader_activation']['sha256'],'738 reader activation link differs')
    references=reader.get('references');need(type(references) is list and len(references)==7 and len({r['path'] for r in references})==7,'738 reader reference coverage differs')
    need(post.get('schema')=='algsolve.reader-postverification.v1' and post.get('passed') is True and post.get('activation_sha256')==allowed['reader_activation']['sha256'] and post.get('reader_bindings_sha256')==allowed['reader_bindings']['sha256'] and post.get('full_operational_references_verified')==references,'738 historical reader postverification missing')
    need(sum(same_ref(r,shared) for r in references)==1,'738 historical full-module identity missing')
    for item in references:
        if same_ref(item,shared):continue # Snapshot is checked above; installed bytes differ by reviewed imports.
        need(sha(item['path'])==item['sha256'],'738 unchanged reader helper/reference drift');refs.append(item)
    for helper in ['approved_test_loader.py','claimed_row_loader.py','runtime_gate.py']:
        need(any(Path(r['path']).name==helper and r['sha256']==files[helper] for r in references),'738 operational helper differs from frozen copy')
    seal=bound['execution_seal'];need(seal.get('runtime_profile')==PROFILE and seal.get('reader_activation_sha256')==allowed['reader_activation']['sha256'] and seal.get('reader_bindings_sha256')==allowed['reader_bindings']['sha256'],'738 seal reader/profile mismatch')
    for name in ['toolchain_before','toolchain_after_controls','toolchain_after']:verification(bound[name],allowed['toolchain_manifest']['sha256'])
    load=bound['approved_test_load'];test=entry['independent_sets'][0]
    need(load.get('schema')=='algsolve.approved-test-load.v1' and load.get('uid')=='lcd:738' and load.get('relative_path')==test['path']=='tests/lcd__738.json' and load.get('sha256')==test['sha256'] and load.get('comparison')=='unchanged' and load.get('corrections_applied') is False and load.get('host_only') is True,'738 direct pinned test load differs')
    count(load.get('tests'),111,'738 direct test count differs')
    need(Path(load['path']).name=='lcd__738.json' and sha(load['path'])==load['raw_sha256']==frozen['dependencies'][load['path']],'738 direct test bytes differ')
    classification=bound['domain_classification'];need(classification.get('schema')=='algsolve.official-domain-supplement.v1' and classification.get('entry')=='0738:javascript' and same_ref(classification.get('packet'),allowed['packet']) and digest(classification.get('official_domain'))==digest({'minimum':0,'maximum':1000000000}) and digest(classification.get('full_unchanged_fixture_result'))==digest({'official':{'cases':85,'passed':85},'extended':{'cases':29,'passed':29},'total':{'cases':114,'passed':114}}),'738 official versus extended classification differs')
    count(bound['number_failure'].get('failed_cases'),5,'738 original Number failures changed')
    prior=bound['prior_uint20'];need(prior.get('status')=='blocked-declared-numeric-domain' and prior.get('entry')=='0738:javascript' and prior.get('runtime_profile')=='lc738-uint20-number-bigint-v1' and prior.get('no_qualification_or_admission') is True,'738 incomplete prior attempt must remain blocked')
    for n,want in [('cases_planned',114),('cases_executed',92),('passed_executed',92),('unexecuted_cases',22)]:count(prior.get(n),want,'738 prior incomplete counts differ')
    need(prior['source']['sha256']==contract['normalized_sha256'] and bound['number_failure']['normalized_sha256']==allowed['prior_source']['sha256'],'738 predecessor source identities differ')
    # Preserve the incomplete attempt and all indexed observations without importing its runner.
    for value in prior.values():
        if type(value) is dict and set(value)>={'path','sha256'}:need(sha(value['path'])==value['sha256'],'738 prior evidence changed');refs.append(value)
    prior_index=check(prior['evidence_index'])
    for item in prior_index.get('files',[]):need(sha(item['path'])==item['sha256'],'738 prior raw artifact changed');refs.append(item)
    technical=bound['technical_review']
    for name in ['qualification','reader_activation','reader_bindings','reader_after','approved_test_load','domain_classification','prior_uint20','number_failure','summary']:
        need(any(same_ref(item,allowed[name]) for item in technical.get('evidence',[])),'738 post-run review lacks binding: '+name)
    q=bound['qualification'];need(q.get('schema')=='algsolve.alternate-integer-development-handoff.v2' and q.get('entry')=='0738:javascript' and q.get('runtime_profile')==PROFILE and same_ref(q.get('source'),{'path':str(Path(allowed['freeze']['path']).parent/'normalized/0738.js'),'sha256':contract['normalized_sha256']}),'738 author handoff identity differs')
    for name in ['freeze','contract','controls','toolchain_manifest','execution_seal','reader_activation','reader_bindings','reader_after','approved_test_load','evidence_index','domain_classification','summary']:
        target='runtime_contract' if name=='contract' else name
        need(same_ref(q.get(name),allowed[target]),'738 author handoff link differs: '+name)
    need(same_ref(q.get('old_uint20_failure_preserved'),allowed['prior_uint20']) and same_ref(q.get('old_number_failure_preserved'),allowed['number_failure']),'738 historical failures missing in handoff')
    for field,want in [('cases',114),('passed',114),('official_cases',85),('official_passed',85),('extended_cases',29),('extended_passed',29),('sandbox_controls',114),('host_controls',30),('infrastructure_errors',0),('decoding_errors',0)]:count(q.get(field),want,'738 handoff count differs: '+field)
    need(q.get('all_controls_passed') is True and q.get('mutation_alias_ok') is True and q.get('completed_python_738_unchanged') is True,'738 handoff failures hidden')
    index=bound['evidence_index'];seen=set()
    for item in index.get('files',[]):
        path=str(Path(item['path']).resolve());need(path not in seen and sha(path)==item['sha256'],'738 raw evidence missing/duplicate/changed');seen.add(path);refs.append(item)
    count(len(seen),236,'738 raw index incomplete')
    return refs

def extra_execution_checks(bound,allowed,execution,refs):
    index={str(Path(item['path']).resolve()):item for item in bound['evidence_index']['files']};folder=Path(allowed['freeze']['path']).parent
    def indexed(name):
        path=str((folder/'results'/name).resolve());need(path in index,'738 raw control artifact missing');return check(index[path])
    controls=bound['controls'];count(controls.get('host_count'),30,'738 host count type invalid');count(controls.get('sandbox_count'),114,'738 control count type invalid')
    need(digest(indexed('controls-summary.json'))==digest(controls),'738 controls summary not in reviewed index')
    for i,row in enumerate(controls['sandbox_controls'],1):need(digest(indexed(f'control-{i:03d}.json'))==digest(row),'738 control raw receipt differs')
    for name in ['summary','toolchain_before','toolchain_after_controls','toolchain_after','approved_test_load']:
        need(str(Path(allowed[name]['path']).resolve()) in index,'738 named result not in reviewed index')
    summary=bound['summary'];need(summary.get('freeze_sha256')==allowed['freeze']['sha256'] and summary.get('toolchain_manifest_sha256')==allowed['toolchain_manifest']['sha256'] and summary.get('reader_activation_sha256')==allowed['reader_activation']['sha256'] and summary.get('approved_test_load_sha256')==allowed['approved_test_load']['sha256'] and summary.get('toolchain_after_sha256')==allowed['toolchain_after']['sha256'],'738 summary runtime binding differs')
    rows=summary.get('results');need(type(rows) is list and len(rows)==1,'738 qualification language coverage differs');row=rows[0]
    need(row.get('language')=='javascript' and row.get('runtime_profile')==PROFILE and row.get('source_sha256')==allowed['normalized_sha256'] and row.get('mutation_alias_ok') is True,'738 summary source/profile differs')
    for name,want in [('id',738),('cases',114),('passed',114),('official_cases',85),('official_passed',85),('infrastructure_errors',0),('decoding_errors',0)]:count(row.get(name),want,'738 summary count differs')
    need(digest(row.get('groups'))==digest([{'name':g['name'],'cases':len(g['tests']),'sha256':digest(g['tests'])} for g in bound['host_tests']]),'738 summary test binding differs')
    for name,want in [('public_total',3),('public_passed',3),('independent_total',111),('independent_passed',111),('infrastructure_errors',0),('decoding_errors',0)]:count(execution.get(name),want,'738 admission count differs')
    for name,want in [('mutation_passed',True),('alias_passed',True),('sandboxed',True),('expected_outputs_in_sandbox',False)]:need(execution.get(name) is want,'738 admission flag differs')
