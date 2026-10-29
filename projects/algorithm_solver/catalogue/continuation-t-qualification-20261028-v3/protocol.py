"""T16 observer-cost rerun controller v3: v2 with observer profile v2 for selected programs.

Binds continuation-t-observers-20261028-v2 (same checks and records as v1,
lower --jitless cost) and dispatches only RERUN. Limits, argv, cases, plan and
host checker are unchanged. Reviews must be new receipts that bind the v2
observer hashes; until they are pinned below, freeze and run fail closed.

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
import stat
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SOURCE=HERE.parent/'authored/continuation-t-20261028-v1'
OBSERVER=HERE.parent/'continuation-t-observers-20261028-v2'
PRIOR_LANE='continuation-t-qualification-20261028-v2'
PRIOR_PROFILE_SHA='dd8f26fcd0cbd975de07049ef7b423540eb6dcbb7c2c1704179c1582ba8b56ea'
RERUN=((234,'javascript'),(235,'javascript'),(236,'javascript'))
IDS=(226,230,232,233,234,235,236,237)
BLOCKED=(243,245)
LANGUAGES=('python','javascript')
MANIFEST_SHA='7b1e566f34b70df1452343010e0bfb54e748b61a5df37c671cefaa3358244129'
PROFILE_SHA='05f0f0111e7753284165ce9517654aa349fbce8941518d75519355ad71711083'
PRIOR_SOURCE_REVIEW_SHA='1c908db7b6ade8452c6670007abd70775a3ca5701820cc4c8a9eafb852dfacac'
# Pin the exact independent receipt that re-reviews RERUN against observer v2
# (schema gamma.independent-source-observer-static-review.v1, observer_profile_sha256=PROFILE_SHA,
# selected_programs=len(RERUN)). None keeps freeze/run fail-closed.
SOURCE_REVIEW_SHA=None

PLAN_SHA='16e73e4f2e8a8b2d9b919305faba5e1ca03b1865437459f9e41fd34bf1508474'
SCHEMA='gamma.t16-official-execution.v3'
FLAGS=('independent_source_review','source_safety','exact_domain_interface','numeric_contract','mandatory_complexity','effects_contract','independent_references_and_boundaries','language_specific_official_entry','native_mutation_and_topology','original_node_constructor_and_identity','stateful_receiver_and_method_types')
SCOPE='Finite independently referenced official T interfaces, exact original variants; no universal/held-out qualification or canonical adoption.'
DEFINITION_QUERY='query questionData($titleSlug: String!) { question(titleSlug:$titleSlug) { questionId questionFrontendId title titleSlug isPaidOnly content exampleTestcaseList metaData } }'
TEMPLATE_QUERY='query template($titleSlug:String!){question(titleSlug:$titleSlug){questionFrontendId titleSlug codeSnippets{langSlug code}}}'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


# These are historical source-free Mac diagnostics, not execution helpers.
# The source-only delivery deliberately excludes their raw output. Never recreate
# those bytes or treat their summaries as verified raw evidence.
# Observer v2 ships no historical stress raw files; its cost evidence is
# observer-cost-measurements.json, a hash-verified profile file.
ARCHIVED_STRESS_FILES=frozenset()


def profile_file_status(name,pin):
    if Path(name).name!=name:raise ValueError('reviewed observer/helper locator')
    path=OBSERVER/name
    try:mode=path.lstat().st_mode
    except FileNotFoundError:
        if name in ARCHIVED_STRESS_FILES:return {'expected_sha256':pin,'status':'unavailable_in_source_only_delivery'}
        raise
    if not stat.S_ISREG(mode):raise ValueError('reviewed observer/helper must be a regular file')
    if sha(path.read_bytes())!=pin:raise ValueError('reviewed observer/helper drift')
    return {'expected_sha256':pin,'status':'hash_verified'}


def historical_stress_evidence():
    return {name:profile_file_status(name,PROFILE_FILES[name]) for name in sorted(ARCHIVED_STRESS_FILES)}


def rerun_record():
    return {'prior_lane':PRIOR_LANE,'prior_observer_profile_sha256':PRIOR_PROFILE_SHA,'prior_source_review_sha256':PRIOR_SOURCE_REVIEW_SHA,
            'selection':[[pid,lang] for pid,lang in RERUN],'prior_failure':'sandbox_process_failure: SIGKILL exit 137 near 3.0 CPU s on large batches; observer-alone cost',
            'prior_raw_results_retained':True,'checks_changed':False,'limits_changed':False}


def pinned_profile():
    raw=(OBSERVER/'native-bindings.json').read_bytes()
    if sha(raw)!=PROFILE_SHA:raise ValueError('exact reviewed T profile required')
    value=json.loads(raw)
    if value['active_ids']!=list(IDS) or [r['id'] for r in value['excluded']]!=list(BLOCKED) or value.get('previous_profile_sha256')!=PRIOR_PROFILE_SHA:raise ValueError('fixed T profile population/lineage')
    for row in value['files']:
        name,pin=row['path'],row['sha256']
        profile_file_status(name,pin)
    if not ARCHIVED_STRESS_FILES.issubset({r['path'] for r in value['files']}):raise ValueError('historical stress inventory differs')
    return value


PROFILE=pinned_profile()
PROFILE_FILES={r['path']:r['sha256'] for r in PROFILE['files']}
ARGV={'python':['/usr/bin/python3','-I','-S','harness.py'],'javascript':['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=256','harness.cjs']}
E=load(HERE.parent/'continuation-qualification-20261028-v1/protocol.py','t16_existing_judge_engine')
PLAN=load(OBSERVER/'plan.py','t16_reviewed_plan')
CHECK=load(OBSERVER/'host_check.py','t16_reviewed_host_check')
exact,read_json,write=E.exact,E.read_json,E.write
LOADED={Path(p):sha(Path(p).read_bytes()) for p in (__file__,E.__file__,E.sandbox.__file__,E.authorize_before_open.__code__.co_filename,E.bounded_regular_read.__code__.co_filename,PLAN.__file__,CHECK.__file__)}


def inventory(manifest,profile=PROFILE):
    if manifest.get('active_ids')!=list(IDS) or [r['id'] for r in manifest.get('excluded',[])]!=list(BLOCKED):raise ValueError('manifest selection differs')
    wanted={(pid,lang) for pid in IDS for lang in LANGUAGES};result={}
    for row in manifest['source_inventory']:
        pid,language=row.get('id'),row.get('language');key=pid,language
        if type(pid) is not int or key not in wanted or key in result:raise ValueError('unknown, Boolean or duplicate T source identity')
        if row['path']!=f'{language}/{pid}.'+('py' if language=='python' else 'js') or row['semantics_path']!=f'semantics/{pid}.json':raise ValueError('exact fixed T source locator')
        result[key]=row
    if set(result)!=wanted:raise ValueError('missing exact T source slots')
    return result


def metadata():
    raw=(SOURCE/'manifest.json').read_bytes()
    if sha(raw)!=MANIFEST_SHA:raise ValueError('exact T source manifest drift')
    manifest=read_json(SOURCE/'manifest.json');rows=inventory(manifest)
    rows={key:row for key,row in rows.items() if key in RERUN} # all 16 slots verified above; dispatch only RERUN
    if tuple(rows)!=RERUN:raise ValueError('exact rerun selection required')
    for name,pin in PROFILE['source_owner_sourcefree_pins'].items():
        if Path(name).name!=name or sha((SOURCE/name).read_bytes())!=pin:raise ValueError('assignment/source-interface metadata drift')
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
    receipt=read_json(args.statements/'refetch-receipt.json')
    if not exact(receipt.get('selected_ids'),list(IDS)) or not exact(receipt.get('blocked_ids'),list(BLOCKED)) or receipt.get('candidate_executions')!=0:raise ValueError('executor public refetch receipt population')
    result={}
    for spec in contract['problems']:
        pid=spec['id']
        if type(pid) is not int or pid not in IDS:raise ValueError('unexpected specification identity')
        raw=read_statement(g,pid,args.statements/f'{pid}.json');q=json.loads(raw)['data']['question'];pin=spec['definition']
        snippets={s['langSlug']:s['code'] for s in q['codeSnippets'] if s['langSlug'] in ('python3','javascript')}
        if (q.get('questionFrontendId')!=str(pid) or q.get('titleSlug')!=spec['slug'] or q.get('isPaidOnly') is not False or not isinstance(q.get('content'),str) or sha(q['content'].encode())!=pin['content_sha256'] or not exact(json.loads(q['metaData']),spec['raw_fixture_metadata']) or {k:sha(v.encode()) for k,v in snippets.items()}!=pin['actual_template_sha256']):raise ValueError('exact original definition/API/templates drift')
        fetched=receipt['pins'].get(str(pid),{})
        if fetched.get('refetched_response_sha256')!=sha(raw) or fetched.get('original_response_sha256')!=pin['response_sha256'] or fetched.get('content_sha256')!=pin['content_sha256'] or fetched.get('api_sha256')!=sha(encoded(spec['raw_fixture_metadata'])) or not exact(fetched.get('templates'),pin['actual_template_sha256']):raise ValueError('refetch receipt/raw/content/API/template binding')
        result[str(pid)]={'definition_sha256':sha(raw),'original_definition_sha256':pin['response_sha256'],'content_sha256':pin['content_sha256'],'api_sha256':sha(encoded(spec['raw_fixture_metadata'])),'language_template_sha256':pin['actual_template_sha256']}
    if set(result)!={str(pid) for pid in IDS}:raise ValueError('selected official definitions incomplete')
    return result


def cases_and_plan(args,g):
    owner,freeze=PLAN.references()
    data=owner.build_cases()
    if tuple(data)!=IDS or sha(owner.encoded(data))!=freeze['case_sha256']:raise ValueError('original independent cases drift')
    raw=args.plan.read_bytes()
    if sha(raw)!=PLAN_SHA:raise ValueError('exact frozen prospective T plan required')
    value=read_json(args.plan)
    if value['reference_freeze_sha256']!=PLAN.REFERENCE_FREEZE_SHA or value['all_cases']!=freeze['case_count']:raise ValueError('plan/reference binding')
    rebuilt={str(pid):PLAN.batch_plan(pid,rows,CHECK.reference) for pid,rows in data.items()}
    if not exact(rebuilt,value['plans']):raise ValueError('case admission/batching differs from frozen plan')
    return data,rebuilt


def binding(pid,lang,row,contract):
    spec=next(p for p in contract['problems'] if p['id']==pid);suffix='py' if lang=='python' else 'cjs';template='python3' if lang=='python' else 'javascript'
    return {'source_sha256':row['sha256'],'semantics_sha256':row['semantics_sha256'],'source_path':str((SOURCE/row['path']).relative_to(ROOT)),
            'source_manifest_sha256':MANIFEST_SHA,'observer_profile_sha256':PROFILE_SHA,'observer_sha256':PROFILE_FILES[f'harness.{suffix}'],
            'native_graph_helper_sha256':PROFILE_FILES[f'native_graphs.{suffix}'],'host_checker_sha256':PROFILE_FILES['host_check.py'],
            'definition_content_sha256':spec['definition']['content_sha256'],
            'official_language_template_sha256':spec['definition']['actual_template_sha256'][template],
            'official_template_response_sha256':spec['definition']['response_sha256']}


def accept_reviews(value,rows,contract):
    supplied={}
    if value is not None:
        if value.get('schema')!='gamma.independent-source-observer-static-review.v1' or type(value.get('candidate_executions')) is not int or value['candidate_executions']!=0 or value.get('observer_profile_sha256')!=PROFILE_SHA or value.get('source_manifest_sha256')!=MANIFEST_SHA or value.get('blocked_ids')!=list(BLOCKED) or value.get('blocked_ids_opened') is not False or type(value.get('selected_programs')) is not int or value['selected_programs']!=len(rows):raise ValueError('source review root binding/count')
        for review in value['programs']:
            pid,lang=review.get('problem_id'),review.get('language');key=pid,lang
            if type(pid) is not int or key not in rows or key in supplied:raise ValueError('unknown/Boolean/duplicate review identity')
            supplied[key]=review
    result={}
    for (pid,lang),row in rows.items():
        record=supplied.get((pid,lang),{});pins=binding(pid,lang,row,contract)
        approved=all(record.get(k)==v for k,v in pins.items()) and isinstance(record.get('reviewer'),str) and bool(record['reviewer'].strip()) and all(record.get(flag) is True for flag in FLAGS)
        result[f'{pid}:{lang}']={'approved':approved,'record':record,'reason':None if approved else 'missing, false, or differently bound independent source review'}
    return result


def reviews(args,rows,contract):
    if args.review is None:return accept_reviews(None,rows,contract)
    if SOURCE_REVIEW_SHA is None:raise ValueError('observer-v2 rebinding review receipt not yet pinned')
    if sha(args.review.read_bytes())!=SOURCE_REVIEW_SHA:raise ValueError('exact independent T16 source review required')
    return accept_reviews(read_json(args.review),rows,contract)


def observer_review(args):
    # Same exact independent receipt explicitly reviews all selected observer helpers.
    if args.review is None:raise ValueError('independent observer/source review required')
    if SOURCE_REVIEW_SHA is None:raise ValueError('observer-v2 rebinding review receipt not yet pinned')
    raw=args.review.read_bytes()
    if sha(raw)!=SOURCE_REVIEW_SHA:raise ValueError('exact independent observer/source receipt required')
    value=json.loads(raw)
    if value.get('observer_profile_sha256')!=PROFILE_SHA or value.get('source_manifest_sha256')!=MANIFEST_SHA:raise ValueError('observer receipt/profile binding')
    return {'sha256':sha(raw),'record':value}


def artifacts(g,rows):
    if any(sha(path.read_bytes())!=pin for path,pin in LOADED.items()):raise ValueError('loaded controller/judge/helper drift; restart with reviewed code')
    result={str(path.relative_to(ROOT)):sha(path.read_bytes()) for path in LOADED}
    # Static owner closure only: a freeze/report written beside this code must
    # not become a new input and invalidate its own execution identity.
    for name in ('protocol.py','test_protocol.py','README.md','validation.json'):
        path=HERE/name
        if path.exists():result[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    if sha((OBSERVER/'native-bindings.json').read_bytes())!=PROFILE_SHA:raise ValueError('reviewed profile drift')
    result[str((OBSERVER/'native-bindings.json').relative_to(ROOT))]=PROFILE_SHA
    for name,pin in PROFILE_FILES.items():
        status=profile_file_status(name,pin)
        if status['status']=='hash_verified':result[str((OBSERVER/name).relative_to(ROOT))]=pin
    _,freeze=PLAN.references()
    result[str((SOURCE/'pre-source-reference-freeze.json').relative_to(ROOT))]=PLAN.REFERENCE_FREEZE_SHA
    for name,pin in freeze['files'].items():result[str((SOURCE/name).relative_to(ROOT))]=pin
    for name in ('manifest.json','assignment.public-safe.json','contracts.json','pre-source-reference-freeze.json'):
        path=SOURCE/name;result[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    for (pid,lang),row in rows.items():
        for field,pinfield in (('path','sha256'),('semantics_path','semantics_sha256')):
            E.access(g,pid,lang,'source');path=SOURCE/row[field]
            raw=E.bounded_regular_read(path,maximum_bytes=1024**2)
            if sha(raw)!=row[pinfield]:raise ValueError('source/semantics changed')
            result[str(path.relative_to(ROOT))]=sha(raw)
    return result


PUBLIC_QUERY='query questionData($titleSlug: String!) { question(titleSlug:$titleSlug) { questionId questionFrontendId title titleSlug isPaidOnly content exampleTestcaseList metaData codeSnippets { langSlug code } } }'

def prepare(args):
    _,contract=metadata();g=gate(args);args.statements.mkdir(parents=True,exist_ok=False)
    fetched={}
    for spec in contract['problems']:
        pid=spec['id']
        if type(pid) is not int or pid not in IDS:raise ValueError('unassigned public refetch')
        for lang in LANGUAGES:
            E.access(g,pid,lang,'source');E.access(g,pid,lang,'statement')
        request=urllib.request.Request('https://leetcode.com/graphql/',data=encoded({'query':PUBLIC_QUERY,'variables':{'titleSlug':spec['slug']}}),headers={'Content-Type':'application/json','User-Agent':'Gamma public-domain qualification'})
        with urllib.request.urlopen(request,timeout=25) as response:raw=response.read(4*1024**2+1)
        with (args.statements/f'{pid}.json').open('xb') as stream:stream.write(raw);stream.flush();E.os.fsync(stream.fileno())
        if len(raw)>4*1024**2:raise ValueError('public response bound exceeded; response retained')
        q=json.loads(raw)['data']['question'];pin=spec['definition'];snippets={s['langSlug']:s['code'] for s in q['codeSnippets'] if s['langSlug'] in ('python3','javascript')}
        if q.get('questionFrontendId')!=str(pid) or q.get('titleSlug')!=spec['slug'] or q.get('isPaidOnly') is not False or sha(q['content'].encode())!=pin['content_sha256'] or not exact(json.loads(q['metaData']),spec['raw_fixture_metadata']) or {k:sha(v.encode()) for k,v in snippets.items()}!=pin['actual_template_sha256']:raise ValueError('refetched content/API/actual templates differ')
        fetched[str(pid)]={'refetched_response_sha256':sha(raw),'original_response_sha256':pin['response_sha256'],'content_sha256':pin['content_sha256'],'api_sha256':sha(encoded(spec['raw_fixture_metadata'])),'templates':pin['actual_template_sha256']}
    write(args.statements/'refetch-receipt.json',{'selected_ids':list(IDS),'blocked_ids':list(BLOCKED),'pins':fetched,'candidate_executions':0})
    return {'public_definitions':len(fetched),'candidate_executions':0}


def freeze(args):
    runtime=E.runtime();raw=args.preflight.read_bytes()
    if PLAN.MAX_OUTPUT_BYTES!=E.LIMITS.max_output_bytes:raise ValueError('prospective output ceiling differs from unchanged actual cap')
    if sha(raw)!=args.preflight_sha256 or re.search(rb'\b37 passed\b',raw) is None:raise ValueError('exact passing existing37-check Linux judge preflight required')
    rows,contract=metadata();g=gate(args);statement_pins=definitions(args,g,contract);data,plans=cases_and_plan(args,g)
    review=reviews(args,rows,contract);observer=observer_review(args);pins=artifacts(g,rows)
    value={'schema':SCHEMA,'ids':list(IDS),'blocked_ids':list(BLOCKED),'program_count':len(rows),'profile_sha256':PROFILE_SHA,'source_manifest_sha256':MANIFEST_SHA,
           'artifact_hashes':pins,'runtime':runtime,'argv':ARGV,'limits':asdict(E.LIMITS),'host_packet_bytes':PLAN.MAX_HOST_PACKET_BYTES,'plan_sha256':PLAN_SHA,
           'statement_pins':statement_pins,'case_sha256':sha(encoded(data)),'case_counts':{str(p):len(v) for p,v in data.items()},'plans':plans,'source_reviews':review,
           'source_review_sha256':SOURCE_REVIEW_SHA if args.review is not None else None,'observer_review':observer,'preflight_sha256':args.preflight_sha256,
           'historical_helper_stress_evidence':historical_stress_evidence(),'historical_helper_stress_used_for_qualification':False,
           'rerun':rerun_record(),'execution_gate_sha256':args.gate_sha256,'boundary_trusted_hashes':g['trusted_hashes'],'scope':SCOPE,'canonical_admission_changed':False}
    write(args.freeze,value)
    return {'freeze_sha256':sha(args.freeze.read_bytes()),'programs':len(rows),'source_reviews_approved':sum(r['approved'] for r in review.values()),'candidate_executions':0}


def verified(args,live):
    raw=args.freeze.read_bytes()
    if sha(raw)!=args.freeze_sha256:raise ValueError('exact execution freeze identity required')
    value=read_json(args.freeze)
    if value.get('schema')!=SCHEMA or not exact(value.get('ids'),list(IDS)) or not exact(value.get('blocked_ids'),list(BLOCKED)) or value.get('profile_sha256')!=PROFILE_SHA or value.get('source_manifest_sha256')!=MANIFEST_SHA or not exact(value.get('limits'),asdict(E.LIMITS)) or not exact(value.get('argv'),ARGV) or value.get('host_packet_bytes')!=PLAN.MAX_HOST_PACKET_BYTES or value.get('plan_sha256')!=PLAN_SHA:raise ValueError('fixed T execution policy differs')
    if not exact(value.get('historical_helper_stress_evidence'),historical_stress_evidence()) or value.get('historical_helper_stress_used_for_qualification') is not False:raise ValueError('historical stress evidence availability drift')
    if not exact(value.get('rerun'),rerun_record()):raise ValueError('rerun selection/lineage drift')
    rows,contract=metadata();g=gate(args)
    if type(value.get('program_count')) is not int or value['program_count']!=len(rows):raise ValueError('dynamic selected program count differs')
    if not exact(g['trusted_hashes'],value['boundary_trusted_hashes']):raise ValueError('six-anchor boundary drift')
    if live and (args.gate_sha256!=value['execution_gate_sha256'] or not exact(E.runtime(),value['runtime'])):raise ValueError('exact execution gate/runtime drift')
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


def summary(pid,lang,cases,plan,total,failures,review):
    planned=sum(len(b['indices']) for b in plan['batches']);complete=total==planned and total>0 and not failures and not plan['blocked_cases'] and plan['admitted_distinct_cases']==len(cases)
    return {'problem_id':pid,'language':lang,'distinct_cases':len(cases),'planned_calls':planned,'executed_calls':total,'failures':failures,'transport_blocked_cases':plan['blocked_cases'],
            'source_review_approved':review['approved'],'blocked_review':not review['approved'],'complete_prepared_suite_passed':complete,
            'qualified_finite_suite':complete and review['approved'],'canonical_admission_changed':False,'scope':SCOPE}


def run_or_replay(args,replay=False):
    value,rows,g,data=verified(args,not replay)
    historical={key:value[key] for key in ('historical_helper_stress_evidence','historical_helper_stress_used_for_qualification')}
    identity={'freeze_sha256':args.freeze_sha256,'profile_sha256':PROFILE_SHA,'rerun':value['rerun'],'runtime':value['runtime'],'artifact_hashes':value['artifact_hashes'],**historical}
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
                        if sha(raw)!=PROFILE_FILES[name]:raise ValueError('native observer changed before dispatch')
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
        row=summary(pid,lang,data[pid],plan,total,failures,review);summaries.append(row);path=args.output/f'{pid}-{lang}.summary.json'
        if replay:
            if not exact(read_json(path),row):raise ValueError('summary differs from raw replay')
        else:write(path,row)
    report={'schema':SCHEMA,**historical,'rerun':value['rerun'],'freeze_sha256':args.freeze_sha256,'program_count':len(summaries),'programs':summaries,'canonical_admission_changed':False,'scope':SCOPE}
    if replay:
        if not exact(read_json(args.output/'report.json'),report):raise ValueError('aggregate differs from raw replay')
        replay_record={'schema':SCHEMA,**historical,'freeze_sha256':args.freeze_sha256,'programs_replayed':len(summaries),'batches_replayed':batches,'raw_stream_hashes':raw_hashes,'all_observations_match_report':True,'candidate_execution_on_replay_host':False,'original_execution_gate_sha256':value['execution_gate_sha256'],'replay_gate_sha256':args.gate_sha256}
        path=args.output/'replay.json'
        if path.exists():
            if not exact(read_json(path),replay_record):raise ValueError('saved replay receipt differs from raw replay')
        else:write(path,replay_record)
    else:write(args.output/'report.json',report)
    return {'programs':len(summaries),'sandbox_batches':batches,'executed_calls':sum(r['executed_calls'] for r in summaries),'qualified_finite_suite_programs':sum(r['qualified_finite_suite'] for r in summaries),'blocked_review_programs':sum(r['blocked_review'] for r in summaries),'replayed':replay,**historical}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('prepare','freeze','run','replay'))
    for name in ('gate','statements','freeze','preflight','review','observer-review','plan','output'):parser.add_argument('--'+name,type=Path)
    for name in ('gate-sha256','freeze-sha256','preflight-sha256'):parser.add_argument('--'+name)
    args=parser.parse_args();result=prepare(args) if args.operation=='prepare' else freeze(args) if args.operation=='freeze' else run_or_replay(args,args.operation=='replay')
    print(encoded(result).decode())

if __name__=='__main__':main()
