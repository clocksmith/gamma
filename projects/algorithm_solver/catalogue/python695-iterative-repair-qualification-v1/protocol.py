"""Separate fixed Python695 iterative variant; no historical source/run mutation."""
from dataclasses import asdict
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BATCH05=ROOT/'projects/algorithm_solver/catalogue/downloaded-batch05-independent-v1'
sys.path.insert(0,str(BATCH05))
spec=importlib.util.spec_from_file_location('repair695_existing_controller_helpers',BATCH05/'qualify.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
E=base.engine
encoded,sha,read_json,write=base.encoded,base.sha,base.read_json,base.write
SOURCE_DIR=ROOT/'projects/algorithm_solver/catalogue/authored/repair-python695-iterative-20261028-v1'
SOURCE_SHA='b04cfc350cf30124e728f3ace84114a3311f55b729f3d1a6f85bdec19bb550ec'
MANIFEST_SHA='72cdfb51c1e7fb01416172071a55a73b4458b843e72346de72bc00573b9c8731'
REVIEW_SHA='6d80496f7736256e99652818a59606391c693d75d6f5df4d3dc0c50ac571b673'
SCHEMA='gamma.python695-iterative-repair-qualification.v1'
SCOPE='Separate iterative Python695 finite development solve variant; no original variant revalidation, official wrapper or canonical adoption.'
LOADED={Path(p):sha(Path(p).read_bytes()) for p in (__file__,base.__file__,str(E.HERE/'protocol.py'),base.cases.__file__,base.oracles.__file__,E.sandbox.__file__,E.authorize_before_open.__code__.co_filename,E.bounded_regular_read.__code__.co_filename)}


def metadata():
    if sha((SOURCE_DIR/'manifest.json').read_bytes())!=MANIFEST_SHA:raise ValueError('fixed repair manifest drift')
    manifest=read_json(SOURCE_DIR/'manifest.json')
    row=manifest['source_inventory']
    if len(row)!=1 or row[0]['id']!=695 or row[0]['language']!='python' or row[0]['path']!='python/695.py' or row[0]['sha256']!=SOURCE_SHA or row[0]['semantics_path']!='semantics/695-python.json':raise ValueError('fixed repair source locator drift')
    assignment=read_json(SOURCE_DIR/'assignment.public-safe.json')
    if sha((SOURCE_DIR/'assignment.public-safe.json').read_bytes())!=manifest['assignment_sha256']:raise ValueError('repair assignment drift')
    problem=assignment['problems']
    if len(problem)!=1 or type(problem[0]['id']) is not int or problem[0]['id']!=695:raise ValueError('repair assignment identity drift')
    return manifest,row[0],problem[0]


def sourcefree_files():
    manifest,_,_=metadata()
    result={}
    for row in manifest['files']:
        if row['path'].startswith(('python/','semantics/')):continue
        path=SOURCE_DIR/row['path']
        raw=E.bounded_regular_read(path,maximum_bytes=4*1024**2)
        if sha(raw)!=row['sha256']:raise ValueError('source-free repair owner drift')
        result[str(path.relative_to(ROOT))]=sha(raw)
    return result


def generated():
    sourcefree_files()
    generator=E.load_module(SOURCE_DIR/'cases.py','repair695_independent_cases')
    crosscheck=E.load_module(SOURCE_DIR/'test_references.py','repair695_independent_dsu_crosscheck')
    rows=generator.build_cases()
    if len(rows)!=72:raise ValueError('fixed72 reference population drift')
    for row in rows:
        base.oracles.validate_generated(695,row['args'])
        if type(row['expected']) is not int or crosscheck.disjoint_set_area(row['args'][0])!=row['expected']:raise ValueError('independent DSU/reference disagreement')
    return rows


def gate(args):
    return base.gate(args)


def read_definition(args,g):
    E.access(g,695,'python','statement')
    raw=E.bounded_regular_read(args.statements/'695.json',maximum_bytes=4*1024**2)
    _,_,problem=metadata();pins=problem['statement_constraints_snapshot']
    question=read_question(raw)
    if (sha(raw)!=pins['official_snapshot_sha256'] or sha(question['content'].encode())!=pins['content_sha256']
        or sha(encoded(json.loads(question['metaData'])))!=sha(encoded(problem['external_interface']['official_metadata']))):raise ValueError('exact695 public definition/API drift')
    return sha(raw)


def read_question(raw):
    q=json.loads(raw)['data']['question']
    if not isinstance(q,dict) or q.get('questionFrontendId')!='695' or q.get('titleSlug')!='max-area-of-island' or q.get('isPaidOnly') is not False or not isinstance(q.get('content'),str) or not q['content']:raise ValueError('official695 definition identity gate')
    return q


def prepare(args):
    metadata();g=gate(args)
    E.access(g,695,'python','source');E.access(g,695,'python','statement')
    args.statements.mkdir(parents=True,exist_ok=False)
    request=urllib.request.Request('https://leetcode.com/graphql/',data=encoded({'query':base.QUERY,'variables':{'titleSlug':'max-area-of-island'}}),headers={'Content-Type':'application/json','User-Agent':'Gamma public-domain qualification'})
    with urllib.request.urlopen(request,timeout=25) as response:raw=response.read(4*1024**2+1)
    with (args.statements/'695.json').open('xb') as stream:stream.write(raw);stream.flush();E.os.fsync(stream.fileno())
    if len(raw)>4*1024**2:raise ValueError('public refetch too large; truncated response retained')
    return {'definition_sha256':read_definition(args,g),'candidate_executions':0}


def artifacts(g):
    if any(sha(path.read_bytes())!=pin for path,pin in LOADED.items()):raise ValueError('loaded owner drift; restart with reviewed files')
    result=sourcefree_files();_,row,_=metadata()
    for name,pin in ((row['path'],SOURCE_SHA),(row['semantics_path'],row['semantics_sha256'])):
        E.access(g,695,'python','source')
        raw=E.bounded_regular_read(SOURCE_DIR/name,maximum_bytes=1024**2)
        if sha(raw)!=pin:raise ValueError('exact repair source/semantics drift')
        result[str((SOURCE_DIR/name).relative_to(ROOT))]=pin
    paths=list(LOADED)+[BATCH05/'contracts.json',BATCH05/'execution-selection.json',ROOT/E.TRANSPORT/'harness.py',SOURCE_DIR/'manifest.json']
    paths+=list(HERE.glob('*.py'))+list(HERE.glob('*.md'))
    for path in paths:result[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    return result


def accept_manual_record(record,pins):
    """Explicit existing static-record serialization and source/profile acceptance."""
    _,row,problem=metadata()
    binding={'problem_id':695,'language':'python','source_sha256':SOURCE_SHA,'manifest_sha256':MANIFEST_SHA,
             'semantics_sha256':row['semantics_sha256'],'reference_sha256':pins[str((BATCH05/'oracles.py').relative_to(ROOT))],
             'case_generator_sha256':pins[str((SOURCE_DIR/'cases.py').relative_to(ROOT))],
             'definition_content_sha256':problem['statement_constraints_snapshot']['content_sha256'],
             'interface_api_sha256':sha(encoded(problem['external_interface']['official_metadata'])),
             'observer_sha256':pins[str(E.TRANSPORT/'harness.py')],'shared_effect_observer_sha256':pins[str(E.TRANSPORT/'harness.py')]}
    if type(record.get('problem_id')) is not int or any(record.get(k)!=v for k,v in binding.items()):raise ValueError('manual review exact source/API/observer binding mismatch')
    if not isinstance(record.get('reviewer'),str) or not record['reviewer'].strip() or any(record.get(flag) is not True for flag in E.REVIEW_FLAGS):raise ValueError('all7 independent mandatory review flags required')
    return {'accepted':True,'record':record,'api_serialization':'json sort_keys=True separators=(comma,colon) ensure_ascii=True allow_nan=False'}


def review(path,pins):
    if sha(Path(path).read_bytes())!=REVIEW_SHA:raise ValueError('exact independently supplied repair review required')
    return accept_manual_record(read_json(path),pins)


def freeze(args):
    runtime=E.runtime();preflight=args.preflight.read_bytes()
    if sha(preflight)!=args.preflight_sha256 or re.search(rb'\b37 passed\b',preflight) is None:raise ValueError('exact passing existing37-check Linux judge preflight required')
    g=gate(args);pins=artifacts(g);definition=read_definition(args,g);rows=generated()
    value={'schema':SCHEMA,'source_sha256':SOURCE_SHA,'manifest_sha256':MANIFEST_SHA,'artifact_hashes':pins,'runtime':runtime,
           'limits':asdict(E.LIMITS),'argv':E.ARGV['python'],'host_packet_budget':base.cases.MAX_HOST_PACKET_BYTES,
           'batch_policy':base.POLICY,'case_sha256':sha(encoded(rows)),'case_count':72,'plan':base.cases.batch_plan(rows),
           'definition_sha256':definition,'manual_review':review(args.review,pins),'review_sha256':REVIEW_SHA,
           'execution_gate_sha256':args.gate_sha256,'boundary_trusted_hashes':g['trusted_hashes'],'preflight_sha256':args.preflight_sha256,'scope':SCOPE}
    write(args.freeze,value)
    return {'freeze_sha256':sha(args.freeze.read_bytes()),'candidate_executions':0,'programs':1}


def verified(args,live):
    if sha(args.freeze.read_bytes())!=args.freeze_sha256:raise ValueError('freeze identity mismatch')
    value=read_json(args.freeze)
    if value.get('schema')!=SCHEMA or value.get('source_sha256')!=SOURCE_SHA or value.get('manifest_sha256')!=MANIFEST_SHA or value.get('limits')!=asdict(E.LIMITS) or value.get('argv')!=E.ARGV['python'] or value.get('host_packet_budget')!=base.cases.MAX_HOST_PACKET_BYTES or value.get('batch_policy')!=base.POLICY:raise ValueError('fixed repair policy drift')
    g=gate(args)
    if g['trusted_hashes']!=value['boundary_trusted_hashes']:raise ValueError('boundary anchor drift')
    if live and (args.gate_sha256!=value['execution_gate_sha256'] or E.runtime()!=value['runtime']):raise ValueError('runtime/execution-gate drift')
    if artifacts(g)!=value['artifact_hashes'] or read_definition(args,g)!=value['definition_sha256']:raise ValueError('artifact/definition drift')
    if review(args.review,value['artifact_hashes'])!=value['manual_review'] or value['review_sha256']!=REVIEW_SHA:raise ValueError('manual review drift')
    rows=generated()
    if len(rows)!=value['case_count'] or sha(encoded(rows))!=value['case_sha256'] or base.cases.batch_plan(rows)!=value['plan']:raise ValueError('independent case/plan drift')
    return value,g,rows


def run_or_replay(args,replay=False):
    value,g,rows=verified(args,not replay)
    identity={'freeze_sha256':args.freeze_sha256,'source_sha256':SOURCE_SHA,'runtime':value['runtime'],'artifact_hashes':value['artifact_hashes']}
    if not replay:
        args.output.mkdir(parents=True,exist_ok=False);write(args.output/'identity.json',identity)
    if not base.oracles.exact(read_json(args.output/'identity.json'),identity):raise ValueError('saved repair execution identity drift')
    failures=[];total=0;raw_evidence={}
    for index,indices in enumerate(value['plan']):
        wire=encoded(base.cases.packet(rows,indices));stem=args.output/f'695-python-{index:04d}'
        start={'source_sha256':SOURCE_SHA,'indices':indices,'inputs_sha256':sha(wire)}
        if not replay:
            E.access(g,695,'python','source')
            source=E.bounded_regular_read(SOURCE_DIR/'python/695.py',maximum_bytes=1024**2)
            observer=(ROOT/E.TRANSPORT/'harness.py').read_bytes()
            if sha(source)!=SOURCE_SHA or sha(observer)!=value['artifact_hashes'][str(E.TRANSPORT/'harness.py')]:raise ValueError('dispatch source/observer drift')
            write(str(stem)+'.start.json',start)
            try:result=E.sandbox.run(E.ARGV['python'],files={'program.py':source,'harness.py':observer,'inputs.json':wire},limits=E.LIMITS)
            except Exception as error:
                write(str(stem)+'.dispatch-error.json',{'exception_type':type(error).__name__,'message':str(error)[:4096],'process_result_available':False});raise
            status=asdict(result)
            for name in ('stdout','stderr'):
                raw=status.pop(name)
                with Path(str(stem)+'.'+name).open('xb') as stream:stream.write(raw);stream.flush();E.os.fsync(stream.fileno())
                status[name+'_sha256']=sha(raw);status[name+'_bytes']=len(raw)
            write(str(stem)+'.result.json',status)
        if not base.oracles.exact(read_json(str(stem)+'.start.json'),start):raise ValueError('saved batch binding drift')
        status=read_json(str(stem)+'.result.json');streams={}
        for name in ('stdout','stderr'):
            raw=E.bounded_regular_read(Path(str(stem)+'.'+name),maximum_bytes=E.LIMITS.max_output_bytes)
            if sha(raw)!=status[name+'_sha256'] or type(status[name+'_bytes']) is not int or len(raw)!=status[name+'_bytes']:raise ValueError('raw failure evidence drift')
            streams[name]=raw;raw_evidence[Path(str(stem)+'.'+name).name]=sha(raw)
        failures.extend(base.verdict(695,'python',rows,indices,status,streams['stdout']));total+=len(indices)
    complete=total==sum(map(len,value['plan'])) and total>0 and not failures
    report={'schema':SCHEMA,'freeze_sha256':args.freeze_sha256,'source_sha256':SOURCE_SHA,'case_count':len(rows),'executed_calls':total,
            'failures':failures,'qualified_finite_suite':complete,'scope':SCOPE,'canonical_admission_changed':False,'official_wrapper_execution_qualified':False}
    if replay:
        if not base.oracles.exact(read_json(args.output/'report.json'),report):raise ValueError('saved repair report mismatch')
        write(args.output/'replay.json',{'schema':SCHEMA,'freeze_sha256':args.freeze_sha256,'source_sha256':SOURCE_SHA,'report_sha256':sha((args.output/'report.json').read_bytes()),'raw_stream_hashes':raw_evidence,'replay_gate_sha256':args.gate_sha256,'original_execution_gate_sha256':value['execution_gate_sha256'],'candidate_execution_on_replay_host':False,'all_observations_match_report':True})
    else:write(args.output/'report.json',report)
    return {'programs':1,'executed_calls':total,'qualified_finite_suite':complete,'replayed':replay,'candidate_execution_on_replay_host':False if replay else None}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('prepare','freeze','run','replay'))
    for name in ('gate','statements','freeze','preflight','review','output'):parser.add_argument('--'+name,type=Path)
    for name in ('gate-sha256','freeze-sha256','preflight-sha256'):parser.add_argument('--'+name)
    args=parser.parse_args();result=prepare(args) if args.operation=='prepare' else freeze(args) if args.operation=='freeze' else run_or_replay(args,args.operation=='replay')
    print(encoded(result).decode())


if __name__=='__main__':main()
