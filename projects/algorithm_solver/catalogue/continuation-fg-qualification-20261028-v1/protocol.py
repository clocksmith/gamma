"""Fixed continuation cohorts: public refetch, source freeze, bounded Linux judge.

Expected results stay on the host. This owner never provisions a runtime or
changes access policy. Original sources and all failed/blocked observations stay
identified independently of whether manual review gates have been completed.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT/'projects/algorithm_solver'))
from algsolve.judge import sandbox
from catalogue.boundary_policy import authorize_before_open
from catalogue.public_batch_adapter import bounded_regular_read

SCHEMA = 'gamma.continuation-fg-qualification.v1'
IDS = {'f': (3741,3742,3746,3747,3748,3751,3753,3755,3756,3759),
       'g': (3760,3761,3765,3766,3767,3770,3775,3776,3777,3780)}
DIRECTORIES = {key: Path('projects/algorithm_solver/catalogue/authored')/f'continuation-{key}-20261028-v1' for key in IDS}
LANGUAGES = ('python','javascript')
TRANSPORT = Path('projects/algorithm_solver/catalogue/public-domain-qualification-easy16-v1')
FUNCTION_TRANSPORT = Path('projects/algorithm_solver/catalogue/imported-commonjs-observer-v1/function-harness.cjs')
LIMITS = sandbox.Limits(cpu_seconds=3, wall_seconds=8, memory_bytes=1024**3,
                       max_output_bytes=16*1024**2)
ARGV = {'python':['/usr/bin/python3','-I','-S','harness.py'],
        'javascript':['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=256','harness.cjs']}
# Explicit prospective host-input envelope, not an interpretation of RLIMIT_FSIZE.
MAX_INPUT_BYTES = 16*1024**2
BATCH_POLICY = 'small-repeat;owner-isolate-singleton;large-repeat-if-fits-else-small-large-small;retain-blocked-v1'
REVIEW_FLAGS = ('independent_source_review','source_safety','exact_domain_interface',
                'numeric_contract','mandatory_complexity','effects_contract',
                'independent_references_and_boundaries')
QUERY = 'query questionData($titleSlug:String!){question(titleSlug:$titleSlug){questionFrontendId title titleSlug isPaidOnly content metaData}}'


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    def pairs(values):
        result={}
        for key,value in values:
            if key in result:raise ValueError('duplicate JSON key')
            result[key]=value
        return result
    return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs,
                      parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))


def write(path,value):
    raw=encoded(value)+b'\n'
    with Path(path).open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())


def gate_file(path,pin):
    raw=Path(path).read_bytes()
    if sha(raw)!=pin:raise ValueError('existing boundary-gate descriptor changed')
    gate=json.loads(raw)
    if not isinstance(gate,dict) or set(('artifact_paths','trusted_hashes'))-set(gate):
        raise ValueError('existing six-anchor gate required')
    return gate


def access(gate,pid,language,kind='source'):
    decision=authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],
                                   language=language,payload_kind=kind)
    if (decision.get('authorized') is not True or decision.get('problem_id')!=f'leetcode:{pid}'
            or decision.get('language')!=language or decision.get('payload_kind')!=kind):
        raise PermissionError('live boundary decision does not bind this exact open')
    return decision


def population():
    value=read_json(HERE/'population.json')
    if value.get('schema')!='gamma.fixed-continuation-fg-population.v1' or set(value.get('cohorts',{}))!=set(IDS):
        raise ValueError('fixed population required')
    for key,expected in IDS.items():
        cohort=value['cohorts'][key]
        if cohort['directory']!=str(DIRECTORIES[key]) or tuple(row['id'] for row in cohort['problems'])!=expected:
            raise ValueError('population locator or exact identity changed')
        for row in cohort['problems']:
            if type(row['id']) is not int or not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',row['slug']):
                raise ValueError('invalid fixed official identity')
            if row['return_policy']!='exact':
                raise ValueError('unsupported result policy')
        directory=ROOT/DIRECTORIES[key]
        for name,field in (('assignment.public-safe.json','assignment_sha256'),('manifest.json','manifest_sha256')):
            if sha((directory/name).read_bytes())!=cohort[field]:raise ValueError('reviewed assignment or manifest drift')
        assignment=read_json(directory/'assignment.public-safe.json')
        if not isinstance(assignment.get('authorization'),str) or not assignment['authorization'].strip():
            raise ValueError('assigned owner authorization reference missing')
        if tuple(p['id'] for p in assignment['problems'])!=expected:raise ValueError('assignment population drift')
        for spec,problem in zip(cohort['problems'],assignment['problems']):
            interface=problem['external_interface']
            api=interface.get('metadata',interface.get('official_metadata',interface.get('official')))
            if (problem['slug']!=spec['slug'] or problem['title']!=spec['title']
                    or sha(encoded(api))!=spec['api_sha256'] or interface['canonical']!='solve'):
                raise ValueError('assignment API/definition mismatch')
    return value


def validate_definition(raw,spec):
    question=json.loads(raw)['data']['question']
    if (not isinstance(question,dict) or question.get('isPaidOnly') is not False
            or str(question.get('questionFrontendId'))!=str(spec['id'])
            or question.get('titleSlug')!=spec['slug'] or question.get('title')!=spec['title']
            or not isinstance(question.get('content'),str) or not question['content']
            or sha(question['content'].encode())!=spec['content_sha256']
            or sha(encoded(json.loads(question['metaData'])))!=spec['api_sha256']):
        raise ValueError('public definition/identity/API/content gate failed')
    return question


def prepare(args):
    pop=population();gate=gate_file(args.gate,args.gate_sha256)
    args.statements.mkdir(parents=True,exist_ok=False)
    records=[]
    for cohort in pop['cohorts'].values():
        for spec in cohort['problems']:
            for language in LANGUAGES:
                access(gate,spec['id'],language,'source');access(gate,spec['id'],language,'statement')
            # Both kinds/languages above are checked immediately before this
            # fixed endpoint fetch; no arbitrary URL or dynamic locator input.
            request=urllib.request.Request('https://leetcode.com/graphql/',
                data=encoded({'query':QUERY,'variables':{'titleSlug':spec['slug']}}),
                headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0',
                         'Referer':'https://leetcode.com/problems/'+spec['slug']+'/'})
            with urllib.request.urlopen(request,timeout=30) as response:
                raw=response.read(4*1024**2+1)
            if len(raw)>4*1024**2:raise ValueError('official response bound exceeded')
            validate_definition(raw,spec)
            with (args.statements/f"{spec['id']}.json").open('xb') as stream:stream.write(raw)
            records.append({'id':spec['id'],'raw_sha256':sha(raw),'content_sha256':spec['content_sha256']})
    write(args.statements/'pins.json',{'schema':'gamma.continuation-fg-public-refetch.v1','records':records,
                                     'historical_protected_payloads_used':False})
    return {'definitions':len(records),'candidate_executions':0,'frozen':False}


def definitions(statements,pop,gate):
    result={}
    for cohort in pop['cohorts'].values():
        for spec in cohort['problems']:
            for language in LANGUAGES:access(gate,spec['id'],language,'statement')
            path=Path(statements)/f"{spec['id']}.json"
            raw=bounded_regular_read(path,maximum_bytes=4*1024**2);validate_definition(raw,spec)
            result[str(spec['id'])]={'raw_sha256':sha(raw),'content_sha256':spec['content_sha256'],
                                    'api_sha256':spec['api_sha256']}
    return result


def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def cases_and_owners(pop):
    cases,owners={},{}
    for key in IDS:
        directory=ROOT/DIRECTORIES[key]
        oracle=load_module(directory/'oracles.py','continuation_'+key+'_oracle')
        if key=='f':
            # Existing F owner uses its sibling's absolute import. Bind only
            # while importing that host generator; restore unrelated modules.
            previous=sys.modules.get('oracles')
            sys.modules['oracles']=oracle
            try:generator=load_module(directory/'cases.py','continuation_f_cases')
            finally:
                if previous is None:sys.modules.pop('oracles',None)
                else:sys.modules['oracles']=previous
        else:generator=oracle
        if tuple(oracle.IDS)!=IDS[key]:raise ValueError('oracle population drift')
        for pid in IDS[key]:
            rows=generator.build_cases(pid,include_maximum=True) if key=='f' else generator.build_cases(pid)
            if not rows or type(rows) is not list:raise ValueError('nonempty independently generated cases required')
            for row in rows:
                if type(row) is not dict or not {'args','expected'}<=set(row):raise ValueError('case shape')
                (oracle.validate_domain if key=='f' else oracle.validate)(pid,row['args'])
                if pid==3669 and row.get('comparison_policy')!='optimal-factor-witness':
                    raise ValueError('explicit factor-witness result policy required')
            cases[pid]=rows;owners[pid]=oracle
    return cases,owners


def artifacts(pop,gate):
    result={}
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.suffix in ('.py','.json','.md'):
            result[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    for key in IDS:
        directory=ROOT/DIRECTORIES[key];cohort=pop['cohorts'][key]
        manifest=read_json(directory/'manifest.json');inventory=manifest['source_inventory']
        wanted={(pid,language) for pid in IDS[key] for language in LANGUAGES}
        observed=set()
        for row in inventory:
            identity=(row['id'],row['language'])
            if identity not in wanted or identity in observed:raise ValueError('source inventory duplicate/unassigned identity')
            observed.add(identity);pid,language=identity
            suffix='py' if language=='python' else 'js';name=f'{language}/{pid}.{suffix}'
            if row['path']!=name:raise ValueError('source locator must match exact assigned ID/language')
            access(gate,pid,language,'source');path=directory/name
            raw=bounded_regular_read(path,maximum_bytes=1024**2)
            if sha(raw)!=row['sha256']:raise ValueError('exact source drift')
            result[str(path.relative_to(ROOT))]=sha(raw)
        if observed!=wanted:raise ValueError('missing assigned source slot')
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix in ('.py','.json','.md'):
                result[str(path.relative_to(ROOT))]=sha(path.read_bytes())
        for row in inventory:
            path=directory/row['semantics_path']
            if path.parent!=directory/'semantics' or path.suffix!='.json':raise ValueError('contract locator escaped')
            raw=path.read_bytes()
            if sha(raw)!=row['semantics_sha256']:raise ValueError('exact source contract drift')
            result[str(path.relative_to(ROOT))]=sha(raw)
    for relative in (TRANSPORT/'harness.py',TRANSPORT/'harness.cjs',FUNCTION_TRANSPORT,
                     Path('projects/algorithm_solver/algsolve/judge/sandbox.py'),
                     Path('projects/algorithm_solver/catalogue/boundary_policy.py'),
                     Path('projects/algorithm_solver/catalogue/public_batch_adapter.py')):
        result[str(relative)]=sha((ROOT/relative).read_bytes())
    return result


def runtime():
    if sys.platform!='linux':raise sandbox.SandboxUnavailable('Linux runtime/preflight required; no host fallback')
    sandbox.check_available();refs={};started=time.monotonic()
    for name in ('python3','node','bwrap','prlimit'):
        path=Path('/usr/bin')/name;refs[str(path)]=sha(path.read_bytes())
        proc=subprocess.run(['/usr/bin/ldd',str(path)],capture_output=True,text=True,check=True,timeout=20)
        for dep in re.findall(r'(?:=>\s*)?(/[^\s()]+)',proc.stdout):refs[dep]=sha(Path(dep).read_bytes())
    stdlib=Path(subprocess.check_output(['/usr/bin/python3','-I','-S','-c',
        'import sysconfig;print(sysconfig.get_path("stdlib"))'],text=True,timeout=20).strip())
    files={};seen=0
    for directory,children,names in os.walk(stdlib):
        children[:]=sorted(name for name in children if name not in ('site-packages','__pycache__'))
        for name in sorted(names):
            seen+=1
            if seen>50000 or time.monotonic()-started>60:raise ValueError('bounded runtime inventory incomplete')
            path=Path(directory)/name
            if path.is_file() and path.suffix in ('.py','.so'):
                files[str(path.relative_to(stdlib))]=sha(path.read_bytes())
    return {'executables_and_linked_libraries':refs,'python_stdlib_path':str(stdlib),'python_stdlib_files':files,
            'python_version':subprocess.check_output(['/usr/bin/python3','--version'],text=True,timeout=20).strip(),
            'node_version':subprocess.check_output(['/usr/bin/node','--version'],text=True,timeout=20).strip()}


def packet(rows,indices):
    return {'entry':'solve','calls':[{'args':rows[i]['args']} for i in indices]}


def projected_output(pid,language,rows,indices):
    total=0
    for position,index in enumerate(indices):
        case=rows[index]
        value=case['expected']
        kind=return_type(pid,case,language)
        record={'i':position,'result':value,'result_type':kind,'args_before':case['args'],
                'args_after':case['args'],'alias_edges':[]}
        # Python's done record has one extra separating space; ASCII input
        # domains make this exact for ordinary records and a safe upper bound
        # for3669's independently checked factor-list result.
        total+=len(encoded(record))+1
    return total+len(encoded({'done':len(indices)}))+1+(language=='python')


def batch_plan(pid,rows):
    def measured(indices,policy):
        return {'indices':indices,'policy':policy,'input_bytes':len(encoded(packet(rows,indices))),
                'projected_output_bytes':{lang:projected_output(pid,lang,rows,indices) for lang in LANGUAGES}}
    def fits(entry):
        return entry['input_bytes']<=MAX_INPUT_BYTES and max(entry['projected_output_bytes'].values())<=LIMITS.max_output_bytes
    sizes=[len(encoded(row['args'])) for row in rows]
    probe=min(range(len(rows)),key=sizes.__getitem__)
    plan=[];blocked=[];small=[];small_bytes=0
    def flush():
        nonlocal small,small_bytes
        if small:
            entry=measured(small+[small[0]],'small-first-call-repeat')
            if not fits(entry):raise ValueError('small batch envelope calculation failed')
            plan.append(entry);small=[];small_bytes=0
    for index,size in enumerate(sizes):
        if rows[index].get('isolate') is True:
            flush()
            entry=measured([index],'owner-declared-isolated-analytic-case')
            if fits(entry):plan.append(entry)
            else:blocked.append({'case':index,'status':'blocked_transport','input_bytes':entry['input_bytes'],
                'projected_output_bytes':entry['projected_output_bytes'],'reason':'isolated analytic case exceeds unchanged envelope'})
        elif size>256*1024:
            flush()
            options=[measured([index,index],'large-repeat'),
                     measured([probe,index,probe],'small-large-small'),
                     measured([index],'large-singleton-partial-state-coverage')]
            accepted=next((entry for entry in options if fits(entry)),None)
            if accepted is not None:plan.append(accepted)
            else:
                one=options[-1];blocked.append({'case':index,'status':'blocked_transport','input_bytes':one['input_bytes'],
                    'projected_output_bytes':one['projected_output_bytes'],'reason':'single case exceeds unchanged output or prospective host input envelope'})
        else:
            if small and (len(small)>=32 or small_bytes+size>256*1024):flush()
            small.append(index);small_bytes+=size
    flush()
    covered={i for entry in plan for i in entry['indices']}
    if covered | {r['case'] for r in blocked} != set(range(len(rows))):raise ValueError('logical case silently omitted')
    return {'batch_policy':BATCH_POLICY,'batches':plan,'blocked_cases':blocked,
            'logical_case_count':len(rows),'admitted_distinct_cases':len(covered)}


def return_type(pid,case,language):
    value=case['expected']
    if language=='python':return type(value).__name__
    if type(value) is bool:return 'boolean'
    if type(value) in (int,float):return 'number'
    if type(value) is str:return 'string'
    return 'object'


def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if type(a) is dict:return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
    return a==b


def parse(raw,count):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate observation key')
            result[key]=value
        return result
    rows=[json.loads(line,object_pairs_hook=pairs,
          parse_constant=lambda token:(_ for _ in ()).throw(ValueError(token))) for line in raw.decode('utf8').splitlines()]
    if len(rows)!=count+1 or type(rows[-1]) is not dict or set(rows[-1])!={'done'} or type(rows[-1]['done']) is not int or rows[-1]['done']!=count:
        raise ValueError('incomplete observation stream')
    for index,row in enumerate(rows[:-1]):
        if type(row) is not dict or type(row.get('i')) is not int or row['i']!=index:raise ValueError('observation order')
        required={'i','error'} if 'error' in row else {'i','result','result_type','args_before','args_after','alias_edges'}
        if set(row)!=required:raise ValueError('observation shape')
    return rows[:-1]


def compare(pid,language,case,record,owner):
    if 'error' in record:return 'candidate_error'
    if record.get('result_type')!=return_type(pid,case,language):return 'result_type'
    if not exact(record.get('args_before'),case['args']) or not exact(record.get('args_after'),case['args']):return 'input_effects'
    if not exact(record.get('alias_edges'),[]):return 'return_aliases'
    good=exact(record.get('result'),case['expected'])
    if pid in IDS.get('g',()):good=good and owner.matches(pid,case['args'],record.get('result'))
    return None if good else 'result_value'


def verdict(pid,language,rows,indices,metadata,stdout,owner):
    if (type(metadata.get('exit_code')) is not int or metadata['exit_code']!=0 or metadata.get('timed_out') is not False
            or metadata.get('output_limit_exceeded') is not False):
        return [{'case':index,'reason':'sandbox_process_failure'} for index in indices]
    try:observed=parse(stdout,len(indices))
    except (ValueError,TypeError,UnicodeError):return [{'case':index,'reason':'observation_protocol'} for index in indices]
    failures=[]
    for index,record in zip(indices,observed):
        reason=compare(pid,language,rows[index],record,owner)
        if reason:failures.append({'case':index,'reason':reason})
    return failures


def manual_reviews(path,pop):
    value={} if path is None else read_json(path)
    rows=value.get('programs',[]) if isinstance(value,dict) else []
    wanted={(pid,lang) for key in IDS for pid in IDS[key] for lang in LANGUAGES}
    observed={}
    for row in rows:
        key=(row.get('problem_id'),row.get('language'))
        if type(row.get('problem_id')) is not int or key not in wanted or key in observed:
            raise ValueError('unknown/duplicate manual source review')
        observed[key]=row
    result={}
    for key in IDS:
        directory=ROOT/DIRECTORIES[key];manifest=read_json(directory/'manifest.json')
        for source in manifest['source_inventory']:
            pid,lang=source['id'],source['language'];review=observed.get((pid,lang),{})
            binding=review_binding(pop,key,pid,lang,source)
            approved=(review.get('source_sha256')==source['sha256'] and
                review.get('semantics_sha256')==source['semantics_sha256'] and
                all(review.get(name)==pin for name,pin in binding.items()) and
                isinstance(review.get('reviewer'),str) and bool(review['reviewer'].strip()) and
                all(review.get(flag) is True for flag in REVIEW_FLAGS))
            result[f'{pid}:{lang}']={'approved':approved,'record':review,
                'reason':None if approved else 'missing, false or differently bound mandatory independent source-review gates'}
    return result


def review_binding(pop,key,pid,language,source):
    directory=ROOT/DIRECTORIES[key]
    spec=next(row for row in pop['cohorts'][key]['problems'] if row['id']==pid)
    observer=(ROOT/TRANSPORT/'harness.py') if language=='python' else ROOT/FUNCTION_TRANSPORT
    return {'source_sha256':source['sha256'],'semantics_sha256':source['semantics_sha256'],
            'reference_sha256':sha((directory/'oracles.py').read_bytes()),
            'case_generator_sha256':sha((directory/('cases.py' if key=='f' else 'oracles.py')).read_bytes()),
            'definition_content_sha256':spec['content_sha256'],'interface_api_sha256':spec['api_sha256'],
            'observer_sha256':sha(observer.read_bytes()),
            'shared_effect_observer_sha256':sha((ROOT/TRANSPORT/'harness.cjs').read_bytes()) if language=='javascript' else sha(observer.read_bytes())}


def review_template(args):
    pop=population();gate=gate_file(args.gate,args.gate_sha256)
    artifacts(pop,gate)  # exact assigned sources with live per-open gates
    rows=[]
    for key in IDS:
        manifest=read_json(ROOT/DIRECTORIES[key]/'manifest.json')
        for source in manifest['source_inventory']:
            pid,language=source['id'],source['language']
            rows.append({'problem_id':pid,'language':language,'reviewer':'',
                **review_binding(pop,key,pid,language,source),**{flag:False for flag in REVIEW_FLAGS}})
    write(args.review,{'schema':'gamma.continuation-fg-mandatory-source-review.v1','programs':rows,
        'note':'Template only. False flags confer no qualification and do not grant source access.'})
    return {'programs':len(rows),'approved':0,'candidate_executions':0}


def freeze(args):
    pop=population();gate=gate_file(args.gate,args.gate_sha256)
    observed_runtime=runtime()  # Mars cannot create an execution freeze.
    preflight=args.preflight.read_bytes()
    if sha(preflight)!=args.preflight_sha256 or re.search(rb'\b37 passed\b',preflight) is None:
        raise ValueError('exact passing existing37-check Linux preflight required')
    definition_pins=definitions(args.statements,pop,gate)
    pins=artifacts(pop,gate);data,_=cases_and_owners(pop)
    contract={'schema':SCHEMA,'created_at':datetime.now(timezone.utc).isoformat(),
        'population_sha256':sha((HERE/'population.json').read_bytes()),'artifact_hashes':pins,
        'runtime':observed_runtime,'argv':ARGV,'limits':asdict(LIMITS),'max_input_bytes':MAX_INPUT_BYTES,
        'batch_policy':BATCH_POLICY,'statement_pins':definition_pins,
        'boundary_trusted_hashes':gate['trusted_hashes'],'execution_gate_sha256':args.gate_sha256,
        'case_sha256':sha(encoded(data)),'case_counts':{str(pid):len(rows) for pid,rows in data.items()},
        'batch_plans':{str(pid):batch_plan(pid,rows) for pid,rows in data.items()},
        'manual_reviews':manual_reviews(args.review,pop),'preflight_sha256':args.preflight_sha256,
        'scope':'Exposed development finite-case solve adapters. No native wrapper, held-out, canonical-adoption or universal/full-domain resource claim.',
        'canonical_admission_changed':False,'historical_protected_payloads_used':False}
    write(args.freeze,contract)
    return {'freeze_sha256':sha(args.freeze.read_bytes()),'programs':40,'candidate_executions':0,
            'blocked_transport_cases':sum(len(p['blocked_cases']) for p in contract['batch_plans'].values())}


def verified_inputs(args,check_runtime):
    raw=args.freeze.read_bytes()
    if sha(raw)!=args.freeze_sha256:raise ValueError('exact frozen execution identity required')
    contract=json.loads(raw)
    if (contract.get('schema')!=SCHEMA or contract.get('argv')!=ARGV or contract.get('limits')!=asdict(LIMITS)
            or contract.get('max_input_bytes')!=MAX_INPUT_BYTES or contract.get('batch_policy')!=BATCH_POLICY):
        raise ValueError('frozen runtime settings differ')
    pop=population();gate=gate_file(args.gate,args.gate_sha256)
    if gate['trusted_hashes']!=contract['boundary_trusted_hashes']:raise ValueError('boundary anchors drift')
    if check_runtime and (args.gate_sha256!=contract['execution_gate_sha256'] or runtime()!=contract['runtime']):
        raise ValueError('execution runtime or exact execution gate changed')
    if artifacts(pop,gate)!=contract['artifact_hashes']:raise ValueError('source/helper/contract drift')
    if definitions(args.statements,pop,gate)!=contract['statement_pins']:raise ValueError('refetched definition snapshots drift')
    data,owners=cases_and_owners(pop)
    if sha(encoded(data))!=contract['case_sha256']:raise ValueError('independently generated cases drift')
    for pid,rows in data.items():
        if batch_plan(pid,rows)!=contract['batch_plans'][str(pid)]:raise ValueError('case admission or batch policy drift')
    return raw,contract,pop,gate,data,owners


def program_summary(pid,language,rows,plan,failures,total,review):
    admitted=plan['admitted_distinct_cases']>0 and not failures
    complete=admitted and not plan['blocked_cases'] and plan['admitted_distinct_cases']==len(rows)
    return {'problem_id':pid,'language':language,'distinct_cases':len(rows),
        'admitted_distinct_cases':plan['admitted_distinct_cases'],'executed_calls':total,'failures':failures,
        'transport_blocked_cases':plan['blocked_cases'],'admitted_cases_passed':admitted,
        'complete_prepared_suite_passed':complete,'mandatory_review_approved':review['approved'],
        'qualified':complete and review['approved'],'canonical_admission_changed':False,
        'official_wrapper_execution_qualified':False,
        'scope':'Finite independently referenced solve cases only; no universal/full-domain or fresh-generalization claim'}


def execute(args):
    raw,contract,pop,gate,data,owners=verified_inputs(args,True)
    args.output.mkdir(parents=True,exist_ok=False)
    write(args.output/'run-identity.json',{'freeze_sha256':sha(raw),'artifact_hashes':contract['artifact_hashes'],
        'runtime':contract['runtime'],'host':platform.node(),'started_at':datetime.now(timezone.utc).isoformat()})
    summaries=[]
    for key in IDS:
        directory=ROOT/DIRECTORIES[key]
        for pid in IDS[key]:
            rows=data[pid];plan=contract['batch_plans'][str(pid)]
            for language in LANGUAGES:
                ext='py' if language=='python' else 'js';failures=[];total=0
                for index,entry in enumerate(plan['batches']):
                    indices=entry['indices'];wire=encoded(packet(rows,indices))
                    if len(wire)!=entry['input_bytes'] or len(wire)>MAX_INPUT_BYTES:raise ValueError('input packet plan differs')
                    access(gate,pid,language,'source');source_path=directory/language/f'{pid}.{ext}'
                    source=bounded_regular_read(source_path,maximum_bytes=1024**2)
                    if sha(source)!=contract['artifact_hashes'][str(source_path.relative_to(ROOT))]:
                        raise ValueError('source changed before dispatch')
                    files={'program.'+ext:source,'inputs.json':wire}
                    if language=='python':files['harness.py']=(ROOT/TRANSPORT/'harness.py').read_bytes()
                    else:
                        files['harness.cjs']=(ROOT/FUNCTION_TRANSPORT).read_bytes()
                        files['observer.cjs']=(ROOT/TRANSPORT/'harness.cjs').read_bytes()
                    for name,relative in ((('harness.py',TRANSPORT/'harness.py'),) if language=='python' else
                                          (('harness.cjs',FUNCTION_TRANSPORT),('observer.cjs',TRANSPORT/'harness.cjs'))):
                        if sha(files[name])!=contract['artifact_hashes'][str(relative)]:
                            raise ValueError('observer changed before dispatch')
                    stem=f'{pid}-{language}-{index:03d}'
                    write(args.output/(stem+'.start.json'),{'problem_id':pid,'language':language,'indices':indices,
                        'inputs_sha256':sha(wire),'source_sha256':sha(source),'planned':entry})
                    result=sandbox.run(ARGV[language],files=files,limits=LIMITS)
                    metadata=asdict(result)
                    # Save original streams and process status before host verdicts.
                    for name in ('stdout','stderr'):
                        stream=metadata.pop(name)
                        with (args.output/(stem+'.'+name)).open('xb') as handle:
                            handle.write(stream);handle.flush();os.fsync(handle.fileno())
                        metadata[name+'_sha256']=sha(stream);metadata[name+'_bytes']=len(stream)
                    metadata['input_bytes']=len(wire)
                    write(args.output/(stem+'.result.json'),metadata)
                    failures.extend(verdict(pid,language,rows,indices,metadata,result.stdout,owners[pid]));total+=len(indices)
                review=contract['manual_reviews'][f'{pid}:{language}']
                summary=program_summary(pid,language,rows,plan,failures,total,review);summaries.append(summary)
                write(args.output/f'{pid}-{language}.summary.json',summary)
    report={'schema':'gamma.continuation-fg-execution-report.v1','freeze_sha256':sha(raw),'programs':summaries,
            'canonical_admission_changed':False,'scope':contract['scope']}
    write(args.output/'report.json',report)
    return {'programs':len(summaries),'admitted_case_passes':sum(r['admitted_cases_passed'] for r in summaries),
            'qualified_finite_suite_programs':sum(r['qualified'] for r in summaries),'canonical_admission_changed':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('prepare','review-template','freeze','run','replay'))
    for name in ('gate','statements','freeze','preflight','review','output'):
        parser.add_argument('--'+name,type=Path)
    for name in ('gate-sha256','freeze-sha256','preflight-sha256'):
        parser.add_argument('--'+name)
    args=parser.parse_args()
    if args.operation=='prepare':result=prepare(args)
    elif args.operation=='review-template':result=review_template(args)
    elif args.operation=='freeze':result=freeze(args)
    elif args.operation=='run':result=execute(args)
    else:
        from verify import verify
        result=verify(args)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
