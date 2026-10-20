"""Narrow coordinator-gated LC633 uint64 -> strict boolean admission.

Only host evidence is parsed/scored. Never import author candidate/codec/runner.
The670 validator and policy stay independent; dispatcher selects explicit keys.
"""
import dataclasses,hashlib,json,math,sys
from pathlib import Path
from algsolve import validate
from algsolve.judge import judge,sandbox
from . import campaign_exact_integer as common,campaign_toolchain
PROFILE='lc633-uint64-bigint-bool-v1'
INTERFACE='exact-public-spelling:uint64-bigint-bool.v1'
DOMAIN={'minimum':'0','maximum':'18446744073709551615','maximum_decimal_digits':20}
MAXIMUM=2**64-1
TAG=common.TAG
RUNTIME=common.RUNTIME
BINDINGS=('freeze','packet','host_tests','qualification','technical_review','prior_failure','standard','runtime_contract','controls','algorithm_controls','summary','toolchain_manifest','execution_seal','toolchain_before','toolchain_after')
need=common.need;sha=common.sha;digest=common.digest;ref=common.ref;check=common.check;identity=common.identity;distinct=common.distinct;compact=common.compact
ENV={'PATH':'/usr/bin','LANG':'C.UTF-8','HOME':'/tmp','PYTHONHASHSEED':'0','PYTHONDONTWRITEBYTECODE':'1'}
LIMITS=sandbox.Limits(wall_seconds=8,cpu_seconds=3,memory_bytes=1024**3,max_output_bytes=4*1024**2)
def key(entry):return f"{entry['id']:04d}:{entry['language']}"
def typed_count(value,expected,message):need(type(value) is int and value==expected,message)
def same_ref(value,expected):return type(value) is dict and value.get('sha256')==expected['sha256'] and Path(value.get('path','')).resolve()==Path(expected['path']).resolve()
def toolchain_check(manifest,folder):
    need(manifest.get('schema')=='algsolve.measured-toolchain.v1' and manifest.get('profile')==PROFILE,'Missing633 measured toolchain')
    need(manifest.get('host_environment')==ENV and manifest.get('sandbox_environment')==ENV,'633 invocation environment changed')
    need(manifest.get('host_driver_argv')==['/usr/bin/python3',str(folder/'run.py')],'633 host driver argv changed')
    need(manifest.get('host_invocation')==['/usr/bin/env','-i',*[k+'='+v for k,v in ENV.items()],'/usr/bin/python3',str(folder/'run.py')],'633 host invocation changed')
    need(type(manifest.get('host_cwd')) is str and type(manifest.get('host_python_flags')) is list and manifest.get('host_python_xoptions')=={} and manifest.get('host_python_warnoptions')==[],'633 startup options missing')
    commands={'python':['/usr/bin/python3','harness.py'],'javascript':['/usr/bin/node','--jitless','--max-old-space-size=64','harness.cjs']}
    need(manifest.get('sandbox_invocations')=={k:sandbox.bwrap_argv(Path('<fresh-task-directory>'),LIMITS,v) for k,v in commands.items()},'633 sandbox command boundary changed')
    need(manifest.get('task_mounts')=={'qualification_python':['calls.json','harness.py','codec.py','candidate.py'],'qualification_javascript':['calls.json','harness.cjs','candidate.cjs'],'expected_outputs_mounted':False},'633 sandbox mount contract changed')
    need(manifest.get('candidate_execution_during_measurement') is False and manifest.get('test_contents_decoded_during_measurement') is False,'633 startup probe scope changed')
    need(type(manifest.get('exclusions')) is list and any('No claim of complete hermetic dependency closure' in x for x in manifest['exclusions'] if type(x) is str),'633 measured scope exclusions missing')
    measured=manifest.get('files');need(type(measured) is list and bool(measured),'Missing633 measured identities')
    paths=[];refs=[]
    def validate_file(row):
        need(type(row) is dict and set(row)=={'path','resolved_path','symlinks','size','sha256'},'Malformed633 measured file identity')
        actual=campaign_toolchain.file_identity(row['path'])
        need(row['resolved_path']==actual['resolved'] and row['symlinks']==actual['symlink_chain'] and row['sha256']==actual['sha256'] and type(row['size']) is int and row['size']==Path(row['resolved_path']).stat().st_size,'633 measured file/link drift')
        refs.append({'path':row['path'],'sha256':row['sha256']})
    for row in measured:validate_file(row);paths.append(row['path'])
    need(len(paths)==len(set(paths)),'Duplicate633 measured identities')
    executables=manifest.get('executables');need(type(executables) is list and [r.get('name') for r in executables]==['python','node','bwrap','prlimit'],'Missing633 executable versions')
    for row,path in zip(executables,['/usr/bin/python3','/usr/bin/node','/usr/bin/bwrap','/usr/bin/prlimit']):
        need(row.get('path')==path and row.get('version_argv')==[path,'--version'] and type(row.get('version_stdout')) is str and bool(row['version_stdout'].strip()),'633 executable version missing')
        validate_file({k:row[k] for k in ['path','resolved_path','symlinks','size','sha256']})
        need(row['path'] in paths and row.get('ldd_argv')==['/usr/bin/ldd',path] and type(row.get('ldd_stdout')) is str and 'not found' not in row['ldd_stdout'],'633 loader measurement missing')
        reported=[]
        for line in row['ldd_stdout'].splitlines():
            reported.extend(word for word in line.split() if word.startswith('/'))
        need(row.get('measured_dependencies')==reported and all(p in paths for p in reported) and bool(reported),'633 loader dependency binding missing')
    validate_file(manifest['host_driver']);need(manifest['host_driver']['resolved_path']==str(Path(sys.executable).resolve()) and manifest['host_driver']['sha256']==sha(sys.executable),'633 host intake Python differs from measured driver')
    probes=manifest.get('sandbox_startup_probes');need(type(probes) is list and [r.get('language') for r in probes]==['python','javascript'],'633 startup probes missing')
    for probe in probes:
        clean_status(probe.get('raw_result',{}));data=probe.get('measurement',{});need(data.get('environment')==dict(ENV,PWD='/task'),'633 observed child environment differs')
        need(json.loads(probe['raw_result']['stdout'])==data,'633 startup raw/decoded mismatch')
        need(type(data.get('mapped_files')) is list and all(p in paths for p in data['mapped_files']),'633 observed mapped library unbound')
        for module in data.get('module_origins',[]):
            path=module['file'];path=str(folder/path.removeprefix('/task/')) if path.startswith('/task/') else path
            need(path in paths,'633 observed Python module unbound')
    approved=manifest.get('approved_test_packet',{});validate_file(approved.get('identity'))
    need(approved.get('path')==approved['identity']['path'] and approved.get('resolved_path')==approved['identity']['resolved_path'] and approved.get('raw_sha256')==approved['identity']['sha256'],'633 approved test identity mismatch')
    return refs

def profile(data,entry,contract):
    entrykey=key(entry);language=entry['language'];ext='py' if language=='python' else 'js'
    need(entrykey in ['0633:python','0633:javascript'] and entry['key']=='lc:sum-of-square-numbers','Only explicit633 language keys supported')
    need(contract.get('schema')=='algsolve.campaign-contract.v3' and contract.get('interface')==INTERFACE and contract.get('comparison')=='unchanged','633 alternate interface/comparison mismatch')
    need(not any(k in contract for k in ['public_comparison','independent_comparison']),'633 combined comparison override forbidden')
    policyref=data.get('inputs',{}).get('uint64_bool_policy');policy=check(policyref)
    need(policy.get('schema')=='algsolve.uint64-bool-admission-policy.v1' and policy.get('status')=='approved','633 coordinator policy not approved')
    need(type(policy.get('entries')) is dict and set(policy['entries'])<= {'0633:python','0633:javascript'},'633 policy includes unsupported entry')
    author=contract.get('source_author');need(distinct(author,policy.get('approved_by')),'633 independent coordinator approval required')
    allowed=policy.get('entries',{}).get(entrykey);need(type(allowed) is dict,'633 entry lacks language-specific policy')
    need(allowed.get('profile')==PROFILE and allowed.get('numeric_domain')==DOMAIN and allowed.get('source_author')==author and allowed.get('normalized_sha256')==contract.get('normalized_sha256'),'633 profile/domain/author/source mismatch')
    from . import campaign_integer_dispatch
    need(allowed.get('admission_common_validator_sha256')==sha(common.__file__) and allowed.get('admission_validator_sha256')==sha(__file__) and allowed.get('admission_dispatch_sha256')==sha(campaign_integer_dispatch.__file__) and allowed.get('admission_toolchain_validator_sha256')==sha(campaign_toolchain.__file__),'633 validator/dispatcher/helper drift')
    refs=[policyref];bound={}
    for name in BINDINGS:bound[name]=check(allowed.get(name));refs.append(allowed[name])
    runtime=allowed.get('runtime');need(type(runtime) is dict and set(runtime)==set(RUNTIME),'633 trusted judge runtime missing')
    for name,path in RUNTIME.items():need(sha(path)==runtime[name],'633 trusted judge runtime drift');refs.append(ref(path))
    packet=bound['packet'];need(packet.get('id')==633 and packet.get('key')=='lc:sum-of-square-numbers' and packet.get('entry')=={'class':'Solution','method':'judgeSquareSum'} and packet.get('params')==[['c','int']],'633 packet/interface identity mismatch')
    sets=entry['independent_sets'];need(type(sets) is list and len(sets)==1 and sets[0].get('uid')=='lcd:633' and sets[0].get('path')=='tests/lcd__633.json' and sets[0].get('tests')==52 and sets==packet.get('independent_test_sets'),'633 unchanged independent identity mismatch')
    typed_count(contract.get('public_tests'),2,'633 public count mismatch');need(len(packet.get('public_tests',[]))==2,'633 public packet mismatch')
    frozen=bound['freeze'];folder=Path(allowed['freeze']['path']).parent.resolve()
    need(frozen.get('schema')=='algsolve.exact-integer-profile-freeze.v1' and frozen.get('runtime_profile')==PROFILE and frozen.get('candidate_execution_started') is False and frozen.get('controls_execution_started') is False and frozen.get('expected_outputs_in_sandbox') is False,'633 pre-execution freeze missing')
    need(digest(frozen.get('limits'))==digest({'parallelism':1,'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1073741824,'cases_per_chunk':1,'small_control_cases_per_chunk':32}),'633 execution limits changed')
    files=frozen.get('sources');need(type(files) is dict and all(n in files for n in ['codec.py','harness.py','harness.cjs','run.py','toolchain.py','toolchain-manifest.json','controls.json','policy.json','contract.json',f'normalized/0633.{ext}',f'normalized/0633.{ext}.bindings.json',f'normalized/0633.{ext}.semantics.json']),'633 frozen source boundary incomplete')
    for rel,want in files.items():
        p=(folder/rel).resolve();need(p.is_relative_to(folder) and sha(p)==want,'633 frozen file drift');refs.append(ref(p))
    for p,want in frozen.get('dependencies',{}).items():need(sha(p)==want,'633 runner dependency drift');refs.append(ref(p))
    need(files[f'normalized/0633.{ext}']==contract['normalized_sha256'] and files['policy.json']==allowed['standard']['sha256']==contract.get('standard_sha256') and files['contract.json']==allowed['runtime_contract']['sha256'] and files['0633-packet.json']==allowed['packet']['sha256'],'633 source/standard/packet not frozen')
    need(frozen.get('toolchain_manifest_sha256')==files['toolchain-manifest.json']==allowed['toolchain_manifest']['sha256'],'633 toolchain not frozen before run')
    rc=bound['runtime_contract'];need(rc.get('runtime_profile')==PROFILE and rc.get('domain')==DOMAIN and rc.get('independent_sets')==sets and rc.get('python_result')=='exact type bool' and rc.get('javascript_result')=='typeof boolean only, no BigInt/Number/string/boxed boolean coercion','633 numeric/result contract differs')
    need('Partial bounded algorithm' in rc.get('completion','') and same_ref(rc.get('toolchain_manifest'),allowed['toolchain_manifest']),'633 partial algorithm/toolchain contract missing')
    technical=bound['technical_review'];need(technical.get('schema')=='algsolve.independent-technical-review.v1' and technical.get('status')=='technical pass within declared partial algorithm and measured toolchain boundary' and technical.get('technical_blockers')==[] and technical.get('author')==author and distinct(technical.get('reviewer'),author),'633 independent technical review required')
    need(technical.get('admission_authorized') is False and technical.get('runtime_profile')==PROFILE and technical.get('source_sha256',{}).get(language)==contract['normalized_sha256'] and technical.get('freeze_sha256')==allowed['freeze']['sha256'] and technical.get('toolchain_manifest_sha256')==allowed['toolchain_manifest']['sha256'],'633 technical review identity differs')
    technical_bindings=technical.get('binding_sha256');need(type(technical_bindings) is dict,'633 technical evidence bindings missing')
    for name in ['freeze','qualification','runtime_contract','summary','controls','algorithm_controls','toolchain_manifest','execution_seal','toolchain_before','toolchain_after']:
        need(technical_bindings.get(str(Path(allowed[name]['path']).resolve()))==allowed[name]['sha256'],'633 artifact not independently reviewed')
    for p,h in technical_bindings.items():need(sha(p)==h,'633 technical review evidence drift');refs.append({'path':p,'sha256':h})
    q=bound['qualification'];need(q.get('schema')=='algsolve.exact-integer-qualification-receipt.v2' and q.get('problem_id')==633 and q.get('runtime_profile')==PROFILE and q.get('author')==author and q.get('source_sha256',{}).get(language)==contract['normalized_sha256'],'633 qualification identity mismatch')
    for name,qname in [('freeze','freeze'),('standard','policy'),('runtime_contract','contract'),('toolchain_manifest','toolchain_manifest'),('toolchain_before','preflight'),('toolchain_after','postflight')]:need(same_ref(q.get(qname),allowed[name]),'633 qualification link differs')
    refs+=toolchain_check(bound['toolchain_manifest'],folder)
    manifest=bound['toolchain_manifest'];test=manifest['approved_test_packet'];need(test['canonical_sha256']==sets[0]['sha256'],'633 measured test packet canonical hash differs');typed_count(test.get('count'),52,'633 measured test count differs')
    need(Path(test['path']).name=='lcd__633.json','633 measured test path differs')
    seal=bound['execution_seal'];need(seal.get('freeze_sha256')==allowed['freeze']['sha256'] and seal.get('toolchain_manifest_sha256')==allowed['toolchain_manifest']['sha256'] and seal.get('runtime_profile')==PROFILE and seal.get('expected_outputs_in_sandbox') is False and type(seal.get('cpu_affinity')) is list and len(seal['cpu_affinity'])==1 and type(seal['cpu_affinity'][0]) is int,'633 execution seal differs')
    for name in ['toolchain_before','toolchain_after']:
        proof=bound[name];need(proof.get('verified') is True and proof.get('manifest_sha256')==allowed['toolchain_manifest']['sha256'],'633 pre/post verification missing')
    before=bound['toolchain_before'];need(before.get('environment')==ENV and before.get('host_orig_argv')==manifest['host_driver_argv'] and digest(before.get('host_flags'))==digest(manifest['host_python_flags']) and before.get('host_cwd')==manifest['host_cwd'],'633 observed host startup differs')
    failure=bound['prior_failure'];need(failure.get('schema')=='algsolve.normalization-failure.v1' and failure.get('entry')==entrykey,'633 prior failure identity missing');typed_count(failure.get('total_cases'),54,'633 prior total differs');typed_count(failure.get('passed_cases'),47,'633 prior failures not preserved');typed_count(failure.get('failed_cases'),7,'633 prior failures changed')
    prior=allowed.get('prior_source');need(type(prior) is dict and sha(prior['path'])==prior.get('sha256')==failure.get('normalized_sha256') and prior['sha256']!=contract['normalized_sha256'],'633 predecessor source missing/replaced');refs.append(prior)
    for item in failure.get('artifacts',[]):need(sha(item['path'])==item['sha256'],'633 predecessor artifact changed');refs.append(item)
    descriptor={'profile':PROFILE,'entry':entrykey,'numeric_domain':DOMAIN,'policy_sha256':policyref['sha256'],'bindings':{n:allowed[n]['sha256'] for n in BINDINGS},'runtime':runtime}
    need(contract.get('runtime_profile')==descriptor,'633 runtime descriptor differs')
    return descriptor,bound,refs

def integer(value):
    result=common.integer(value);need(0<=result<=MAXIMUM,'633 uint64 overflow');return result

def decode_stdout(raw,cases,language):
    need(language in ['python','javascript'] and type(cases) is list and bool(cases),'633 decoder scope invalid')
    need(type(raw) is str and len(raw.encode())<=4*1024**2,'633 raw output size invalid')
    rows=[]
    for line in raw.splitlines():
        row=json.loads(line);need(compact(row)==line,'633 duplicate/noncanonical transport');rows.append(row)
    need(len(rows)==len(cases)+1,'633 incomplete/extra records')
    done=rows[-1];need(type(done) is dict and set(done)=={'done'},'633 completion shape invalid');typed_count(done.get('done'),len(cases),'633 completion count invalid')
    decoded=[]
    for index,(row,case) in enumerate(zip(rows[:-1],cases)):
        fields={'i','result','args_before','args_after','argument_runtime_types','result_runtime_type','input_object_count','returned_input_ids','input_node_values_preserved'}
        need(type(row) is dict and set(row)==fields,'633 result shape invalid');typed_count(row.get('i'),index,'633 result index invalid')
        need(type(row['result']) is bool,'633 result must be strict boolean');typed_count(row.get('input_object_count'),0,'633 primitive alias count invalid')
        need(row.get('returned_input_ids')==[] and row.get('input_node_values_preserved') is True,'633 primitive alias marker invalid')
        need(type(case) is dict and not case.get('kwargs') and type(case.get('args')) is list and len(case['args'])==1 and type(case['args'][0]) is int and 0<=case['args'][0]<=MAXIMUM,'633 case outside uint64')
        out=dict(row)
        for name in ['args_before','args_after']:
            need(type(row[name]) is list and len(row[name])==1,'633 argument shape invalid');out[name]=[integer(row[name][0])];need(out[name]==case['args'],'633 host argument binding/mutation failure')
        need(row['argument_runtime_types']==(['int'] if language=='python' else ['bigint']) and row['result_runtime_type']==('bool' if language=='python' else 'boolean'),'633 runtime type label differs')
        decoded.append(out)
    return decoded+[done]

def clean_status(row):
    need(type(row) is dict and row.get('sandbox_ok') is True,'633 sandbox status missing');typed_count(row.get('exit_code'),0,'633 exit status invalid')
    need(row.get('signal') is None and 'signal' in row and row.get('timed_out') is False and row.get('output_limit_exceeded') is False,'633 execution failure flags')
    wall=row.get('wall_seconds');need(type(wall) in [int,float] and math.isfinite(wall) and 0<=wall<=8,'633 wall time invalid')
    need(type(row.get('stderr')) is str and len(row['stderr'].encode())<=4*1024**2 and type(row.get('notes')) is list,'633 stderr/notes malformed')

def score_chunk(row,cases,language):
    clean_status(row);need(row.get('decode_error') is None and 'decode_error' in row and row.get('mutation_alias_ok') is True,'633 decoding/mutation flags invalid')
    need(all(type(case.get('expected')) is bool and case.get('compare','return')=='return' for case in cases),'633 expected output/comparison outside boolean contract')
    decoded=decode_stdout(row.get('stdout'),cases,language)
    need(all(observation['result'] is case['expected'] for observation,case in zip(decoded,cases)),'633 exact boolean result mismatch')
    need(digest(decoded)==digest(row.get('decoded_observations')),'633 saved decoded output differs from raw')
    payload=compact({'profile':PROFILE,'entry':'Solution.judgeSquareSum','calls':[{'args':[{TAG:str(case['args'][0])}]} for case in cases]})
    need(hashlib.sha256(payload.encode()).hexdigest()==row.get('payload_sha256') and digest(cases)==row.get('original_cases_sha256'),'633 frozen input/expected/comparison binding differs')
    result=sandbox.SandboxResult(exit_code=0,signal=None,stdout=('\n'.join(json.dumps(v) for v in decoded)+'\n').encode(),stderr=row['stderr'].encode(),wall_seconds=row['wall_seconds'],timed_out=False,output_limit_exceeded=False,notes=row['notes'])
    verdict=judge._score_functional(result,validate.functional_tests(cases));need(verdict.passed and verdict.tests_passed==len(cases) and digest(verdict.to_dict())==digest(row.get('verdict')),'633 unchanged host score failed or differs')
    return len(cases)

def controls_check(summary,fixture):
    typed_count(summary.get('host_count'),29,'633 host controls incomplete');typed_count(summary.get('sandbox_count'),66,'633 sandbox controls incomplete');need(summary.get('passed') is True,'633 controls failed')
    names=['host-roundtrip-'+str(v) for v in fixture['roundtrip']]+['host-reject-'+repr(v) for v in [-1,MAXIMUM+1,True,False,None,1.0,'1']]
    names+=['host-'+n for n in ['duplicate-row-key','duplicate-envelope-key','whitespace','bool-done','bool-index','numeric-result','missing-done','extra-row','wrong-host-input','mutated-argument','js-number-argument','js-int-argument','python-bigint','wrong-result-label','bool-object-count','overflow-argument']]
    host=summary.get('host_checks');need(type(host) is list and len(names)==len(set(names))==29 and [r.get('name') for r in host]==names and all(r.get('passed') is True for r in host),'633 host control identity/status missing')
    expected=[]
    for lang in ['python','javascript']:
        expected.append((lang,'input-roundtrip-type-boundary','roundtrip'))
        expected.extend((lang,r['name'],'input-error') for r in fixture['malformed_inputs'])
        expected.extend((lang,'invalid-result-'+expression,'output-error') for expression in fixture['invalid_results'][lang])
        expected.append((lang,'exhausted-helper-never-false','exhaustion'))
    rows=summary.get('sandbox_controls');need(type(rows) is list and len(rows)==len(expected)==66,'633 profile control coverage incomplete')
    for row,(language,name,kind) in zip(rows,expected):
        need(row.get('language')==language and row.get('name')==name and row.get('passed') is True,'633 sandbox control identity/status differs');clean_status(row)
        raw=row.get('stdout');need(type(raw) is str and len(raw.encode())<=4*1024**2,'633 profile control raw output invalid');parsed=[]
        for line in raw.splitlines():
            value=json.loads(line);need(compact(value)==line,'633 profile control noncanonical output');parsed.append(value)
        if kind=='roundtrip':
            decoded=decode_stdout(raw,[{'args':[v]} for v in fixture['roundtrip']],language)
            need(all(row['result'] is True for row in decoded[:-1]) and digest(decoded)==digest(row.get('decoded')),'633 exact input/control result mismatch')
        elif kind=='input-error':
            need(len(parsed)==1 and type(parsed[0]) is dict and parsed[0].get('load_error')=='input_validation' and 'SOURCE_EXECUTED' not in raw+row['stderr'],'633 malformed input reached candidate')
        else:
            need(len(parsed)==2 and type(parsed[0]) is dict and parsed[0].get('error')=='candidate_or_output' and 'result' not in parsed[0] and type(parsed[0].get('i')) is int and parsed[0]['i']==0 and type(parsed[1]) is dict and set(parsed[1])=={'done'},'633 invalid output/exhaustion was accepted')
            typed_count(parsed[1].get('done'),1,'633 invalid-result completion missing')
            if kind=='exhaustion':need('work limit exhausted' in parsed[0].get('detail',''),'633 exhausted helper did not fail explicitly')

def execution_profile(data,entry,contract,execution,review):
    descriptor,bound,refs=profile(data,entry,contract);language=entry['language'];allowed=check(data['inputs']['uint64_bool_policy'])['entries'][key(entry)];folder=Path(allowed['freeze']['path']).parent.resolve()
    need(execution.get('runtime_profile')==descriptor and review.get('runtime_profile')==descriptor,'633 execution/review descriptor differs')
    need(review.get('runtime_profile_reviewed') is True and distinct(review.get('reviewer'),contract['source_author']) and review.get('runtime_qualification_sha256')==descriptor['bindings']['qualification'],'633 independent admission review required')
    q=bound['qualification'];artifacts=q.get('artifacts');need(type(artifacts) is list and bool(artifacts),'633 reviewed raw artifacts missing')
    indexed={}
    for item in artifacts:
        need(type(item) is dict and type(item.get('path')) is str and sha(item['path'])==item.get('sha256'),'633 raw artifact hash changed')
        path=str(Path(item['path']).resolve());need(path not in indexed,'633 duplicate raw artifact identity');indexed[path]=item;refs.append(item)
    def artifact(name):
        path=str(folder/'results'/name);need(path in indexed,'633 raw evidence missing: '+name)
        return check(indexed[path])
    groups=bound['host_tests'];names=['public','independent-lcd-633'];need(type(groups) is list and [g.get('name') for g in groups]==names,'633 test group coverage/order differs')
    need(digest(groups[0].get('tests'))==digest(bound['packet']['public_tests']),'633 public tests/comparisons changed')
    need(type(groups[1].get('tests')) is list and len(groups[1]['tests'])==52 and digest(groups[1]['tests'])==entry['independent_sets'][0]['sha256'],'633 independent tests/comparisons changed')
    passed=[0,0]
    for group_index,group in enumerate(groups):
        for offset,case in enumerate(group['tests']):
            row=artifact(f'0633-{language}-{group["name"]}-{offset}.json');need(row.get('group')==group['name'],'633 observation group differs');typed_count(row.get('offset'),offset,'633 observation offset differs');typed_count(row.get('count'),1,'633 chunk count differs')
            need(type(row.get('official_admissible')) is bool and row['official_admissible']==(0<=case['args'][0]<=2147483647),'633 domain subset marker differs')
            passed[group_index]+=score_chunk(row,[case],language)
    need(passed==[2,52],'633 unchanged qualification incomplete')
    summary=bound['summary'];need(digest(artifact('summary.json'))==digest(summary) and summary.get('freeze_sha256')==allowed['freeze']['sha256'],'633 summary/freeze differs')
    summaries=summary.get('results');need(type(summaries) is list and [r.get('language') for r in summaries]==['python','javascript'],'633 summary language coverage differs')
    for result in summaries:
        for field,count in [('id',633),('cases',54),('passed',54),('official_cases',43),('official_passed',43),('infrastructure_errors',0),('decoding_errors',0)]:typed_count(result.get(field),count,'633 summary count differs: '+field)
        need(result.get('runtime_profile')==PROFILE and result.get('mutation_alias_ok') is True,'633 summary profile/alias differs')
        need(result.get('source_sha256')==bound['technical_review']['source_sha256'][result['language']],'633 summary source differs')
        need(digest(result.get('groups'))==digest([{'name':g['name'],'cases':len(g['tests']),'sha256':digest(g['tests'])} for g in groups]),'633 summary group binding differs')
    qcounts=q.get('qualification');need(type(qcounts) is dict,'633 qualification count declaration missing')
    for field,count in [('unchanged_cases_per_language',54),('passed_per_language',54),('public',2),('independent',52),('official_subset',43),('exact_uint64_extended_subset',11),('algorithm_controls_per_language',1038),('host_controls',29),('sandbox_profile_controls',66),('runtime_failures',0),('decoding_errors',0),('mutation_alias_errors',0)]:typed_count(qcounts.get(field),count,'633 qualification count declaration differs: '+field)
    need(qcounts.get('comparison')=='unchanged' and qcounts.get('all_controls_passed') is True,'633 qualification comparison/control declaration differs')
    fixture=json.loads((folder/'controls.json').read_text());controls_check(bound['controls'],fixture)
    need(digest(artifact('profile-controls-summary.json'))==digest(bound['controls']),'633 control summary differs from reviewed raw artifacts')
    for i,row in enumerate(bound['controls']['sandbox_controls'],1):need(digest(artifact(f'profile-control-{i:03d}.json'))==digest(row),'633 standalone control transcript differs')
    total=0
    for offset in range(0,len(fixture['small_exhaustive']),32):
        cases=fixture['small_exhaustive'][offset:offset+32];row=artifact(f'algorithm-{language}-small-{offset}.json')
        need(row.get('group')=='small-exhaustive','633 small control group differs');typed_count(row.get('offset'),offset,'633 small control offset differs');typed_count(row.get('count'),len(cases),'633 small control count differs');total+=score_chunk(row,cases,language)
    for offset,item in enumerate(fixture['constructed']):
        row=artifact(f'algorithm-{language}-constructed-{offset}.json');case={k:item[k] for k in ['args','expected','compare']}
        need(row.get('group')=='constructed' and row.get('name')==item['name'],'633 constructed control identity differs');typed_count(row.get('offset'),offset,'633 constructed control offset differs');typed_count(row.get('count'),1,'633 constructed control count differs');total+=score_chunk(row,[case],language)
    typed_count(total,1038,'633 arithmetic controls incomplete')
    need(digest(artifact('algorithm-controls-summary.json'))==digest(bound['algorithm_controls']),'633 arithmetic summary differs')
    summaries=bound['algorithm_controls'];need(type(summaries) is list and [r.get('language') for r in summaries]==['python','javascript'],'633 arithmetic summary language coverage differs')
    for row in summaries:
        typed_count(row.get('cases'),1038,'633 arithmetic count changed');typed_count(row.get('passed'),1038,'633 arithmetic pass count changed');need(row.get('all_small_passed') is True and row.get('failures')==[],'633 arithmetic failure hidden')
    for field,count in [('public_total',2),('public_passed',2),('independent_total',52),('independent_passed',52),('decoding_errors',0),('infrastructure_errors',0)]:typed_count(execution.get(field),count,'633 execution count mismatch: '+field)
    for field,want in [('mutation_passed',True),('alias_passed',True),('sandboxed',True),('expected_outputs_in_sandbox',False)]:need(execution.get(field) is want,'633 execution flag mismatch: '+field)
    declared=execution.get('artifacts');need(type(declared) is list,'633 execution artifacts missing')
    for item in refs:need(any(same_ref(x,item) for x in declared),'633 preserved runtime artifact missing')
    return refs
