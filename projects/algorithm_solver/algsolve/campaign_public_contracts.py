"""Narrow opt-in public-order admission; host-scores saved transcripts only.

A coordinator-owned ledger input pins the statement/public packet and trusted
runtime. Author-provided self-consistent hashes alone grant no comparison change.
The ledger still never imports or executes candidate code. This profile explicitly
reads approved host-only test transcripts, unlike legacy metadata-only admission.
"""
import dataclasses,hashlib,json,math
from pathlib import Path
from algsolve import public_contracts,public_examples,records,validate,values,importers
from algsolve.judge import judge,functional_semantics,declared_comparison,sandbox
MODE='statement-declared-public.v1'
RUNTIME={name:Path(module.__file__).resolve() for name,module in {
 'public_contracts.py':public_contracts,'public_examples.py':public_examples,
 'records.py':records,'values.py':values,'importers.py':importers,'validate.py':validate,
 'judge/judge.py':judge,'judge/functional_semantics.py':functional_semantics,
 'judge/declared_comparison.py':declared_comparison,'judge/sandbox.py':sandbox}.items()}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def checked(ref):
    if not isinstance(ref,dict) or not isinstance(ref.get('path'),str) or sha(ref['path'])!=ref.get('sha256'):raise ValueError('Unbound public-contract artifact')
    return json.loads(Path(ref['path']).read_text())
def need(condition,message):
    if not condition:raise ValueError(message)
def requires_profile(data,entry):
    ref=data.get('inputs',{}).get('public_comparison_policy')
    if ref is None:return False
    registry=checked(ref)
    need(registry.get('schema')=='algsolve.public-comparison-policy.v1' and isinstance(registry.get('entries'),dict),'Wrong coordinator policy schema')
    return entry['key'] in registry['entries']

def profile(data,entry,contract):
    need(contract.get('schema')=='algsolve.campaign-contract.v2' and contract.get('comparison')==MODE and contract.get('independent_comparison')=='unchanged','Unsupported comparison profile')
    author=contract.get('source_author');need(isinstance(author,str) and bool(author.strip()),'Source author required')
    registry_ref=data.get('inputs',{}).get('public_comparison_policy');registry=checked(registry_ref)
    need(registry.get('schema')=='algsolve.public-comparison-policy.v1','Wrong coordinator policy schema')
    approver=registry.get('approved_by');need(isinstance(approver,str) and bool(approver.strip()) and approver!=author,'Independent coordinator approval required')
    allowed=registry.get('entries',{}).get(entry['key']);need(isinstance(allowed,dict),'Problem lacks coordinator policy')
    need(allowed.get('mode')==MODE,'Coordinator mode mismatch')
    packet=checked(allowed['packet'])
    need(packet.get('id')==entry['id'] and packet.get('key')==entry['key'],'Public packet identity mismatch')
    need(packet.get('independent_test_sets')==entry['independent_sets'],'Packet independent identity mismatch')
    runtime=allowed.get('runtime');need(isinstance(runtime,dict) and set(runtime)==set(RUNTIME),'Incomplete trusted comparator runtime')
    for name,path in RUNTIME.items():need(sha(path)==runtime[name],'Trusted comparator runtime drift: '+name)
    need(type(packet.get('statement')) is str and public_contracts.unordered_outer_declared(packet['statement']),'No unambiguous statement declaration')
    raw=packet.get('public_tests');need(type(raw) is list and bool(raw),'Missing pinned public cases')
    q=records.Problem('contract:'+entry['key'],'contract',entry['family'],'','',packet['statement'],'functional',entry=packet['entry'],params=packet['params'],public_tests=raw)
    bound=public_contracts.bind(public_examples.recover(q)).public_tests
    need(len(raw)==contract.get('public_tests') and len(bound)==len(raw),'Public case count mismatch')
    changed=False
    for before,after in zip(raw,bound):
        need(type(before) is dict and type(after) is dict,'Malformed public case')
        original_mode=before.get('compare','return');effective=after.get('compare','return')
        need(digest({k:v for k,v in before.items() if k!='compare'})==digest({k:v for k,v in after.items() if k!='compare'}),'Public data changed')
        need(effective==original_mode or (original_mode=='return' and effective=='return:unordered_outer' and type(before.get('expected')) is list),'Undeclared public comparison change')
        changed=changed or effective!=original_mode
    need(changed,'Profile must declare an actual public-only comparison change')
    descriptor={'mode':MODE,'policy_sha256':registry_ref['sha256'],'packet_sha256':allowed['packet']['sha256'],'statement_sha256':hashlib.sha256(packet['statement'].encode()).hexdigest(),'raw_public_sha256':digest(raw),'bound_public_sha256':digest(bound),'runtime':runtime}
    need(contract.get('public_comparison')==descriptor,'Contract does not bind coordinator comparison policy')
    refs=[registry_ref,allowed['packet']]+[{'path':str(path),'sha256':runtime[name]} for name,path in RUNTIME.items()]
    return descriptor,raw,bound,refs

def sandbox_result(payload,cases):
    fields={f.name for f in dataclasses.fields(sandbox.SandboxResult)}
    need(type(payload) is dict and set(payload)==fields,'Incomplete sandbox transcript fields')
    need(type(payload['exit_code']) is int and payload['exit_code']==0 and payload['signal'] is None,'Unclean sandbox transcript exit')
    need(payload['timed_out'] is False and payload['output_limit_exceeded'] is False,'Sandbox transcript resource failure')
    wall=payload['wall_seconds'];need(type(wall) in (int,float) and math.isfinite(wall) and 0<=wall<=8,'Invalid sandbox transcript duration')
    need(type(payload['notes']) is list and all(type(x) is str for x in payload['notes']),'Invalid sandbox notes')
    for name in ['stdout','stderr']:need(type(payload[name]) is str and len(payload[name].encode())<=4*1024**2,'Invalid sandbox output')
    rows=[json.loads(line) for line in payload['stdout'].splitlines() if line.strip()]
    need(len(rows)==len(cases)+1,'Incomplete sandbox result records')
    seen=set();done=False
    for row in rows:
        need(type(row) is dict,'Invalid sandbox record')
        if 'done' in row:
            need(set(row)=={'done'} and type(row['done']) is int and row['done']==len(cases) and not done,'Invalid completion record');done=True;continue
        i=row.get('i');need(type(i) is int and 0<=i<len(cases) and i not in seen,'Duplicate/malformed result index');seen.add(i)
        need('result' in row and 'error' not in row and 'load_error' not in row,'Failed candidate observation')
        need(not cases[i].get('kwargs') and digest(row.get('args_before'))==digest(cases[i]['args']) and digest(row.get('args_after'))==digest(cases[i]['args']),'Input mutation or call binding mismatch')
        need(row.get('returned_input_ids')==[] and row.get('input_node_values_preserved') is True,'Input alias/value observation failed')
    need(done and len(seen)==len(cases),'Missing completion or result')
    return sandbox.SandboxResult(**dict(payload,stdout=payload['stdout'].encode(),stderr=payload['stderr'].encode()))

def execution_profile(data,entry,contract,execution,review):
    descriptor,raw_public,bound_public,refs=profile(data,entry,contract)
    need(execution.get('public_comparison')==descriptor and execution.get('independent_comparison')=='unchanged','Execution comparison binding mismatch')
    need(review.get('public_comparison_reviewed') is True and review.get('public_comparison_sha256')==digest(descriptor),'Independent comparison review required')
    need(review.get('reviewer')!=contract['source_author'],'Source author cannot self-review')
    qref=execution.get('semantic_qualification');q=checked(qref)
    fref=execution.get('qualification_freeze');freeze=checked(fref)
    href=execution.get('host_tests');groups=checked(href)
    predecessor_ref=execution.get('strict_predecessor');predecessor=checked(predecessor_ref)
    need(q.get('source_author')==contract['source_author'],'Qualification source author mismatch')
    need(q.get('schema')=='algsolve.public-semantic-qualification.v1' and q.get('problem_key')==entry['key'],'Wrong qualification identity')
    need(q.get('freeze_sha256')==fref['sha256'] and q.get('host_tests_sha256')==href['sha256'],'Qualification evidence links mismatch')
    need(q.get('packet_sha256')==descriptor['packet_sha256'] and q.get('raw_public_sha256')==descriptor['raw_public_sha256'] and q.get('bound_public_sha256')==descriptor['bound_public_sha256'],'Qualification public binding mismatch')
    need(q.get('public_comparison')=='statement-declared:unordered_outer.v1' and q.get('independent_comparison')=='unchanged' and q.get('independent_sets')==entry['independent_sets'],'Qualification comparison mismatch')
    for key in ['candidate_bytes_changed','expected_outputs_changed','expected_values_in_sandbox']:need(q.get(key) is False,'Qualification safety declaration mismatch')
    need(freeze.get('schema')=='algsolve.public-semantic-qualification-freeze.v1' and freeze.get('problem_key')==entry['key'] and freeze.get('frozen_before_new_execution_and_independent_reload') is True,'Missing pre-execution freeze')
    need(freeze.get('packet_sha256')==descriptor['packet_sha256'] and freeze.get('statement_sha256')==descriptor['statement_sha256'] and freeze.get('raw_public_sha256')==descriptor['raw_public_sha256'] and freeze.get('bound_public_sha256')==descriptor['bound_public_sha256'],'Freeze public binding mismatch')
    need(freeze.get('independent_comparison')=='unchanged' and freeze.get('independent_sets')==entry['independent_sets'],'Freeze independent binding mismatch')
    need(freeze.get('limits')=={'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1024**3,'serial_cpus':1,'max_output_bytes':4*1024**2},'Qualification limits mismatch')
    runtime_refs=freeze.get('runtime');need(type(runtime_refs) is list and {str(Path(x['path']).resolve()):x['sha256'] for x in runtime_refs}=={str(path):descriptor['runtime'][name] for name,path in RUNTIME.items()},'Freeze runtime mismatch')
    for ref in runtime_refs:need(sha(ref['path'])==ref['sha256'],'Freeze runtime drift')
    folder=Path(fref['path']).parent
    files=freeze.get('files');need(type(files) is dict and bool(files),'Missing frozen files')
    for rel,want in files.items():
        path=(folder/rel).resolve();need(path.is_relative_to(folder.resolve()) and sha(path)==want,'Frozen input changed')
        refs.append({'path':str(path),'sha256':want})
    ext='py' if entry['language']=='python' else 'js'
    need(files.get(f"normalized/{entry['id']:04d}.{ext}")==contract['normalized_sha256'],'Qualification candidate freeze mismatch')
    need(predecessor.get('schema')=='algsolve.strict-predecessor.v1' and type(predecessor.get('files')) is list and bool(predecessor['files']),'Strict predecessor evidence required')
    need(files.get('strict-predecessor.json')==predecessor_ref['sha256'],'Strict predecessor not frozen')
    for ref in predecessor['files']:need(sha(ref['path'])==ref['sha256'],'Strict predecessor changed')
    expected_names=['public']+['independent:'+s['uid'] for s in entry['independent_sets']]
    need(type(groups) is list and [g.get('name') for g in groups]==expected_names and len(set(expected_names))==len(expected_names),'Missing/duplicate test group')
    need(digest(groups[0].get('raw_tests'))==digest(raw_public) and digest(groups[0].get('effective_tests'))==digest(bound_public),'Public transcript data/comparison changed')
    for group,testset in zip(groups[1:],entry['independent_sets']):
        raw=group.get('raw_tests');need(type(raw) is list and len(raw)==testset['tests'] and digest(raw)==testset['sha256'] and digest(group.get('effective_tests'))==digest(raw),'Independent tests or comparisons changed')
    matching=[row for row in q.get('results',[]) if row.get('variant')=='normalized' and row.get('language')==entry['language']]
    need(len(matching)==1 and matching[0].get('source_sha256')==contract['normalized_sha256'],'Qualification source mismatch')
    chunks=matching[0].get('chunks');need(type(chunks) is list,'Missing observation chunks')
    need(all(c.get('group') in expected_names for c in chunks),'Unexpected observation group')
    totals={};strict_totals={}
    for group in groups:
        offset=passed=strict_passed=0
        selected=[c for c in chunks if c.get('group')==group['name']]
        for chunk in selected:
            count=chunk.get('count');need(type(count) is int and 1<=count<=16 and type(chunk.get('offset')) is int and chunk['offset']==offset,'Missing/duplicate chunk range')
            raw=group['raw_tests'][offset:offset+count];effective=group['effective_tests'][offset:offset+count]
            need(len(raw)==count and digest(raw)==chunk.get('raw_cases_sha256') and digest(effective)==chunk.get('effective_cases_sha256'),'Chunk test identity mismatch')
            result=sandbox_result(chunk.get('result'),raw)
            verdict=judge._score_functional(result,validate.functional_tests(effective));strict=judge._score_functional(result,validate.functional_tests(raw))
            need(verdict.passed and verdict.tests_passed==count,'Observed semantic or independent comparison failed')
            need(verdict.to_dict()==chunk.get('verdict') and strict.to_dict()==chunk.get('strict_verdict') and chunk.get('mutation_alias_ok') is True,'Claimed transcript verdict differs')
            offset+=count;passed+=verdict.tests_passed;strict_passed+=strict.tests_passed
        need(offset==len(group['raw_tests']),'Incomplete test observations')
        totals[group['name']]=passed;strict_totals[group['name']]=strict_passed
    need(execution.get('public_total')==len(raw_public) and execution.get('public_passed')==totals['public'] and execution.get('strict_public_passed')==strict_totals['public'],'Public score receipt mismatch')
    need(execution.get('independent_passed')==sum(totals[n] for n in expected_names[1:]),'Independent score receipt mismatch')
    refs += [qref,fref,href,predecessor_ref]+predecessor['files']+runtime_refs
    declared=execution.get('artifacts',[])
    for ref in refs:need(any(x.get('sha256')==ref['sha256'] and Path(x['path']).resolve()==Path(ref['path']).resolve() for x in declared),'Execution omits underlying profile evidence')
    return refs
