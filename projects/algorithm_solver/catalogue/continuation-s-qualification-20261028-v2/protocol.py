"""Fixed S20 official controller v2: v1 with the refetched raw response hash recorded, not pinned.

Import/development never opens a candidate. Actual operation handlers require
explicit fixed pins and the existing Linux judge; no runtime provisioning.
"""
from dataclasses import asdict
from datetime import datetime,timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SOURCE=HERE.parent/'authored/continuation-s-20261028-v1'
OBSERVER=HERE.parent/'continuation-s-observers-20261028-v1'
IDS=(199,203,206,208,211,212,214,222,224,225)
BLOCKED=()
LANGUAGES=('python','javascript')
MANIFEST_SHA='30c940ab501d9c276d391ba40123d3d9ea71fe3857ac64eba04070ffa3f75526'
PROFILE_SHA='bf3481a50b40bb2da04b46e993da4857923ab84101edfabc01afa5ceb3775fa9'
SOURCE_REVIEW_SHA='586e961550864e992750897ecbdcdb19b37bfc4548352291899e7860d5bd4f5c'
OBSERVER_REVIEW_SHA='4006b13fa78e937009ab007f185f061788f8456712ce79634e68e2f01847cf69'
PLAN_SHA='e3aef8f45d87d776fdef85414ce1f8c2f5d3d4bad75b401b0b71f3edff6d6cf1'
SCHEMA='gamma.s20-official-execution.v2'
SCOPE_NOTE_SHA='d064f0501f9fd19d49639f3bde0fdb244b4554825cd1090f649e0ba50aa70f6d'
ARGV={'python':['/usr/bin/python3','-I','-S','harness.py'],'javascript':['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=256','harness.cjs']}
SAFETY_REVIEW_TEXT='Entire exact candidate and official entry/nodeconstructor bytes inspected. No filesystem/network/process/dynamic execution/eval,stdout,observer/prototype mutations or mutable module state. Only declared input-node mutation (203/206), ownclassstate mutation and localbuffers.'
FLAGS=('independent_source_review','exact_domain_interface','numeric_contract','mandatory_complexity','effects_contract','independent_references_and_boundaries','language_specific_official_entry','native_mutation_and_topology','original_node_constructor_and_identity')
SCOPE='Original 2111 finite cases plus explicit supplementary required-domain transport witnesses; no universal/held-out proof or canonical adoption.208 remains required-scope blocked.'
DEFINITION_QUERY='query questionData($titleSlug:String!){question(titleSlug:$titleSlug){questionFrontendId title titleSlug isPaidOnly content metaData codeSnippets{langSlug code}}}'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def pinned_profile():
    raw=(OBSERVER/'native-bindings.json').read_bytes()
    if sha(raw)!=PROFILE_SHA:raise ValueError('exact reviewed S profile required')
    value=json.loads(raw)
    if value['ids']!=list(IDS):raise ValueError('fixed S profile population')
    files={row['path']:row['sha256'] for row in value['files']}
    if len(files)!=len(value['files']):raise ValueError('duplicate observer closure path')
    for name,pin in files.items():
        if Path(name).name!=name or sha((OBSERVER/name).read_bytes())!=pin:raise ValueError('reviewed observer/helper drift')
    value['files']=files
    return value


PROFILE=pinned_profile()
E=load(HERE.parent/'continuation-qualification-20261028-v1/protocol.py','s20_existing_judge_engine')
PLAN=load(OBSERVER/'plan.py','s20_reviewed_plan')
PLAN.references()
CHECK=load(OBSERVER/'host_check.py','s20_reviewed_host_check')
exact,read_json,write=E.exact,E.read_json,E.write
LOADED={Path(p):sha(Path(p).read_bytes()) for p in (__file__,E.__file__,E.sandbox.__file__,E.authorize_before_open.__code__.co_filename,E.bounded_regular_read.__code__.co_filename,PLAN.__file__,CHECK.__file__)}


def inventory(manifest,profile=PROFILE):
    wanted={(pid,lang) for pid in IDS for lang in LANGUAGES};result={}
    for row in manifest['source_inventory']:
        pid,language=row.get('id'),row.get('language');key=pid,language
        if type(pid) is not int or key not in wanted or key in result:raise ValueError('unknown, Boolean or duplicate S source identity')
        if row['path']!=f'{language}/{pid}.'+('py' if language=='python' else 'js') or row['semantics_path']!=f'semantics/{pid}.json':raise ValueError('exact fixed S source locator')
        result[key]=row
    if set(result)!=wanted:raise ValueError('missing exact S source slots')
    return result


def metadata():
    raw=(SOURCE/'manifest.json').read_bytes()
    if sha(raw)!=MANIFEST_SHA:raise ValueError('exact S source manifest drift')
    manifest=read_json(SOURCE/'manifest.json');rows=inventory(manifest)
    if sha((SOURCE/'assignment.public-safe.json').read_bytes())!=manifest['assignment_sha256']:raise ValueError('source assignment metadata drift')
    PLAN.references() # verifies original source-blind reference owner, never sources
    return rows,read_json(SOURCE/'contracts.json')


def gate(args):
    value=E.gate_file(args.gate,args.gate_sha256)
    from catalogue.boundary_policy import ARTIFACTS
    if set(value['artifact_paths'])!=set(ARTIFACTS) or set(value['trusted_hashes'])!=set(ARTIFACTS):raise ValueError('exact six boundary anchors required')
    return value


def read_statement(g,pid,path):
    if type(pid) is not int or pid not in IDS:raise ValueError('blocked/unassigned statement open')
    for lang in LANGUAGES:E.access(g,pid,lang,'statement')
    return E.bounded_regular_read(path,maximum_bytes=4*1024**2)


def definitions(args,g,contract):
    result={}
    for spec in contract['problems']:
        pid=spec['id']
        if type(pid) is not int or pid not in IDS:raise ValueError('fixed S official identity required')
        raw=read_statement(g,pid,args.statements/f'{pid}.json');q=json.loads(raw)['data']['question']
        snippets={s['langSlug']:s['code'] for s in q['codeSnippets'] if s['langSlug'] in ('python3','javascript')}
        # The full response also carries every other language's template, so its raw hash
        # can change while content, API and the selected templates stay identical.
        if (q.get('questionFrontendId')!=str(pid) or q.get('titleSlug')!=spec['slug'] or q.get('isPaidOnly') is not False or not isinstance(q.get('content'),str) or sha(q['content'].encode())!=spec['official_content_sha256'] or sha(encoded(json.loads(q['metaData'])))!=sha(encoded(spec['official_api'])) or {k:sha(v.encode()) for k,v in snippets.items()}!=spec['actual_language_templates_sha256']):raise ValueError('exact official definition/API/language template drift')
        result[str(pid)]={'definition_sha256':sha(raw),'original_definition_sha256':spec['official_definition_sha256'],'content_sha256':spec['official_content_sha256'],'api_sha256':sha(encoded(spec['official_api'])),'language_template_sha256':spec['actual_language_templates_sha256']}
    if set(result)!={str(pid) for pid in IDS}:raise ValueError('selected official definitions incomplete')
    return result


def cases_and_plan(args,g):
    owner,freeze=PLAN.references()
    data=owner.build_cases()
    if tuple(data)!=IDS or sha(owner.encoded(data))!=freeze['case_sha256']:raise ValueError('original independent cases drift')
    raw=args.plan.read_bytes()
    if sha(raw)!=PLAN_SHA:raise ValueError('exact frozen prospective S plan required')
    value=read_json(args.plan)
    if value['reference_freeze_sha256']!=PLAN.REFERENCE_FREEZE_SHA or sha(owner.encoded(data))!=freeze['case_sha256']:raise ValueError('plan/reference binding')
    rebuilt={str(pid):PLAN.batch_plan(pid,rows,owner.oracle) for pid,rows in data.items()}
    if not exact(rebuilt,value['plans']):raise ValueError('case admission/batching differs from frozen plan')
    return data,rebuilt


def binding(pid,lang,row,contract):
    spec=next(p for p in contract['problems'] if p['id']==pid);suffix='py' if lang=='python' else 'cjs';template='python3' if lang=='python' else 'javascript'
    return {'source_sha256':row['sha256'],'semantics_sha256':row['semantics_sha256'],'source_path':str((SOURCE/row['path']).relative_to(ROOT)),
            'source_manifest_sha256':MANIFEST_SHA,'source_assignment_sha256':read_json(SOURCE/'manifest.json')['assignment_sha256'],
            'reference_freeze_sha256':PLAN.REFERENCE_FREEZE_SHA,'reference_sha256':sha((SOURCE/'oracles.py').read_bytes()),'case_generator_sha256':sha((SOURCE/'cases.py').read_bytes()),'contracts_sha256':sha((SOURCE/'contracts.json').read_bytes()),
            'observer_profile_sha256':PROFILE_SHA,'observer_sha256':PROFILE['files'][f'harness.{suffix}'],'native_graphs_sha256':PROFILE['files'][f'native_graphs.{suffix}'],'host_checker_sha256':PROFILE['files']['host_check.py'],
            'definition_response_sha256':spec['official_definition_sha256'],'definition_content_sha256':spec['official_content_sha256'],'interface_api_sha256':sha(encoded(spec['official_api'])),
            'official_language_template_sha256':spec['actual_language_templates_sha256'][template]}


def accept_reviews(value,rows,contract):
    supplied={}
    if value is not None:
        if value.get('schema')!='gamma.s-independent-mandatory-static-review.v1' or type(value.get('candidate_executions')) is not int or value['candidate_executions']!=0 or value.get('static_failures')!=[] or type(value.get('static_reviewed_programs')) is not int or value['static_reviewed_programs']!=len(rows):raise ValueError('source review root binding/count')
        for review in value['programs']:
            pid,lang=review.get('problem_id'),review.get('language');key=pid,lang
            if type(pid) is not int or key not in rows or key in supplied:raise ValueError('unknown/Boolean/duplicate review identity')
            supplied[key]=review
    result={}
    for (pid,lang),row in rows.items():
        record=supplied.get((pid,lang),{});pins=binding(pid,lang,row,contract)
        approved=all(record.get(k)==v for k,v in pins.items()) and isinstance(record.get('reviewer'),str) and bool(record['reviewer'].strip()) and all(record.get(flag) is True for flag in FLAGS) and record.get('source_safety')==SAFETY_REVIEW_TEXT
        result[f'{pid}:{lang}']={'approved':approved,'record':record,'reason':None if approved else 'missing, false, or differently bound independent source review'}
    return result


def reviews(args,rows,contract):
    if args.review is None:return accept_reviews(None,rows,contract)
    if sha(args.review.read_bytes())!=SOURCE_REVIEW_SHA:raise ValueError('exact independent S20 source review required')
    return accept_reviews(read_json(args.review),rows,contract)


def observer_review(args):
    if args.observer_review is None:raise ValueError('separate observer review required; never a source-review substitute')
    raw=args.observer_review.read_bytes()
    if sha(raw)!=OBSERVER_REVIEW_SHA:raise ValueError('exact independent observer receipt required')
    value=read_json(args.observer_review)
    if value.get('profile_sha256')!=PROFILE_SHA or value.get('source_review_sha256')!=SOURCE_REVIEW_SHA or any(PROFILE['files'].get(name)!=pin for name,pin in value['reviewed_helpers'].items()):raise ValueError('observer receipt/profile/source-review binding')
    return {'sha256':sha(raw),'record':value}


def artifacts(g,rows):
    if any(sha(path.read_bytes())!=pin for path,pin in LOADED.items()):raise ValueError('loaded controller/judge/helper drift; restart with reviewed code')
    result={str(path.relative_to(ROOT)):sha(path.read_bytes()) for path in LOADED}
    # Static owner closure only: a freeze/report written beside this code must
    # not become a new input and invalidate its own execution identity.
    for name in ('protocol.py','test_protocol.py','README.md','required-domain-supplement.json','validation.json'):
        path=HERE/name
        if path.exists():result[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    if sha((OBSERVER/'native-bindings.json').read_bytes())!=PROFILE_SHA:raise ValueError('reviewed profile drift')
    result[str((OBSERVER/'native-bindings.json').relative_to(ROOT))]=PROFILE_SHA
    for name,pin in PROFILE['files'].items():
        path=OBSERVER/name
        if sha(path.read_bytes())!=pin:raise ValueError('reviewed code drift')
        result[str(path.relative_to(ROOT))]=pin
    _,freeze=PLAN.references()
    for name,pin in freeze['files'].items():result[str((SOURCE/name).relative_to(ROOT))]=pin
    for name in ('manifest.json','assignment.public-safe.json','pre-source-reference-freeze.json'):
        path=SOURCE/name;result[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    for (pid,lang),row in rows.items():
        for field,pinfield in (('path','sha256'),('semantics_path','semantics_sha256')):
            E.access(g,pid,lang,'source');path=SOURCE/row[field]
            raw=E.bounded_regular_read(path,maximum_bytes=1024**2)
            if sha(raw)!=row[pinfield]:raise ValueError('source/semantics changed')
            result[str(path.relative_to(ROOT))]=sha(raw)
    return result


def prepare(args):
    _,contract=metadata();g=gate(args);args.statements.mkdir(parents=True,exist_ok=False)
    for spec in contract['problems']:
        pid=spec['id']
        for lang in LANGUAGES:
            E.access(g,pid,lang,'source');E.access(g,pid,lang,'statement')
        request=urllib.request.Request('https://leetcode.com/graphql/',data=encoded({'query':DEFINITION_QUERY,'variables':{'titleSlug':spec['slug']}}),headers={'Content-Type':'application/json','User-Agent':'Gamma public-domain qualification'})
        with urllib.request.urlopen(request,timeout=25) as response:raw=response.read(4*1024**2+1)
        with (args.statements/f'{pid}.json').open('xb') as stream:stream.write(raw);stream.flush();E.os.fsync(stream.fileno())
        if len(raw)>4*1024**2:raise ValueError('official response bound exceeded; truncated response retained')
    pins=definitions(args,g,contract);write(args.statements/'refetch-receipt.json',{'selected_ids':list(IDS),'pins':pins,'candidate_executions':0})
    return {'public_definitions':len(pins),'language_template_sets':len(pins),'candidate_executions':0}


def required_blockers(contract):
    """Symbolic required witness: no long word/trace/packet is allocated."""
    spec=next(p for p in contract['problems'] if p['id']==208)
    if type(spec['id']) is not int or type(spec['domain']['word_prefix_length']) is not list or any(type(n) is not int for n in spec['domain']['word_prefix_length']) or spec['domain']['word_prefix_length']!=[1,2000] or type(spec['domain']['calls_max']) is not int or spec['domain']['calls_max']!=30000 or spec['domain']['alphabet']!='lowercase':raise ValueError('exact208official domain evidence changed')
    if PLAN.MAX_HOST_PACKET_BYTES!=16777216 or E.LIMITS.max_output_bytes!=16777216:raise ValueError('unchanged16MiB envelopes required')
    calls,length=10000,2000
    characters=calls*length;args_bytes=15+calls*(length+14);echo_bytes=2*args_bytes
    return {'208':[{'schema':'gamma.s208-required-domain-transport-blocker.v1','problem_id':208,'witness_id':'legal-Trie-10000-inserts-x2000-ASCII-symbolic-v1','required':True,'status':'blocked_transport',
        'witness':{'constructor':'Trie()','method':'insert','calls':calls,'word_recipe':{'lowercase_character':'a','repeat_count':length},'same_receiver_required':True,'duplicate_insertions_permitted':True,'materialized':False},
        'official_evidence':{'definition_response_sha256':spec['official_definition_sha256'],'definition_content_sha256':spec['official_content_sha256'],'interface_api_sha256':sha(encoded(spec['official_api'])),'word_length':[1,2000],'method_calls_max':30000},
        'proof':{'raw_word_utf8_lower_bound_bytes':characters,'exact_compact_args_bytes':args_bytes,'input_packet_lower_bound_bytes':args_bytes,'argument_echo_stdout_lower_bound_bytes':echo_bytes,'args_formula':'15+N*(L+14)','host_input_cap_bytes':PLAN.MAX_HOST_PACKET_BYTES,'stdout_cap_bytes':E.LIMITS.max_output_bytes},
        'scope_note_sha256':SCOPE_NOTE_SHA,'original_case_freeze_unchanged':True,'original_case_count':2111,'not_an_extra_executed_case':True,'claim':'Existing raw one-receiver packet/argument-echo profile cannot carry this legal witness. Original finite passes cannot establish complete required scope or qualification. No cap raise, trace split, compression, silent omission or trie-memory impossibility claim.'}]}


def scope_note(args,contract):
    if args.scope_note is None:raise ValueError('exact supplementary208domain evidence note required')
    raw=args.scope_note.read_bytes()
    if sha(raw)!=SCOPE_NOTE_SHA:raise ValueError('supplementary208note hash differs')
    value=read_json(args.scope_note);spec=next(p for p in contract['problems'] if p['id']==208);evidence=value['official_evidence'];calculation=value['bounded_calculation'];blocker=required_blockers(contract)['208'][0]
    if (value.get('schema')!='gamma.s208-known-domain-transport-limitation.v1' or type(value.get('problem_id')) is not int or value['problem_id']!=208 or evidence['response_sha256']!=spec['official_definition_sha256'] or evidence['content_sha256']!=spec['official_content_sha256'] or evidence['api_sha256']!=sha(encoded(spec['official_api'])) or calculation['exact_args_json_bytes']!=blocker['proof']['exact_compact_args_bytes'] or calculation['two_argument_echoes_lower_bound_bytes']!=blocker['proof']['argument_echo_stdout_lower_bound_bytes'] or value.get('giant_trace_allocated') is not False or value.get('cap_changes')!=0):raise ValueError('required208note/official-evidence binding differs')
    prepared=value['prepared_scope']
    if prepared['source_manifest_sha256']!=MANIFEST_SHA or prepared['source_review_sha256']!=SOURCE_REVIEW_SHA or prepared['prepared_case_freeze_sha256']!=PLAN.REFERENCE_FREEZE_SHA or type(prepared['frozen_cases']) is not int or prepared['frozen_cases']!=2111:raise ValueError('supplementary note/original lineage differs')
    return {'sha256':sha(raw),'record':value}


def freeze(args):
    runtime=E.runtime();raw=args.preflight.read_bytes()
    if sha(raw)!=args.preflight_sha256 or re.search(rb'\b37 passed\b',raw) is None:raise ValueError('exact passing existing37-check Linux judge preflight required')
    rows,contract=metadata();g=gate(args);statement_pins=definitions(args,g,contract);data,plans=cases_and_plan(args,g)
    review=reviews(args,rows,contract);observer=observer_review(args);pins=artifacts(g,rows)
    value={'schema':SCHEMA,'ids':list(IDS),'blocked_ids':list(BLOCKED),'program_count':len(rows),'profile_sha256':PROFILE_SHA,'source_manifest_sha256':MANIFEST_SHA,
           'artifact_hashes':pins,'runtime':runtime,'argv':ARGV,'limits':asdict(E.LIMITS),'host_packet_bytes':PLAN.MAX_HOST_PACKET_BYTES,'plan_sha256':PLAN_SHA,
           'statement_pins':statement_pins,'case_sha256':sha(encoded(data)),'case_counts':{str(p):len(v) for p,v in data.items()},'plans':plans,'required_scope_blockers':required_blockers(contract),'scope_note':scope_note(args,contract),'source_reviews':review,
           'source_review_sha256':SOURCE_REVIEW_SHA if args.review is not None else None,'observer_review':observer,'preflight_sha256':args.preflight_sha256,
           'execution_gate_sha256':args.gate_sha256,'boundary_trusted_hashes':g['trusted_hashes'],'scope':SCOPE,'canonical_admission_changed':False}
    write(args.freeze,value)
    return {'freeze_sha256':sha(args.freeze.read_bytes()),'programs':len(rows),'source_reviews_approved':sum(r['approved'] for r in review.values()),'candidate_executions':0}


def verified(args,live):
    raw=args.freeze.read_bytes()
    if sha(raw)!=args.freeze_sha256:raise ValueError('exact execution freeze identity required')
    value=read_json(args.freeze)
    if value.get('schema')!=SCHEMA or not exact(value.get('ids'),list(IDS)) or not exact(value.get('blocked_ids'),list(BLOCKED)) or value.get('profile_sha256')!=PROFILE_SHA or value.get('source_manifest_sha256')!=MANIFEST_SHA or not exact(value.get('limits'),asdict(E.LIMITS)) or not exact(value.get('argv'),ARGV) or value.get('host_packet_bytes')!=PLAN.MAX_HOST_PACKET_BYTES or value.get('plan_sha256')!=PLAN_SHA:raise ValueError('fixed S execution policy differs')
    rows,contract=metadata();g=gate(args)
    if type(value.get('program_count')) is not int or value['program_count']!=len(rows):raise ValueError('dynamic selected program count differs')
    if not exact(g['trusted_hashes'],value['boundary_trusted_hashes']):raise ValueError('six-anchor boundary drift')
    if live and (args.gate_sha256!=value['execution_gate_sha256'] or not exact(E.runtime(),value['runtime'])):raise ValueError('exact execution gate/runtime drift')
    if not exact(value.get('required_scope_blockers'),required_blockers(contract)) or not exact(value.get('scope_note'),scope_note(args,contract)):raise ValueError('supplementary required-scope witness/evidence drift')
    if not exact(artifacts(g,rows),value['artifact_hashes']) or not exact(definitions(args,g,contract),value['statement_pins']):raise ValueError('source/helper/definition drift')
    data,plans=cases_and_plan(args,g)
    if sha(encoded(data))!=value['case_sha256'] or not exact({str(p):len(v) for p,v in data.items()},value['case_counts']) or not exact(plans,value['plans']):raise ValueError('reference cases/plan drift')
    if value.get('source_review_sha256')!=(SOURCE_REVIEW_SHA if args.review is not None else None) or not exact(reviews(args,rows,contract),value['source_reviews']) or not exact(observer_review(args),value['observer_review']):raise ValueError('review binding drift')
    return value,rows,g,data


def verdict(pid,lang,cases,indices,status,stdout):
    if type(status.get('exit_code')) is not int or status['exit_code']!=0 or status.get('timed_out') is not False or status.get('output_limit_exceeded') is not False:return [{'case':i,'reason':'sandbox_process_failure'} for i in indices]
    try:records=parse_rows(stdout,len(indices))
    except (ValueError,TypeError,UnicodeError):return [{'case':i,'reason':'observation_protocol'} for i in indices]
    failures=[]
    for i,record in zip(indices,records):
        accepted,reason=CHECK.check_observation(pid,cases[i]['args'],record,lang)
        if not accepted:failures.append({'case':i,'reason':reason})
    return failures


def parse_rows(raw,count):
    def pairs(items):
        row={}
        for key,value in items:
            if key in row:raise ValueError('duplicate observation JSON key')
            row[key]=value
        return row
    records=[json.loads(line,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))) for line in raw.decode('utf8').splitlines()]
    if len(records)!=count+1 or type(records[-1]) is not dict or set(records[-1])!={'done'} or type(records[-1]['done']) is not int or records[-1]['done']!=count:raise ValueError('exact complete native stream required')
    for i,row in enumerate(records[:-1]):
        if type(row) is not dict or type(row.get('i')) is not int or row['i']!=i or 'error' in row and set(row)!={'i','error'}:raise ValueError('native row identity/order/shape')
    return records[:-1]


def summary(pid,lang,cases,plan,total,failures,review,blockers):
    if type(pid) is not int or pid not in IDS or lang not in LANGUAGES:raise ValueError('fixed summary identity')
    if pid==208 and not blockers:raise ValueError('required208supplementary witness may not be omitted')
    planned=sum(len(b['indices']) for b in plan['batches']);finite=total==planned and total>0 and not failures and not plan['blocked_cases'] and plan['admitted_distinct_cases']==len(cases)
    complete=finite and not blockers
    return {'problem_id':pid,'language':lang,'original_distinct_cases':len(cases),'planned_calls':planned,'dispatched_call_slots':total,'failures':failures,'original_plan_transport_blocked_cases':plan['blocked_cases'],
            'source_review_approved':review['approved'],'blocked_review':not review['approved'],'original_finite_suite_passed':finite,'required_scope_transport_blockers':blockers,
            'complete_required_scope_passed':complete,'qualified':complete and review['approved'],'canonical_admission_changed':False,'scope':SCOPE}


def run_or_replay(args,replay=False):
    value,rows,g,data=verified(args,not replay)
    identity={'freeze_sha256':args.freeze_sha256,'profile_sha256':PROFILE_SHA,'runtime':value['runtime'],'artifact_hashes':value['artifact_hashes']}
    if not replay:args.output.mkdir(parents=True,exist_ok=False);write(args.output/'identity.json',identity)
    if not exact(read_json(args.output/'identity.json'),identity):raise ValueError('saved run identity differs')
    summaries=[];raw_hashes={};batches=0
    for (pid,lang),source in rows.items():
        plan=value['plans'][str(pid)];review=value['source_reviews'][f'{pid}:{lang}'];total=0;failures=[]
        if review['approved']:
            for index,entry in enumerate(plan['batches']):
                indices=entry['indices'];wire=PLAN.encoded(PLAN.packet(pid,data[pid],indices));stem=args.output/f'{pid}-{lang}-{index:04d}'
                if len(wire)!=entry['host_input_bytes'] or len(wire)>PLAN.MAX_HOST_PACKET_BYTES or max(entry['projected_output_bytes'].values())>E.LIMITS.max_output_bytes:raise ValueError('frozen packet/output envelope differs')
                start={'problem_id':pid,'language':lang,'indices':indices,'inputs_sha256':sha(wire),'input_bytes':len(wire),'source_sha256':source['sha256'],'source_path':source['path'],'plan':entry}
                if not replay:
                    E.access(g,pid,lang,'source');body=E.bounded_regular_read(SOURCE/source['path'],maximum_bytes=1024**2)
                    if sha(body)!=source['sha256']:raise ValueError('source changed immediately before dispatch')
                    ext='py' if lang=='python' else 'cjs';files={'program.'+ext:body,'inputs.json':wire}
                    for name in (f'harness.{ext}',f'native_graphs.{ext}'):
                        raw=(OBSERVER/name).read_bytes()
                        if sha(raw)!=PROFILE['files'][name]:raise ValueError('native observer changed before dispatch')
                        files[name]=raw
                    write(str(stem)+'.start.json',start)
                    try:result=E.sandbox.run(ARGV[lang],files=files,limits=E.LIMITS)
                    except Exception as error:
                        write(str(stem)+'.dispatch-error.json',{'exception_type':type(error).__name__,'message':str(error)[:4096],'process_result_available':False,'execution_outcome':'uncertain; inspect before any retry'});raise
                    status=asdict(result)
                    for name in ('stdout','stderr'):
                        raw=status.pop(name)
                        with Path(str(stem)+'.'+name).open('xb') as f:f.write(raw);f.flush();E.os.fsync(f.fileno())
                        status[name+'_sha256']=sha(raw);status[name+'_bytes']=len(raw)
                    write(str(stem)+'.result.json',status) # raw evidence precedes verdict
                if not exact(read_json(str(stem)+'.start.json'),start):raise ValueError('saved packet/source/start drift')
                status=read_json(str(stem)+'.result.json');streams={}
                for name in ('stdout','stderr'):
                    raw=E.bounded_regular_read(Path(str(stem)+'.'+name),maximum_bytes=E.LIMITS.max_output_bytes)
                    if sha(raw)!=status.get(name+'_sha256') or type(status.get(name+'_bytes')) is not int or len(raw)!=status[name+'_bytes']:raise ValueError('raw evidence hash/byte count drift')
                    streams[name]=raw;raw_hashes[Path(str(stem)+'.'+name).name]=sha(raw)
                failures.extend(verdict(pid,lang,data[pid],indices,status,streams['stdout']));total+=len(indices);batches+=1
        row=summary(pid,lang,data[pid],plan,total,failures,review,value['required_scope_blockers'].get(str(pid),[]));summaries.append(row);path=args.output/f'{pid}-{lang}.summary.json'
        if replay:
            if not exact(read_json(path),row):raise ValueError('summary differs from raw replay')
        else:write(path,row)
    report={'schema':SCHEMA,'freeze_sha256':args.freeze_sha256,'program_count':len(summaries),'programs':summaries,'required_scope_blockers':value['required_scope_blockers'],'canonical_admission_changed':False,'scope':SCOPE}
    if replay:
        if not exact(read_json(args.output/'report.json'),report):raise ValueError('aggregate differs from raw replay')
        write(args.output/'replay.json',{'schema':SCHEMA,'freeze_sha256':args.freeze_sha256,'programs_replayed':len(summaries),'batches_replayed':batches,'raw_stream_hashes':raw_hashes,'all_observations_match_report':True,'candidate_execution_on_replay_host':False,'original_execution_gate_sha256':value['execution_gate_sha256'],'replay_gate_sha256':args.gate_sha256})
    else:write(args.output/'report.json',report)
    return {'programs':len(summaries),'sandbox_batches':batches,'dispatched_call_slots':sum(r['dispatched_call_slots'] for r in summaries),'original_finite_suite_pass_programs':sum(r['original_finite_suite_passed'] for r in summaries),'complete_required_scope_pass_programs':sum(r['complete_required_scope_passed'] for r in summaries),'qualified_programs':sum(r['qualified'] for r in summaries),'required_scope_transport_blocked_programs':sum(bool(r['required_scope_transport_blockers']) for r in summaries),'blocked_review_programs':sum(r['blocked_review'] for r in summaries),'replayed':replay}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('prepare','freeze','run','replay'))
    for name in ('gate','statements','freeze','preflight','review','observer-review','scope-note','plan','output'):parser.add_argument('--'+name,type=Path)
    for name in ('gate-sha256','freeze-sha256','preflight-sha256'):parser.add_argument('--'+name)
    args=parser.parse_args();result=prepare(args) if args.operation=='prepare' else freeze(args) if args.operation=='freeze' else run_or_replay(args,args.operation=='replay')
    print(encoded(result).decode())

if __name__=='__main__':main()
