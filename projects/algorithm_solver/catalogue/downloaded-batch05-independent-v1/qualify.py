"""Fixed batch05 controller; existing sandbox/observers, no authority creation.

All public-definition, source and review pins must be supplied before dispatch.
Importing this module or generating a review template never executes a program.
"""
from dataclasses import asdict
import argparse
import importlib.util
from pathlib import Path
import re
import sys
import urllib.request

import cases
import oracles

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SUPPORT=ROOT/'projects/algorithm_solver/catalogue/continuation-qualification-20261028-v1/protocol.py'
spec=importlib.util.spec_from_file_location('batch05_existing_judge_support',SUPPORT)
engine=importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
encoded,sha,read_json,write=engine.encoded,engine.sha,engine.read_json,engine.write
LANGUAGES=('python','javascript')
SCHEMA='gamma.batch05-fixed-execution.v1'
FLAGS=engine.REVIEW_FLAGS
DISPATCH_FLAGS=('independent_source_review','source_safety','exact_domain_interface','independent_references_and_boundaries')
BLOCKED=(562,616,625,634,651,681,694)
POLICY='gamma.downloaded-batch05-probe-bracket.v1'
SELECTION=read_json(HERE/'execution-selection.json')
RESERVED=(556,565,583,592,621,624,646,680,684)
SELECTED=tuple(pid for pid in cases.IDS if pid not in RESERVED)
OBJECT_TRANSPORT=Path('projects/algorithm_solver/catalogue/imported-commonjs-observer-v1/harness.cjs')
if SELECTION['selected_ids']!=list(SELECTED) or SELECTION['reserved_excluded_ids']!=list(RESERVED):raise ValueError('prospective selection drift')
SOURCE_DIRECTORY=Path('projects/algorithm_solver/catalogue/authored/downloaded-general47-v1')
SCOPE='Finite exposed-development solve adapters; no official-wrapper, unseen-generalization or canonical-adoption claim.'
LOADED={Path(p):sha(Path(p).read_bytes()) for p in (__file__,cases.__file__,oracles.__file__,str(SUPPORT),engine.sandbox.__file__,engine.authorize_before_open.__code__.co_filename,engine.bounded_regular_read.__code__.co_filename)}
QUERY='query questionData($titleSlug: String!) { question(titleSlug:$titleSlug) { questionId questionFrontendId title titleSlug isPaidOnly content exampleTestcaseList metaData } }'


def population(source_root):
    contract=read_json(HERE/'contracts.json')
    directory=Path(source_root)/SOURCE_DIRECTORY
    for name,field in (('assignment.public-safe.json','assignment_sha256'),('manifest.json','source_import_manifest_sha256')):
        if sha((directory/name).read_bytes())!=contract[field]:raise ValueError('assigned metadata drift')
    manifest=read_json(directory/'manifest.json')
    observed={}
    for row in manifest['source_inventory']:
        pid,language=row['id'],row['language']
        if type(pid) is not int or pid not in oracles.IDS or language not in LANGUAGES or (pid,language) in observed:
            raise ValueError('unknown or duplicate source identity')
        suffix='py' if language=='python' else 'js'
        if row['path']!=f'{language}/{pid}.{suffix}' or row['semantics_path']!=f'semantics/{pid}.json':
            raise ValueError('source/contract locator escaped exact assignment')
        observed[pid,language]=row
    if set(observed)!={(p,l) for p in oracles.IDS for l in LANGUAGES}:raise ValueError('incomplete source inventory')
    if tuple(p for p in oracles.IDS if p not in cases.IDS)!=BLOCKED:raise ValueError('blocked population drift')
    return directory,{key:value for key,value in observed.items() if key[0] in SELECTED}


def gate(args):
    result=engine.gate_file(args.gate,args.gate_sha256)
    from catalogue.boundary_policy import ARTIFACTS
    if set(result['artifact_paths'])!=set(ARTIFACTS) or set(result['trusted_hashes'])!=set(ARTIFACTS):
        raise ValueError('all six exact boundary anchors required')
    return result


def definition_reader(args,g):
    def read(path):
        pid=int(path.stem)
        if pid not in SELECTED or path!=args.statements/f'{pid}.json':raise ValueError('unassigned definition locator')
        for language in LANGUAGES:engine.access(g,pid,language,'statement')
        return engine.bounded_regular_read(path,maximum_bytes=4*1024**2)
    return read


def data(args,g):
    return cases.build(args.statements, read_raw=definition_reader(args,g), selected_ids=SELECTED)


def artifacts(args,g,inventory):
    if any(sha(path.read_bytes())!=pin for path,pin in LOADED.items()):raise ValueError('loaded controller/support drift; restart with reviewed code')
    pins={}
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.suffix in ('.py','.json','.md'):pins[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    paths=[SUPPORT,ROOT/engine.TRANSPORT/'harness.py',ROOT/engine.TRANSPORT/'harness.cjs',ROOT/OBJECT_TRANSPORT,
           ROOT/'projects/algorithm_solver/algsolve/judge/sandbox.py',ROOT/'projects/algorithm_solver/catalogue/boundary_policy.py',
           ROOT/'projects/algorithm_solver/catalogue/public_batch_adapter.py']
    for path in paths:pins[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    directory=Path(args.source_root)/SOURCE_DIRECTORY
    for (pid,language),row in inventory.items():
        engine.access(g,pid,language,'source')
        raw=engine.bounded_regular_read(directory/row['path'],maximum_bytes=1024**2)
        if sha(raw)!=row['sha256']:raise ValueError('source drift')
        engine.access(g,pid,language,'source')
        raw=engine.bounded_regular_read(directory/row['semantics_path'],maximum_bytes=1024**2)
        if sha(raw)!=row['semantics_sha256']:raise ValueError('semantics drift')
        for field in ('path','semantics_path'):pins[str(SOURCE_DIRECTORY/row[field])]=row['sha256' if field=='path' else 'semantics_sha256']
    return pins


def binding(pid,language,row,pins):
    problem=next(p for p in read_json(HERE/'contracts.json')['problems'] if p['id']==pid)
    observer=engine.TRANSPORT/'harness.py' if language=='python' else OBJECT_TRANSPORT
    return {'source_sha256':row['sha256'],'semantics_sha256':row['semantics_sha256'],
            'reference_sha256':sha((HERE/'oracles.py').read_bytes()),'case_generator_sha256':sha((HERE/'cases.py').read_bytes()),
            'contracts_sha256':sha((HERE/'contracts.json').read_bytes()),
            'definition_content_sha256':problem['definition']['content_sha256'],
            'official_metadata_sha256':problem['official_signature_metadata']['metadata_sha256'],
            'observer_sha256':pins[str(observer)],'shared_effect_observer_sha256':pins[str(engine.TRANSPORT/'harness.cjs')],
            'batch_policy':POLICY}


def reviews(path,inventory,pins):
    records=[] if path is None else read_json(path)['programs']
    supplied={}
    for row in records:
        key=row.get('problem_id'),row.get('language')
        if type(key[0]) is not int or key not in inventory or key in supplied:raise ValueError('unknown/duplicate source review')
        supplied[key]=row
    result={}
    for (pid,lang),source in inventory.items():
        row=supplied.get((pid,lang),{})
        approved=(all(row.get(k)==v for k,v in binding(pid,lang,source,pins).items()) and
                  isinstance(row.get('reviewer'),str) and bool(row['reviewer'].strip()) and all(row.get(flag) is True for flag in FLAGS))
        dispatch=(all(row.get(k)==v for k,v in binding(pid,lang,source,pins).items()) and isinstance(row.get('reviewer'),str) and bool(row['reviewer'].strip()) and all(row.get(flag) is True for flag in DISPATCH_FLAGS))
        result[f'{pid}:{lang}']={'approved':approved,'dispatch_approved':dispatch,'record':row}
    return result


def prepare(args):
    population(args.source_root);g=gate(args)
    problems={p['id']:p for p in read_json(HERE/'contracts.json')['problems']}
    args.statements.mkdir(parents=True,exist_ok=False)
    for pid in SELECTED:
        problem=problems[pid]
        for language in LANGUAGES:
            engine.access(g,pid,language,'source');engine.access(g,pid,language,'statement')
        request=urllib.request.Request('https://leetcode.com/graphql/',
            data=encoded({'query':QUERY,'variables':{'titleSlug':problem['definition']['slug']}}),
            headers={'Content-Type':'application/json','User-Agent':'Gamma public-domain qualification'})
        with urllib.request.urlopen(request,timeout=25) as response:raw=response.read(4*1024**2+1)
        with (args.statements/f'{pid}.json').open('xb') as stream:
            stream.write(raw);stream.flush();engine.os.fsync(stream.fileno())
        if len(raw)>4*1024**2 or sha(raw)!=problem['definition']['snapshot_sha256']:
            raise ValueError('refetched snapshot differs from reference design; response retained, review new identity explicitly')
    cases.validate_definitions(args.statements,read_raw=definition_reader(args,g), selected_ids=SELECTED)
    return {'definitions':len(SELECTED),'premium_blocked':list(BLOCKED),'candidate_executions':0}


def review_template(args):
    _,inventory=population(args.source_root);g=gate(args);pins=artifacts(args,g,inventory)
    write(args.review,{'programs':[{'problem_id':pid,'language':lang,'reviewer':'',**binding(pid,lang,row,pins),
                                  **{flag:False for flag in FLAGS}} for (pid,lang),row in inventory.items()]})
    return {'templates':len(SELECTED)*2,'candidate_executions':0,'approved':0}


def freeze(args):
    runtime=engine.runtime()  # Linux-only; no host fallback or provisioning.
    preflight=args.preflight.read_bytes()
    if sha(preflight)!=args.preflight_sha256 or re.search(rb'\b37 passed\b',preflight) is None:
        raise ValueError('exact passing existing 37-check judge preflight required')
    _,inventory=population(args.source_root);g=gate(args);rows=data(args,g);pins=artifacts(args,g,inventory)
    value={'schema':SCHEMA,'ids':list(SELECTED),'blocked_ids':list(BLOCKED),'reserved_ids':list(RESERVED),'artifact_hashes':pins,
           'runtime':runtime,'limits':asdict(engine.LIMITS),'argv':engine.ARGV,'batch_policy':POLICY,
           'host_packet_budget':cases.MAX_HOST_PACKET_BYTES,'output_budget':cases.MAX_EXPECTED_OUTPUT_BYTES,
           'case_sha256':sha(encoded(rows)),'plans':{str(pid):cases.batch_plan(values) for pid,values in rows.items()},
           'reviews':reviews(args.review,inventory,pins),'boundary_trusted_hashes':g['trusted_hashes'],
           'execution_gate_sha256':args.gate_sha256,'preflight_sha256':args.preflight_sha256,
           'definitions':{str(pid):sha(definition_reader(args,g)(args.statements/f'{pid}.json')) for pid in SELECTED},'scope':SCOPE}
    write(args.freeze,value)
    return {'freeze_sha256':sha(args.freeze.read_bytes()),'programs':len(SELECTED)*2,'candidate_executions':0}


def verified(args,live):
    raw=args.freeze.read_bytes()
    if sha(raw)!=args.freeze_sha256:raise ValueError('freeze identity mismatch')
    value=read_json(args.freeze)
    if (value.get('schema')!=SCHEMA or value.get('ids')!=list(SELECTED) or value.get('blocked_ids')!=list(BLOCKED) or value.get('reserved_ids')!=list(RESERVED)
        or value.get('argv')!=engine.ARGV or value.get('limits')!=asdict(engine.LIMITS) or value.get('batch_policy')!=POLICY
        or value.get('host_packet_budget')!=cases.MAX_HOST_PACKET_BYTES or value.get('output_budget')!=cases.MAX_EXPECTED_OUTPUT_BYTES):
        raise ValueError('fixed execution policy drift')
    directory,inventory=population(args.source_root);g=gate(args)
    if g['trusted_hashes']!=value['boundary_trusted_hashes']:raise ValueError('boundary anchor drift')
    if live and (args.gate_sha256!=value['execution_gate_sha256'] or engine.runtime()!=value['runtime']):raise ValueError('runtime/gate drift')
    if artifacts(args,g,inventory)!=value['artifact_hashes']:raise ValueError('source/helper drift')
    rows=data(args,g)
    if sha(encoded(rows))!=value['case_sha256']:raise ValueError('case drift')
    if {str(p):cases.batch_plan(v) for p,v in rows.items()}!=value['plans']:raise ValueError('plan drift')
    if {str(p):sha(definition_reader(args,g)(args.statements/f'{p}.json')) for p in SELECTED}!=value['definitions']:raise ValueError('definition drift')
    if reviews_from_frozen(value,inventory)!=value['reviews']:raise ValueError('review binding drift')
    return value,directory,inventory,g,rows


def reviews_from_frozen(value,inventory):
    result={}
    for (pid,lang),source in inventory.items():
        review=value['reviews'][f'{pid}:{lang}'];row=review['record']
        approved=(all(row.get(k)==v for k,v in binding(pid,lang,source,value['artifact_hashes']).items()) and
                  isinstance(row.get('reviewer'),str) and bool(row['reviewer'].strip()) and all(row.get(flag) is True for flag in FLAGS))
        dispatch=(all(row.get(k)==v for k,v in binding(pid,lang,source,value['artifact_hashes']).items()) and isinstance(row.get('reviewer'),str) and bool(row['reviewer'].strip()) and all(row.get(flag) is True for flag in DISPATCH_FLAGS))
        result[f'{pid}:{lang}']={'approved':approved,'dispatch_approved':dispatch,'record':row}
    return result


def verdict(pid,lang,values,indices,metadata,stdout):
    if (type(metadata.get('exit_code')) is not int or metadata['exit_code']!=0 or metadata.get('timed_out') is not False
        or metadata.get('output_limit_exceeded') is not False):return [{'case':i,'reason':'sandbox_process_failure'} for i in indices]
    try:observed=engine.parse(stdout,len(indices))
    except (ValueError,TypeError,UnicodeError):return [{'case':i,'reason':'observation_protocol'} for i in indices]
    failures=[]
    for i,record in zip(indices,observed):
        good,reason=oracles.compare(pid,values[i]['args'],values[i]['expected'],record,lang)
        if not good:failures.append({'case':i,'reason':reason})
    return failures


def summary(pid,lang,values,review,total,failures):
    planned=sum(len(indices) for indices in cases.batch_plan(values))
    complete=review['dispatch_approved'] and total==planned and total>0 and not failures
    return {'problem_id':pid,'language':lang,'distinct_cases':len(values),'planned_calls':planned,'executed_calls':total,
            'failures':failures,'blocked_review':not review['dispatch_approved'],'mandatory_review_approved':review['approved'],'complete_prepared_suite_passed':complete,
            'qualified_finite_suite':complete and review['approved'],'official_wrapper_execution_qualified':False,'canonical_admission_changed':False}


def run_or_replay(args,replay=False):
    value,directory,inventory,g,rows=verified(args,not replay)
    if not replay:
        args.output.mkdir(parents=True,exist_ok=False)
        write(args.output/'identity.json',{'freeze_sha256':args.freeze_sha256,'runtime':value['runtime'],'artifact_hashes':value['artifact_hashes']})
    identity=read_json(args.output/'identity.json')
    if not oracles.exact(identity,{'freeze_sha256':args.freeze_sha256,'runtime':value['runtime'],'artifact_hashes':value['artifact_hashes']}):raise ValueError('saved run identity drift')
    summaries=[]
    for pid in SELECTED:
        for lang in LANGUAGES:
            review=value['reviews'][f'{pid}:{lang}'];total=0;failures=[]
            if review['dispatch_approved']:
                for index,indices in enumerate(value['plans'][str(pid)]):
                    wire=encoded(cases.packet(rows[pid],indices));source_row=inventory[pid,lang]
                    stem=args.output/f'{pid}-{lang}-{index:04d}'
                    start={'problem_id':pid,'language':lang,'indices':indices,'inputs_sha256':sha(wire),'source_sha256':source_row['sha256']}
                    if not replay:
                        engine.access(g,pid,lang,'source')
                        source=engine.bounded_regular_read(directory/source_row['path'],maximum_bytes=1024**2)
                        if sha(source)!=source_row['sha256']:raise ValueError('source changed immediately before dispatch')
                        suffix='py' if lang=='python' else 'js';files={'program.'+suffix:source,'inputs.json':wire}
                        observer_files={'harness.py':engine.TRANSPORT/'harness.py'} if lang=='python' else {'harness.cjs':OBJECT_TRANSPORT,'observer.cjs':engine.TRANSPORT/'harness.cjs'}
                        for name,path in observer_files.items():
                            files[name]=(ROOT/path).read_bytes()
                            if sha(files[name])!=value['artifact_hashes'][str(path)]:raise ValueError('observer dispatch drift')
                        write(str(stem)+'.start.json',start)
                        try:result=engine.sandbox.run(engine.ARGV[lang],files=files,limits=engine.LIMITS)
                        except Exception as error:
                            write(str(stem)+'.dispatch-error.json',{'exception_type':type(error).__name__,'message':str(error)[:4096],'process_result_available':False})
                            raise
                        metadata=asdict(result)
                        for name in ('stdout','stderr'):
                            raw=metadata.pop(name)
                            with Path(str(stem)+'.'+name).open('xb') as stream:
                                stream.write(raw);stream.flush();engine.os.fsync(stream.fileno())
                            metadata[name+'_sha256']=sha(raw);metadata[name+'_bytes']=len(raw)
                        write(str(stem)+'.result.json',metadata)
                    if not oracles.exact(read_json(str(stem)+'.start.json'),start):raise ValueError('batch identity drift')
                    metadata=read_json(str(stem)+'.result.json');streams={}
                    for name in ('stdout','stderr'):
                        streams[name]=engine.bounded_regular_read(Path(str(stem)+'.'+name),maximum_bytes=engine.LIMITS.max_output_bytes)
                        if sha(streams[name])!=metadata[name+'_sha256'] or type(metadata[name+'_bytes']) is not int or len(streams[name])!=metadata[name+'_bytes']:raise ValueError('raw evidence drift')
                    failures.extend(verdict(pid,lang,rows[pid],indices,metadata,streams['stdout']));total+=len(indices)
            result=summary(pid,lang,rows[pid],review,total,failures);summaries.append(result)
            path=args.output/f'{pid}-{lang}.summary.json'
            if replay:
                if not oracles.exact(read_json(path),result):raise ValueError('summary replay mismatch')
            else:write(path,result)
    report={'schema':SCHEMA,'freeze_sha256':args.freeze_sha256,'programs':summaries,'scope':SCOPE,'canonical_admission_changed':False}
    if replay:
        if not oracles.exact(read_json(args.output/'report.json'),report):raise ValueError('aggregate replay mismatch')
    else:write(args.output/'report.json',report)
    return {'programs':len(summaries),'executed_calls':sum(s['executed_calls'] for s in summaries),
            'qualified_finite_suite_programs':sum(s['qualified_finite_suite'] for s in summaries),
            'replayed':replay,'candidate_execution_on_replay_host':False if replay else None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('prepare','review-template','freeze','run','replay'))
    for name in ('source-root','gate','statements','freeze','preflight','review','output'):parser.add_argument('--'+name,type=Path)
    for name in ('gate-sha256','freeze-sha256','preflight-sha256'):parser.add_argument('--'+name)
    args=parser.parse_args()
    result=prepare(args) if args.operation=='prepare' else review_template(args) if args.operation=='review-template' else freeze(args) if args.operation=='freeze' else run_or_replay(args,args.operation=='replay')
    print(encoded(result).decode())


if __name__=='__main__':main()
