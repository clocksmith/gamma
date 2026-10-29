"""Boundary-repaired Q subset (126, 129, 140, 144): the Q official controller restricted to
eight programs, with every original Q case plus independently referenced boundary cases.

Limits, observers, official-template binding, repair-origin selection, superseded
original 126/140 exclusion, review flags, dispatch, transport and batch policy are
the Q controller's. No source promotion or provisioning.
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
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'projects/algorithm_solver'))
from algsolve.judge import sandbox
from catalogue.boundary_policy import authorize_before_open
from catalogue.public_batch_adapter import bounded_regular_read
Q_IDS=(126,129,132,133,138,140,141,142,143,144)  # full Q observer/reference population
IDS=(126,129,140,144)  # this lane
LANGUAGES=('python','javascript')
NATIVE={129,133,138,141,142,143,144}
SOURCES={'original':Path('projects/algorithm_solver/catalogue/authored/continuation-q-20261028-v1'),
         'repair126':Path('projects/algorithm_solver/catalogue/authored/continuation-q126-output-sensitive-20261028-v1'),
         'repair140':Path('projects/algorithm_solver/catalogue/authored/continuation-q140-output-sensitive-20261028-v1')}
OBSERVER=Path('projects/algorithm_solver/catalogue/continuation-q-observers-20261028-v1')
OBSERVER_PIN='a2f15032304b2981b231d6327360f6b0581ab98ac5f2b389650acd3feaffe916'
SCHEMA='gamma.q-boundary-execution-freeze.v1'
LIMITS=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=16*1024**2)
ARGV={'python':['/usr/bin/python3','-I','-S','harness.py'],
      'javascript':['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=256','harness.cjs']}
MAX_INPUT_BYTES=16*1024**2  # prospective host-prewritten envelope, not RLIMIT_FSIZE
PER_STREAM_OUTPUT_BYTES=LIMITS.max_output_bytes # stdout and stderr EACH, not aggregate
DISPATCH_POLICY='all-mandatory-bound-source-reviews-before-dispatch-v1'
BATCH_POLICY='owner-isolate;small-repeat;fit-repeat-or-probe-large-probe-or-single;retain-blocked-v1'
PROJECTION_POLICY='successful-stdout-shape;clone-indices-max-digit-width;per-stream-output-v2'
REVIEW_FLAGS=('independent_source_review','source_safety','actual_official_template_binding','numeric_contract',
              'mandatory_complexity','effects_contract','independent_references_and_boundaries','exposure_history_preserved')
NATIVE_FLAGS=('original_node_constructor_binding','native_identity_effects','full_shape_cycles_aliases')
REPAIR_FLAGS=('complexity_repair_proof','certificate_bridge_review','superseded_original_excluded')
QUERY='query questionData($titleSlug:String!){question(titleSlug:$titleSlug){questionFrontendId title titleSlug isPaidOnly content metaData codeSnippets{langSlug code}}}'


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def decode_json(raw):
    def pairs(values):
        result={}
        for key,value in values:
            if key in result:raise ValueError('duplicate JSON key')
            result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs,
                      parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))

def read_json(path):return decode_json(Path(path).read_bytes())


def write(path,value):
    raw=encoded(value)+b'\n'
    with Path(path).open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())

def gate_file(path,pin):
    raw=Path(path).read_bytes()
    if sha(raw)!=pin:raise ValueError('existing boundary-gate descriptor changed')
    gate=decode_json(raw)
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

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

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
    refs['/usr/bin/ldd']=sha(Path('/usr/bin/ldd').read_bytes())
    host_driver=Path(sys.executable).resolve()
    return {'host_reference_python':{'path':str(host_driver),'sha256':sha(host_driver.read_bytes()),'version':sys.version},'executables_and_linked_libraries':refs,'python_stdlib_path':str(stdlib),'python_stdlib_files':files,
            'python_version':subprocess.check_output(['/usr/bin/python3','--version'],text=True,timeout=20).strip(),
            'node_version':subprocess.check_output(['/usr/bin/node','--version'],text=True,timeout=20).strip()}

def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if type(a) is dict:return set(a)==set(b) and all(exact(a[k],b[k]) for k in a)
    return a==b


def wanted_origin(pid):
    return 'repair126' if pid==126 else 'repair140' if pid==140 else 'original'


def profile(pop):
    path=ROOT/OBSERVER/'native-bindings.json'
    if sha(path.read_bytes())!=OBSERVER_PIN or pop.get('observer_profile_sha256')!=OBSERVER_PIN:raise ValueError('unchanged Q observer profile required')
    value=read_json(path)
    if value.get('problem_ids')!=list(Q_IDS) or value.get('solve_fallback') is not False or value.get('constructor_injection') is not False or value.get('source_rewriting') is not False:raise ValueError('fixed original official observer required')
    if value.get('source_manifest_sha256')!=pop['packets']['original']['manifest_sha256']:raise ValueError('original observer source-history binding drift')
    if set(value['helper_sha256'])!={'harness.py','harness.cjs','models.py','identity_models.cjs','host_check.py'}:raise ValueError('unknown Q helper')
    for name,pin in value['helper_sha256'].items():
        if sha((ROOT/OBSERVER/name).read_bytes())!=pin:raise ValueError('Q observer helper drift')
    if (ROOT/OBSERVER/'models.py').read_bytes()!=(ROOT/SOURCES['original']/'identity_models.py').read_bytes():raise ValueError('original identity primitives changed')
    expected_refs={'oracles.py','cases.py','contracts.json','pre-source-reference-freeze.json'}
    if set(value['host_only_reference_dependencies'])!=expected_refs:raise ValueError('unknown reference dependency')
    for name,pin in value['host_only_reference_dependencies'].items():
        if sha((ROOT/SOURCES['original']/name).read_bytes())!=pin:raise ValueError('original reference/history drift')
    for spec in pop['problems']:
        if value['official_template_sha256'][str(spec['id'])]!=spec['template_sha256']:raise ValueError('actual per-language template drift')
    return value


def population():
    pop=read_json(HERE/'population.json')
    if pop.get('schema')!='gamma.fixed-q-boundary-population.v1' or tuple(row['id'] for row in pop['problems'])!=IDS or set(pop['packets'])!=set(SOURCES):raise ValueError('fixed Q population required')
    for spec in pop['problems']:
        if type(spec['id']) is not int or not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',spec['slug']) or set(spec['template_sha256'])!={'python3','javascript'}:raise ValueError('invalid exact official identity')
    inventories={}
    for key,relative in SOURCES.items():
        packet=pop['packets'][key]
        if packet['directory']!=str(relative):raise ValueError('fixed source owner locator changed')
        for name,field in (('manifest.json','manifest_sha256'),('assignment.public-safe.json','assignment_sha256')):
            if sha((ROOT/relative/name).read_bytes())!=packet[field]:raise ValueError('source-owner metadata drift')
        manifest=read_json(ROOT/relative/'manifest.json');assignment=read_json(ROOT/relative/'assignment.public-safe.json')
        if not isinstance(assignment.get('authorization'),str) or not assignment['authorization'].strip():raise ValueError('source owner authorization absent')
        for item in manifest['files']:
            relative=Path(item['path'])
            if relative.parent==Path('.') and relative.suffix in ('.py','.json','.md'):
                path=ROOT/SOURCES[key]/relative
                if path.is_symlink() or sha(path.read_bytes())!=item['sha256']:raise ValueError('public owner helper/metadata drift')
        inventories[key]=manifest['source_inventory']
    wanted={(pid,language) for pid in IDS for language in LANGUAGES};seen=set()
    for program in pop['programs']:
        pid,language=program['problem_id'],program['language'];identity=(pid,language)
        if type(pid) is not int or type(language) is not str or identity not in wanted or identity in seen or program['origin']!=wanted_origin(pid):raise ValueError('unknown, duplicate or superseded source selection')
        seen.add(identity);extension='py' if language=='python' else 'js'
        if program['source_path']!=f'{language}/{pid}.{extension}':raise ValueError('source locator must bind exact ID/language')
        semantics=Path(program['semantics_path'])
        if semantics.is_absolute() or '..' in semantics.parts or semantics.parent!=Path('semantics') or semantics.suffix!='.json':raise ValueError('unsafe contract path')
        matching=[row for row in inventories[program['origin']] if type(row['id']) is int and row['id']==pid and row['language']==language]
        if len(matching)!=1:raise ValueError('source slot missing/duplicate in owner')
        row=matching[0]
        if any(program[field]!=row[owner] for field,owner in [('source_path','path'),('source_sha256','sha256'),('semantics_path','semantics_path'),('semantics_sha256','semantics_sha256')]):raise ValueError('selected source/contract identity drift')
    if seen!=wanted:raise ValueError('missing fixed source slot')
    excluded=[row for row in inventories['original'] if row['id'] in (126,140)]
    if len(excluded)!=4 or any(row['sha256'] in {p['source_sha256'] for p in pop['programs']} for row in excluded):raise ValueError('superseded original source selected')
    if [{key:value for key,value in row.items() if key!='reason'} for row in pop['excluded_superseded_variants']]!=excluded:raise ValueError('superseded-source history drift')
    profile(pop)
    return pop


def program_count(pop):return len(pop['programs'])


def program_path(program):return ROOT/SOURCES[program['origin']]/program['source_path']


def validate_definition(raw,spec):
    question=decode_json(raw)['data']['question']
    if (type(question) is not dict or question.get('isPaidOnly') is not False or str(question.get('questionFrontendId'))!=str(spec['id'])
            or question.get('titleSlug')!=spec['slug'] or question.get('title')!=spec['title'] or type(question.get('content')) is not str
            or sha(question['content'].encode())!=spec['content_sha256'] or sha(encoded(decode_json(question['metaData'])))!=spec['raw_metadata_sha256']):raise ValueError('public content or preserved raw metadata drift')
    snippets={}
    for row in question.get('codeSnippets',[]):
        if row.get('langSlug') in ('python3','javascript'):
            if row['langSlug'] in snippets or type(row.get('code')) is not str:raise ValueError('ambiguous official template')
            snippets[row['langSlug']]=sha(row['code'].encode())
    if snippets!=spec['template_sha256']:raise ValueError('actual official templates drift; raw metadata is not ABI authority')
    return question


def prepare(args):
    pop=population();gate=gate_file(args.gate,args.gate_sha256);args.statements.mkdir(parents=True,exist_ok=False);records=[]
    for spec in pop['problems']:
        for language in LANGUAGES:
            access(gate,spec['id'],language,'source');access(gate,spec['id'],language,'statement')
        request=urllib.request.Request('https://leetcode.com/graphql/',data=encoded({'query':QUERY,'variables':{'titleSlug':spec['slug']}}),headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0','Referer':'https://leetcode.com/problems/'+spec['slug']+'/'})
        with urllib.request.urlopen(request,timeout=30) as response:raw=response.read(4*1024**2+1)
        if len(raw)>4*1024**2:raise ValueError('official response bound exceeded')
        validate_definition(raw,spec)
        with (args.statements/f"{spec['id']}.json").open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        records.append({'id':spec['id'],'raw_sha256':sha(raw),'content_sha256':spec['content_sha256'],'template_sha256':spec['template_sha256']})
    write(args.statements/'pins.json',{'schema':'gamma.q-public-executor-refetch.v1','records':records,'local_private_statements_transferred':False})
    return {'definitions':len(records),'programs':program_count(pop),'candidate_executions':0,'frozen':False}


def definitions(directory,pop,gate):
    pins={}
    for spec in pop['problems']:
        for language in LANGUAGES:access(gate,spec['id'],language,'statement')
        raw=bounded_regular_read(Path(directory)/f"{spec['id']}.json",maximum_bytes=4*1024**2);validate_definition(raw,spec)
        pins[str(spec['id'])]={'raw_sha256':sha(raw),'content_sha256':spec['content_sha256'],'raw_metadata_sha256':spec['raw_metadata_sha256'],'official_api_sha256':spec['official_api_sha256'],'template_sha256':spec['template_sha256']}
    return pins


def cases_and_owners(pop):
    reference=load_module(ROOT/SOURCES['original']/'oracles.py','q_controller_reference')
    generator=load_module(ROOT/SOURCES['original']/'cases.py','q_controller_original_cases')
    base_checker=load_module(ROOT/OBSERVER/'host_check.py','q_controller_host_checker')
    boundary=load_module(HERE/'boundary_cases.py','q_boundary_lane_cases')
    bridge=load_module(HERE/'boundary_check.py','q_boundary_lane_checker')
    if tuple(reference.IDS)!=Q_IDS or tuple(boundary.IDS)!=IDS:raise ValueError('reference population drift')
    data={};owners={}
    for pid in IDS:
        original=generator.build_cases(pid,include_maximum=True)
        if pid in (126,140):
            directory=ROOT/SOURCES[wanted_origin(pid)];repair=load_module(directory/'cases.py',f'q_controller_repair_cases_{pid}')
            rows=repair.build_cases();owner=load_module(directory/'host_check.py',f'q_controller_repair_checker_{pid}')
            if len(rows)!=len(original)+1:raise ValueError('repair membership must append exactly one frozen certificate')
            for index,(old,new) in enumerate(zip(original,rows)):
                if type(new.get('inherited_q_case_index')) is not int or new['inherited_q_case_index']!=index or not exact({k:v for k,v in new.items() if k!='inherited_q_case_index'},old):raise ValueError('old case membership/payload changed')
        else:rows=original;owner=base_checker
        if pid in (126,140):owner=bridge  # delegates to the repair checker within its budget
        inherited=len(rows);rows=list(rows)+boundary.build_boundary(pid,[row['args'] for row in rows])
        result=[]
        for index,row in enumerate(rows):
            if type(row) is not dict or not {'args','expected'}<=set(row):raise ValueError('case shape')
            reference.validate_domain(pid,row['args'])
            if not exact(owner.expected(pid,row['args']),row['expected']):raise ValueError('independent expected/certificate binding drift')
            origin='q-original' if index<len(original) else wanted_origin(pid)+'-certificate' if index<inherited else 'q-boundary'
            result.append({**row,'case_identity':{'origin':origin,'problem_id':pid,'original_index':index if origin=='q-original' else None,
                'certificate_index':0 if origin.endswith('-certificate') else None,'boundary_index':index-inherited if origin=='q-boundary' else None}})
        if not result:raise ValueError('empty prepared suite')
        data[pid]=result;owners[pid]=owner
    return data,owners


def artifacts(pop,gate):
    pins={}
    def pin(path):pins[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.suffix in ('.py','.json','.md'):pin(path)
    for key,relative in SOURCES.items():
        directory=ROOT/relative
        # Public owner metadata/host helpers only; NEVER scan source subdirs.
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix in ('.py','.json','.md'):pin(path)
    for program in pop['programs']:
        pid,language=program['problem_id'],program['language'];access(gate,pid,language,'source');path=program_path(program)
        raw=bounded_regular_read(path,maximum_bytes=1024**2)
        if sha(raw)!=program['source_sha256']:raise ValueError('exact selected source changed')
        pins[str(path.relative_to(ROOT))]=sha(raw)
        path=ROOT/SOURCES[program['origin']]/program['semantics_path']
        if sha(path.read_bytes())!=program['semantics_sha256']:raise ValueError('selected contract changed')
        pin(path)
    for path in sorted((ROOT/OBSERVER).iterdir()):
        if path.is_file() and path.suffix in ('.py','.cjs','.json','.md'):pin(path)
    for relative in ('projects/algorithm_solver/algsolve/judge/sandbox.py','projects/algorithm_solver/catalogue/boundary_policy.py','projects/algorithm_solver/catalogue/public_batch_adapter.py'):pin(ROOT/relative)
    return pins


def packet(pid,rows,indices):
    if type(pid) is not int or pid not in IDS:raise ValueError('fixed Q packet identity required')
    return {'schema':'gamma.q-official-wrapper-packet.v1','problem_id':pid,'calls':[{'args':rows[index]['args']} for index in indices]}


_PROJECTION_MODULES={}

def projection_rules():
    # Cache pure, hash-validated host code only; never cache a gate decision.
    path=ROOT/OBSERVER/'host_check.py'
    if path not in _PROJECTION_MODULES:_PROJECTION_MODULES[path]=load_module(path,'q_projection_rules')
    return _PROJECTION_MODULES[path]


def projected_record(pid,language,case,position):
    """Successful wire-size upper bound, NEVER an execution observation.

    Clone correspondence may permute physical pool IDs. Replacing every
    nonnull clone reference by n-1 bounds its decimal byte width. Such sizing
    rows need not be valid topology and are never judged or sent to a child.
    """
    base=projection_rules()
    record={'i':position,'native_route':'official-wrapper-q-v1','entry_kind':'python-solution-method' if language=='python' else 'javascript-official-function',
            'problem_id':pid,'method':base.METHODS[pid],'result':case['expected'],'result_type':'int' if language=='python' else 'number',
            'args_before':case['args'],'args_after':case['args'],'alias_edges':[],'node_identity':None,'node_integrity':None}
    if pid not in NATIVE:
        if pid in (126,140):record['result_type']='list' if language=='python' else 'object'
        return record
    model=case['args'][0];before=base.original_pool(pid,model);after=[dict(row) for row in before];n=len(before);root=model.get('root',0 if n else None)
    result_index=None;reordered=None;clones=[];clone_root=None
    if pid in (133,138):
        for row in before:
            copy={'value':row['value']}
            for field,value in row.items():
                if field=='value':continue
                copy[field]=[n-1 for _ in value] if field=='neighbors' else None if value is None else n-1
            clones.append(copy)
        clone_root=0 if n else None;record['result']={'__clone_pool__':clones,'root':clone_root}
        record['result_type']=('Node' if n else 'NoneType') if language=='python' else 'object'
    elif pid==142:
        result_index=case['expected'];record['result_type']=('ListNode' if result_index is not None else 'NoneType') if language=='python' else 'object'
        if result_index is not None:record['alias_edges']=[['result',f'args.0.pool.{result_index}']]
    elif pid==143:
        reordered=case['expected'];order=reordered['original_identity_order']
        for index,node in enumerate(order):after[node]['next']=order[index+1] if index+1<n else None
        record['result_type']='NoneType' if language=='python' else 'undefined'
    elif pid==141:record['result_type']='bool' if language=='python' else 'boolean'
    elif pid==144:record['result_type']='list' if language=='python' else 'object'
    record['args_after']=[{'__native_pool__':after,'root':root}]
    record['node_identity']={'before':before,'after':after,'argument_root':root,'original_node_count':n,'result_original_index':result_index,'clone_pool':clones,'clone_root':clone_root,'reordered':reordered}
    record['node_integrity']={'schema':'gamma.q-native-identity-integrity.v1','class_or_prototype_unchanged':True,'own_field_descriptors_unchanged':True,'original_node_classes_unchanged':True,'clone_pool_disjoint':True if pid in (133,138) else None,'original_neighbor_containers_unchanged':True if pid==133 else None}
    return record


def projected_stdout(pid,language,rows,indices):
    return sum(len(encoded(projected_record(pid,language,rows[index],position)))+1 for position,index in enumerate(indices))+len(encoded({'done':len(indices)}))+1+(language=='python')


def batch_plan(pid,rows):
    if not rows:raise ValueError('nonempty finite case population required')
    def measured(indices,policy):
        wire=encoded(packet(pid,rows,indices))
        return {'indices':indices,'policy':policy,'input_bytes':len(wire),'inputs_sha256':sha(wire),
                'projected_stdout_bytes':{language:projected_stdout(pid,language,rows,indices) for language in LANGUAGES},'output_cap_semantics':'stdout-and-stderr-each-16MiB','stderr_projection':'not inferred; actual stderr independently capped'}
    def fits(entry):return entry['input_bytes']<=MAX_INPUT_BYTES and max(entry['projected_stdout_bytes'].values())<=PER_STREAM_OUTPUT_BYTES
    single=[measured([index],'single-measurement') for index in range(len(rows))]
    probe=min(range(len(rows)),key=lambda index:single[index]['input_bytes']+max(single[index]['projected_stdout_bytes'].values()))
    plan=[];blocked=[];small=[]
    def block(index,entry):
        reason='single_input_exceeds_host_envelope' if entry['input_bytes']>MAX_INPUT_BYTES else 'single_successful_stdout_exceeds_per_stream_output_cap'
        blocked.append({'case':index,'case_identity':rows[index].get('case_identity'),'status':'blocked_transport','reason':reason,'input_bytes':entry['input_bytes'],'projected_stdout_bytes':entry['projected_stdout_bytes']})
    def flush():
        nonlocal small
        if small:
            entry=measured(small+[small[0]],'small-first-call-repeat')
            if not fits(entry):raise ValueError('small admission invariant failed')
            plan.append(entry);small=[]
    for index,row in enumerate(rows):
        if row.get('isolate') is True:
            flush();entry=measured([index],'owner-declared-isolated-maximum-or-certificate')
            if fits(entry):plan.append(entry)
            else:block(index,entry)
            continue
        trial=measured(small+[index]+[small[0] if small else index],'small-first-call-repeat')
        if small and (len(small)>=32 or trial['input_bytes']>256*1024 or not fits(trial)):
            flush();trial=measured([index,index],'repeated-case')
        if fits(trial) and trial['input_bytes']<=256*1024:small.append(index);continue
        flush()
        options=[measured([index,index],'large-repeat'),measured([probe,index,probe],'small-large-small'),measured([index],'singleton-partial-repetition-coverage')]
        entry=next((entry for entry in options if fits(entry)),None)
        if entry is None:block(index,options[-1])
        else:plan.append(entry)
    flush()
    covered={index for entry in plan for index in entry['indices']};excluded={row['case'] for row in blocked}
    if covered&excluded or covered|excluded!=set(range(len(rows))):raise ValueError('case silently omitted or doubly classified')
    return {'batch_policy':BATCH_POLICY,'projection_policy':PROJECTION_POLICY,'logical_case_count':len(rows),'admitted_distinct_cases':len(covered),
            'batches':plan,'blocked_cases':blocked,'owner_isolated_cases':sum(row.get('isolate') is True for row in rows),
            'coverage_limits':['Finite exposed-development suite only. Owner-isolated maxima run once; small repeats do not prove every maximum repeat.',
                               'Input-cardinality maxima do not establish maximum-output multiplicity, every topology, numeric boundary or universal resource behavior.']}


def parse(raw,count):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate observation key')
            result[key]=value
        return result
    rows=[json.loads(line,object_pairs_hook=pairs,parse_constant=lambda token:(_ for _ in ()).throw(ValueError(token))) for line in raw.decode('utf8').splitlines()]
    if len(rows)!=count+1 or type(rows[-1]) is not dict or set(rows[-1])!={'done'} or type(rows[-1]['done']) is not int or rows[-1]['done']!=count:raise ValueError('incomplete observation stream')
    normal={'i','native_route','entry_kind','problem_id','method','result','result_type','args_before','args_after','alias_edges','node_identity','node_integrity'}
    for index,row in enumerate(rows[:-1]):
        if type(row) is not dict or type(row.get('i')) is not int or row['i']!=index or set(row)!=({'i','error'} if 'error' in row else normal):raise ValueError('observation order or shape')
    return rows[:-1]


def verdict(pid,language,rows,indices,metadata,stdout,owner):
    if (type(metadata.get('exit_code')) is not int or metadata['exit_code']!=0 or metadata.get('signal') is not None or metadata.get('timed_out') is not False or metadata.get('output_limit_exceeded') is not False
            or type(metadata.get('stderr_bytes')) is not int or not 0<=metadata['stderr_bytes']<=PER_STREAM_OUTPUT_BYTES or len(stdout)>PER_STREAM_OUTPUT_BYTES):
        return [{'case':index,'case_identity':rows[index].get('case_identity'),'reason':'sandbox_process_failure'} for index in indices]
    try:records=parse(stdout,len(indices))
    except (ValueError,TypeError,UnicodeError,RecursionError):return [{'case':index,'case_identity':rows[index].get('case_identity'),'reason':'observation_protocol'} for index in indices]
    failures=[]
    for index,record in zip(indices,records):
        if 'error' in record:good,reason=False,'candidate_error'
        else:
            try:good,reason=owner.check_observation(pid,rows[index]['args'],record,language)
            except (ValueError,TypeError,KeyError,IndexError,OverflowError,RecursionError):good,reason=False,'host_checker_failure'
        if good is not True:failures.append({'case':index,'case_identity':rows[index].get('case_identity'),'reason':reason or 'host_checker_rejected'})
    return failures


def coverage_summary(data):
    summary={}
    for pid,rows in data.items():
        item={'prepared_cases':len(rows),'original_cases':sum(row['case_identity']['origin']=='q-original' for row in rows),
              'appended_certificates':sum(row['case_identity']['origin'].endswith('-certificate') for row in rows),
              'boundary_cases':sum(row['case_identity']['origin']=='q-boundary' for row in rows),
              'owner_isolated_cases':sum(row.get('isolate') is True for row in rows),'actual_candidate_executions':0}
        if pid in NATIVE:
            item['max_prepared_input_nodes']=max(len(row['args'][0]['values']) for row in rows)
            if pid==133:item['max_prepared_directed_neighbor_entries']=max(sum(map(len,row['args'][0]['neighbors'])) for row in rows)
            if pid==129:item['max_prepared_expected_integer']=max(row['expected'] for row in rows)
            if pid in (129,144):item['right_only_child_nodes']=sum(sum(l is None and r is not None for l,r in zip(row['args'][0]['left'],row['args'][0]['right'])) for row in rows)
            if pid in (141,142):item['max_size_cycle_positions']=sorted({row['args'][0]['pos'] for row in rows if len(row['args'][0]['values'])==item['max_prepared_input_nodes']})
        elif pid==126:
            item.update(max_prepared_dictionary_words=max(len(row['args'][2]) for row in rows),
                        max_prepared_expected_path_count=max(len(row['expected']) for row in rows),
                        max_prepared_expected_total_answer_words=max(sum(map(len,row['expected'])) for row in rows),
                        max_prepared_expected_path_words=max((len(path) for row in rows for path in row['expected']),default=0),
                        output_multiplicity_promise_fully_exercised=False)
        elif pid==140:
            item.update(max_prepared_input_characters=max(len(row['args'][0]) for row in rows),max_prepared_dictionary_words=max(len(row['args'][1]) for row in rows),
                        max_prepared_expected_sentence_count=max(len(row['expected']) for row in rows),
                        max_prepared_expected_answer_characters=max(sum(map(len,row['expected'])) for row in rows),output_multiplicity_promise_fully_exercised=False)
        else:item.update(max_prepared_input_characters=max(len(row['args'][0]) for row in rows),max_prepared_expected_integer=max(row['expected'] for row in rows))
        item['scope_limit']='Finite input/effect witnesses; not every topology, output multiplicity, numeric boundary or universal resources.'
        summary[str(pid)]=item
    return summary


def review_flags(pid):return REVIEW_FLAGS+(NATIVE_FLAGS if pid in NATIVE else ())+(REPAIR_FLAGS if pid in (126,140) else ())


def review_binding(pop,program):
    pid,language=program['problem_id'],program['language'];spec=next(row for row in pop['problems'] if row['id']==pid)
    directory=ROOT/SOURCES[program['origin']];checker=directory/'host_check.py' if pid in (126,140) else ROOT/OBSERVER/'host_check.py'
    generator=directory/'cases.py';history=directory/('pre-source-design-freeze.json' if pid in (126,140) else 'pre-source-reference-freeze.json')
    observer=ROOT/OBSERVER/('harness.py' if language=='python' else 'harness.cjs')
    helper=ROOT/OBSERVER/('models.py' if language=='python' else 'identity_models.cjs')
    packet=pop['packets'][program['origin']]
    return {'source_sha256':program['source_sha256'],'semantics_sha256':program['semantics_sha256'],'selected_manifest_sha256':packet['manifest_sha256'],'assignment_sha256':packet['assignment_sha256'],
            'definition_content_sha256':spec['content_sha256'],'preserved_raw_metadata_sha256':spec['raw_metadata_sha256'],'actual_official_api_sha256':spec['official_api_sha256'],
            'actual_language_template_sha256':spec['template_sha256']['python3' if language=='python' else 'javascript'],
            'observer_profile_sha256':OBSERVER_PIN,'observer_sha256':sha(observer.read_bytes()),'identity_helper_sha256':sha(helper.read_bytes()),
            'host_checker_sha256':sha(checker.read_bytes()),'case_generator_sha256':sha(generator.read_bytes()),
            'original_reference_sha256':sha((ROOT/SOURCES['original']/'oracles.py').read_bytes()),'original_cases_sha256':sha((ROOT/SOURCES['original']/'cases.py').read_bytes()),
            'exposure_design_history_sha256':sha(history.read_bytes()),'raw_metadata_corrections_sha256':sha((ROOT/SOURCES['original']/'metadata-reconciliation.json').read_bytes()),
            'frozen_q_host_checker_sha256':sha((ROOT/OBSERVER/'host_check.py').read_bytes()),
            'boundary_cases_sha256':sha((HERE/'boundary_cases.py').read_bytes()),
            'boundary_checker_sha256':sha((HERE/'boundary_check.py').read_bytes()) if pid in (126,140) else None}


def evaluate_reviews(pop,records):
    wanted={(row['problem_id'],row['language']) for row in pop['programs']};observed={}
    if type(records) is not list:raise ValueError('review records must be a list')
    for row in records:
        if type(row) is not dict:raise ValueError('review row shape')
        pid,language=row.get('problem_id'),row.get('language');identity=(pid,language)
        if type(pid) is not int or type(language) is not str or identity not in wanted or identity in observed:raise ValueError('unknown, duplicate or non-integer review identity')
        observed[identity]=row
    result={}
    for program in pop['programs']:
        pid,language=program['problem_id'],program['language'];row=observed.get((pid,language),{});binding=review_binding(pop,program)
        approved=(all(row.get(name)==pin for name,pin in binding.items()) and isinstance(row.get('reviewer'),str) and bool(row['reviewer'].strip()) and all(row.get(flag) is True for flag in review_flags(pid)))
        result[f'{pid}:{language}']={'approved':approved,'record':row,'reason':None if approved else 'missing/false/differently-bound mandatory independent source/template/complexity/effect review'}
    return result


def manual_reviews(path,pop):
    value={'programs':[]} if path is None else read_json(path)
    if type(value) is not dict or type(value.get('programs')) is not list:raise ValueError('manual review envelope required')
    return evaluate_reviews(pop,value['programs'])


def review_template(args):
    pop=population();gate=gate_file(args.gate,args.gate_sha256);artifacts(pop,gate);records=[]
    for program in pop['programs']:
        pid,language=program['problem_id'],program['language']
        records.append({'problem_id':pid,'language':language,'reviewer':'',**review_binding(pop,program),**{flag:False for flag in review_flags(pid)}})
    write(args.review,{'schema':'gamma.q-boundary-mandatory-official-source-review.v1','programs':records,'note':'All flags false. This is no execution/access/qualification approval.'})
    return {'programs':len(records),'approved':0,'candidate_executions':0}


def freeze(args):
    pop=population();gate=gate_file(args.gate,args.gate_sha256);runtime_pins=runtime()
    log=args.preflight.read_bytes()
    if sha(log)!=args.preflight_sha256 or re.search(rb'\b37 passed\b',log) is None:raise ValueError('exact passing existing37-check Linux preflight required')
    definition_pins=definitions(args.statements,pop,gate);pins=artifacts(pop,gate);data,_=cases_and_owners(pop)
    plans={str(pid):batch_plan(pid,rows) for pid,rows in data.items()};reviews=manual_reviews(args.review,pop)
    if artifacts(pop,gate)!=pins:raise ValueError('source/helper changed while preparing freeze')
    contract={'schema':SCHEMA,'created_at':datetime.now(timezone.utc).isoformat(),'population_sha256':sha((HERE/'population.json').read_bytes()),
              'artifact_hashes':pins,'runtime':runtime_pins,'argv':ARGV,'limits':asdict(LIMITS),'max_input_bytes':MAX_INPUT_BYTES,'per_stream_output_bytes':PER_STREAM_OUTPUT_BYTES,'dispatch_policy':DISPATCH_POLICY,
              'batch_policy':BATCH_POLICY,'projection_policy':PROJECTION_POLICY,'program_count':program_count(pop),'problem_count':len(data),
              'statement_pins':definition_pins,'boundary_trusted_hashes':gate['trusted_hashes'],'execution_gate_sha256':args.gate_sha256,
              'case_sha256':sha(encoded(data)),'prepared_case_coverage':coverage_summary(data),'case_counts':{str(pid):len(rows) for pid,rows in data.items()},'batch_plans':plans,
              'manual_reviews':reviews,'review_records':[row['record'] for row in reviews.values() if row['record']],
              'preflight_sha256':args.preflight_sha256,'selected_programs':pop['programs'],'excluded_superseded_variants':pop['excluded_superseded_variants'],
              'observer_profile_used_unchanged':OBSERVER_PIN,'scope':'Finite exposed-development official ABI/effect suites: original Q cases plus independently referenced boundary cases for 126/129/140/144. Original126/140 excluded. No universal resources, unseen generalization, canonical adoption or publication claim.',
              'canonical_admission_changed':False,'local_private_statements_transferred':False}
    write(args.freeze,contract)
    return {'freeze_sha256':sha(args.freeze.read_bytes()),'programs':program_count(pop),'problems':len(data),'candidate_executions':0,
            'blocked_transport_cases':sum(len(plan['blocked_cases']) for plan in plans.values())}


def verified_inputs(args,check_runtime):
    raw=args.freeze.read_bytes()
    if sha(raw)!=args.freeze_sha256:raise ValueError('exact frozen execution identity required')
    contract=decode_json(raw)
    if (contract.get('schema')!=SCHEMA or not exact(contract.get('argv'),ARGV) or not exact(contract.get('limits'),asdict(LIMITS)) or type(contract.get('max_input_bytes')) is not int or contract['max_input_bytes']!=MAX_INPUT_BYTES
            or type(contract.get('per_stream_output_bytes')) is not int or contract['per_stream_output_bytes']!=PER_STREAM_OUTPUT_BYTES or contract.get('dispatch_policy')!=DISPATCH_POLICY or contract.get('batch_policy')!=BATCH_POLICY or contract.get('projection_policy')!=PROJECTION_POLICY):raise ValueError('frozen runtime/transport settings changed')
    pop=population();gate=gate_file(args.gate,args.gate_sha256)
    if (contract.get('population_sha256')!=sha((HERE/'population.json').read_bytes()) or type(contract.get('program_count')) is not int or contract['program_count']!=program_count(pop)
            or not exact(contract.get('selected_programs'),pop['programs']) or not exact(contract.get('excluded_superseded_variants'),pop['excluded_superseded_variants'])):raise ValueError('frozen selected program identity/count changed')
    if not exact(gate['trusted_hashes'],contract['boundary_trusted_hashes']):raise ValueError('existing boundary anchors changed')
    if check_runtime and (args.gate_sha256!=contract['execution_gate_sha256'] or not exact(runtime(),contract['runtime'])):raise ValueError('execution gate or runtime drift')
    if artifacts(pop,gate)!=contract['artifact_hashes']:raise ValueError('source/contract/helper/history drift')
    if definitions(args.statements,pop,gate)!=contract['statement_pins']:raise ValueError('executor definition/template snapshot drift')
    data,owners=cases_and_owners(pop)
    if type(contract.get('problem_count')) is not int or contract['problem_count']!=len(data) or sha(encoded(data))!=contract['case_sha256'] or not exact(contract['case_counts'],{str(pid):len(rows) for pid,rows in data.items()}):raise ValueError('finite case identity/count drift')
    if not exact(contract.get('prepared_case_coverage'),coverage_summary(data)):raise ValueError('prepared witness coverage statement drift')
    for pid,rows in data.items():
        if not exact(batch_plan(pid,rows),contract['batch_plans'][str(pid)]):raise ValueError('prospective case admission/bytes drift')
    if not exact(evaluate_reviews(pop,contract['review_records']),contract['manual_reviews']):raise ValueError('frozen review records cannot justify approvals')
    if artifacts(pop,gate)!=contract['artifact_hashes']:raise ValueError('source/helper changed during verification')
    return raw,contract,pop,gate,data,owners


def program_summary(program,rows,plan,failures,total,review):
    planned_calls=sum(len(entry['indices']) for entry in plan['batches'])
    dispatch_approved=review.get('approved') is True
    execution_complete=dispatch_approved and type(total) is int and total==planned_calls
    admitted=plan['admitted_distinct_cases']>0 and not failures and execution_complete
    complete=admitted and not plan['blocked_cases'] and plan['admitted_distinct_cases']==len(rows)
    return {'problem_id':program['problem_id'],'language':program['language'],'origin':program['origin'],'source_sha256':program['source_sha256'],
            'distinct_cases':len(rows),'admitted_distinct_cases':plan['admitted_distinct_cases'],'executed_calls':total,'planned_calls':planned_calls,'execution_complete':execution_complete,'failures':failures,'transport_blocked_cases':plan['blocked_cases'],
            'admitted_cases_passed':admitted,'complete_prepared_suite_passed':complete,'mandatory_review_approved':dispatch_approved,'dispatch_authorized':dispatch_approved,'dispatch_blocked_reason':None if dispatch_approved else 'mandatory_source_review_not_approved','qualified':complete and dispatch_approved,
            'actual_official_entry_suite_qualified':complete and dispatch_approved,'canonical_admission_changed':False,
            'scope':'Finite source-bound official entry/effects only; no maximum-output multiplicity, every-topology, universal resource or fresh-generalization claim.'}


def aggregate_report(raw,contract,summaries):
    pairs={}
    for row in summaries:pairs.setdefault(row['problem_id'],{})[row['language']]=row['qualified']
    return {'schema':'gamma.q-boundary-execution-report.v1','freeze_sha256':sha(raw),'program_count':len(summaries),'programs':summaries,
            'executed_call_count':sum(row.get('executed_calls',0) for row in summaries),'dispatch_blocked_program_count':sum(row.get('dispatch_authorized') is not True for row in summaries),'qualified_program_count':sum(row['qualified'] for row in summaries),'qualified_problem_pair_count':sum(set(value)==set(LANGUAGES) and all(value.values()) for value in pairs.values()),
            'canonical_admission_changed':False,'scope':contract['scope']}


def staged_files(program,source,wire,contract):
    language=program['language'];files={'program.py' if language=='python' else 'program.cjs':source,'inputs.json':wire}
    names=('harness.py','models.py') if language=='python' else ('harness.cjs','identity_models.cjs')
    for name in names:
        path=ROOT/OBSERVER/name;raw=path.read_bytes()
        if sha(raw)!=contract['artifact_hashes'][str(path.relative_to(ROOT))]:raise ValueError('unchanged Q observer/helper drift before dispatch')
        files[name]=raw
    return files


def execute(args):
    raw,contract,pop,gate,data,owners=verified_inputs(args,True);args.output.mkdir(parents=True,exist_ok=False)
    write(args.output/'run-identity.json',{'freeze_sha256':sha(raw),'artifact_hashes':contract['artifact_hashes'],'runtime':contract['runtime'],
                                       'selected_programs':contract['selected_programs'],'host':platform.node(),'started_at':datetime.now(timezone.utc).isoformat()})
    summaries=[]
    for program in pop['programs']:
        pid,language=program['problem_id'],program['language'];rows=data[pid];plan=contract['batch_plans'][str(pid)];failures=[];total=0
        review=contract['manual_reviews'].get(f'{pid}:{language}',{'approved':False,'record':{},'reason':'missing mandatory review'})
        for batch_index,entry in enumerate(plan['batches'] if review.get('approved') is True else []):
            indices=entry['indices'];wire=encoded(packet(pid,rows,indices))
            if len(wire)!=entry['input_bytes'] or sha(wire)!=entry['inputs_sha256'] or len(wire)>MAX_INPUT_BYTES:raise ValueError('frozen packet bytes drift')
            access(gate,pid,language,'source');path=program_path(program);source=bounded_regular_read(path,maximum_bytes=1024**2)
            if sha(source)!=program['source_sha256']:raise ValueError('exact selected source changed before launch')
            files=staged_files(program,source,wire,contract);stem=f'{pid}-{language}-{batch_index:04d}'
            write(args.output/(stem+'.start.json'),{'problem_id':pid,'language':language,'origin':program['origin'],'source_sha256':sha(source),'indices':indices,'inputs_sha256':sha(wire),'planned':entry})
            try:result=sandbox.run(ARGV[language],files=files,limits=LIMITS)
            except Exception as error:
                write(args.output/(stem+'.launch-error.json'),{'status':'execution_outcome_not_confirmed','error_type':type(error).__name__,'detail':str(error)[:300],'automatic_retry':False})
                raise
            metadata=asdict(result)
            for name in ('stdout','stderr'):
                stream=metadata.pop(name)
                with (args.output/(stem+'.'+name)).open('xb') as handle:handle.write(stream);handle.flush();os.fsync(handle.fileno())
                metadata[name+'_sha256']=sha(stream);metadata[name+'_bytes']=len(stream)
            metadata['input_bytes']=len(wire);write(args.output/(stem+'.result.json'),metadata)
            failures.extend(verdict(pid,language,rows,indices,metadata,result.stdout,owners[pid]));total+=len(indices)
        summary=program_summary(program,rows,plan,failures,total,review);summaries.append(summary)
        write(args.output/f'{pid}-{language}.summary.json',summary)
    report=aggregate_report(raw,contract,summaries)
    if len(summaries)!=program_count(pop):raise ValueError('selected program missing from final report')
    write(args.output/'report.json',report)
    return {key:report[key] for key in ('program_count','executed_call_count','dispatch_blocked_program_count','qualified_program_count','qualified_problem_pair_count','canonical_admission_changed')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('plan','prepare','review-template','freeze','run','replay'))
    for name in ('gate','statements','freeze','preflight','review','output'):parser.add_argument('--'+name,type=Path)
    for name in ('gate-sha256','freeze-sha256','preflight-sha256'):parser.add_argument('--'+name)
    args=parser.parse_args()
    required={'plan':(), 'prepare':('gate','gate_sha256','statements'),'review-template':('gate','gate_sha256','review'),
              'freeze':('gate','gate_sha256','statements','preflight','preflight_sha256','freeze'),
              'run':('gate','gate_sha256','statements','freeze','freeze_sha256','output'),'replay':('gate','gate_sha256','statements','freeze','freeze_sha256','output')}
    for name in required[args.operation]:
        if getattr(args,name) is None:parser.error('missing --'+name.replace('_','-'))
    if args.operation=='plan':
        pop=population();data,_=cases_and_owners(pop);plans={str(pid):batch_plan(pid,rows) for pid,rows in data.items()}
        result={'programs':program_count(pop),'case_counts':{str(pid):len(rows) for pid,rows in data.items()},'plans':plans,'candidate_executions':0}
    elif args.operation=='prepare':result=prepare(args)
    elif args.operation=='review-template':result=review_template(args)
    elif args.operation=='freeze':result=freeze(args)
    elif args.operation=='run':result=execute(args)
    else:
        from verify import verify
        result=verify(args)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
