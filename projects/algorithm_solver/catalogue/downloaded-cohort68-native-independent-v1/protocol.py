"""Frozen named/class native adapter execution with measured observation counts."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

import cases
from cases import o
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'projects/algorithm_solver'))
from algsolve.judge import sandbox
assert Path(sandbox.__file__).resolve()==(ROOT/'projects/algorithm_solver/algsolve/judge/sandbox.py').resolve()
ORIGINAL=Path('projects/algorithm_solver/catalogue/authored/downloaded-general68-v1')
ROOT_LANE=Path('projects/algorithm_solver/catalogue/downloaded-remaining-qualification-v1')
TRANSPORT=Path('projects/algorithm_solver/catalogue/public-domain-qualification-easy16-v1')
LIMITS=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=16*1024**2)
ARGV={'python':['/usr/bin/python3','-I','-S','harness.py'],
      'javascript':['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=256','harness.cjs']}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())

def runtime():
    refs = {}
    for name in ('python3', 'node', 'bwrap', 'prlimit'):
        path = Path('/usr/bin') / name
        refs[str(path)] = sha(path.read_bytes())
        proc = subprocess.run(['/usr/bin/ldd', str(path)], capture_output=True, text=True, check=True)
        for dep in re.findall(r'(?:=>\s*)?(/[^\s()]+)', proc.stdout):
            refs[dep] = sha(Path(dep).read_bytes())
    lib = Path(subprocess.check_output(['/usr/bin/python3', '-I', '-S', '-c',
                'import sysconfig;print(sysconfig.get_path("stdlib"))'], text=True).strip())
    standard = {str(p.relative_to(lib)): sha(p.read_bytes()) for p in sorted(lib.rglob('*'))
                if p.is_file() and p.suffix in ('.py', '.so') and
                'site-packages' not in p.parts and '__pycache__' not in p.parts}
    return {'executables_and_linked_libraries': refs, 'python_stdlib_path': str(lib),
            'python_stdlib_files': standard,
            'python_version': subprocess.check_output(['/usr/bin/python3', '--version'], text=True).strip(),
            'node_version': subprocess.check_output(['/usr/bin/node', '--version'], text=True).strip()}

def parse(raw, count):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate observation key')
            result[key] = value
        return result
    rows = [json.loads(line, object_pairs_hook=pairs,
                       parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            for line in raw.decode('utf8').splitlines()]
    if len(rows) != count + 1 or rows[-1] != {'done': count}:
        raise ValueError('incomplete observation stream')
    for i, row in enumerate(rows[:-1]):
        if not isinstance(row, dict) or type(row.get('i')) is not int or row['i'] != i:
            raise ValueError('observation order mismatch')
        required = {'i', 'error'} if 'error' in row else {
            'i', 'result', 'result_type', 'args_before', 'args_after', 'alias_edges'}
        if set(row) != required:
            raise ValueError('observation shape mismatch')
    return rows[:-1]


@lru_cache(None)
def selection():
    rows=json.loads((HERE/'sources.json').read_bytes())['source_inventory']
    assert len(rows)==136
    selected={(r['problem_id'],r['language']):r for r in rows};assert len(selected)==136
    for row in rows:
        assert sha((ROOT/row['selected_source_path']).read_bytes())==row['selected_source_sha256']
        assert sha((ROOT/row['original_source_path']).read_bytes())==row['original_source_sha256']
    reviews=json.loads((HERE/'independent-review.json').read_bytes())
    changed={(r['problem_id'],r['language']):r['reviewed_source_sha256'] for r in reviews['native_reviews']+reviews['mandatory_repair_reviews']}
    assert len(changed)==19
    for key,row in selected.items():
        if row['selected_kind']!='original':assert changed[key]==row['selected_source_sha256']
    return selected


@lru_cache(None)
def contracts():
    rows=json.loads((HERE/'contracts.json').read_bytes())['problems']
    result={r['id']:r for r in rows};assert len(result)==68
    for pid,row in result.items():
        assert (row['official_metadata']['return']['type']=='void')==(pid in cases.NATIVE)
    return result


def units():
    result=[]
    for pid in cases.IDS:
        for language in ('python','javascript'):
            result.append({'id':f'{pid}-{language}-class-selected','problem_id':pid,'language':language,
                           'mode':'native_void' if pid in cases.NATIVE else 'native_value',
                           'source_kind':'selected','negative_control':False,'entry_form':'class'})
    for pid in cases.NATIVE:
        result.append({'id':f'{pid}-javascript-named-selected','problem_id':pid,'language':'javascript',
                       'mode':'native_void','source_kind':'selected','negative_control':False,'entry_form':'named'})
        for language in ('python','javascript'):
            result.append({'id':f'{pid}-{language}-free-selected','problem_id':pid,'language':language,
                           'mode':'free_solve','source_kind':'selected','negative_control':False,'entry_form':'free'})
            result.append({'id':f'{pid}-{language}-native-original-control','problem_id':pid,'language':language,
                           'mode':'native_void','source_kind':'original','negative_control':True,'entry_form':'class' if language=='python' else 'named'})
    assert len(result)==161
    return result


def adapter(unit):
    if unit['mode']=='free_solve':return b''
    method=selection()[(unit['problem_id'],unit['language'])]['method']
    assert re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',method)
    if unit['language']=='python':
        call=f"getattr(Solution(), {method!r})(*args)"
        if unit['mode']=='native_void':
            text=f"\n\ndef gamma_entry(*args):\n    value = {call}\n    return {{'observed_return_kind': 'void' if value is None else type(value).__name__}}\n"
        else:text=f"\n\ndef gamma_entry(*args):\n    return {call}\n"
    else:
        call=method+'(...args)' if unit['entry_form']=='named' else 'new Solution()['+json.dumps(method)+'](...args)'
        if unit['mode']=='native_void':
            text='\nfunction gamma_entry(...args) { const value = '+call+"; return {observed_return_kind: value === undefined ? 'void' : value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value}; }\n"
        else:text='\nfunction gamma_entry(...args) { return '+call+'; }\n'
    return text.encode()


def source(unit):
    row=selection()[(unit['problem_id'],unit['language'])]
    prefix='selected' if unit['source_kind']=='selected' else 'original'
    raw=(ROOT/row[prefix+'_source_path']).read_bytes()
    assert sha(raw)==row[prefix+'_source_sha256']
    return raw+adapter(unit)


def artifacts():
    paths=list(HERE.glob('*.py'))+[HERE/n for n in ('README.md','sources.json','contracts.json','independent-review.json')]
    paths+=list((HERE/'references').rglob('*.py'))+list((HERE/'references').rglob('*.json'))
    paths+=[ROOT/TRANSPORT/'harness.cjs',ROOT/'projects/algorithm_solver/algsolve/judge/sandbox.py',
            ROOT/ORIGINAL/'manifest.json',ROOT/ORIGINAL/'assignment.public-safe.json',
            ROOT/ROOT_LANE/'cohort68-repairs/manifest.json',ROOT/ROOT_LANE/'cohort68-native-repairs-v2/manifest.json']
    for row in selection().values():paths.extend([ROOT/row['selected_source_path'],ROOT/row['original_source_path']])
    return {str(path.relative_to(ROOT)):sha(path.read_bytes()) for path in sorted(set(paths))}


def load_cases(statements,pins):
    assert len(pins)==68 and {p['id'] for p in pins}==set(cases.IDS)
    for pin in pins:
        raw=(Path(statements)/f"{pin['id']}.json").read_bytes();q=json.loads(raw)['data']['question']
        assert (sha(raw)==pin['snapshot_sha256'] and sha(q['content'].encode())==pin['content_sha256']
                and sha(q['metaData'].encode())==pin['metadata_sha256']
                and q['questionFrontendId']==str(pin['id']) and q['titleSlug']==pin['slug'])
    return cases.build(statements)


def batches(values):
    batch=[];size=0
    for index,case in enumerate(values):
        length=len(encoded(case['args']))
        if case.get('isolate'):
            if batch:yield batch+[batch[0]]
            yield [index,index];batch=[];size=0;continue
        if batch and (len(batch)>=32 or size+length>256*1024):yield batch+[batch[0]];batch=[];size=0
        batch.append(index);size+=length
    if batch:yield batch+[batch[0]]


def native_effect(case,record,language,pid):
    if 'error'in record:return False,False,'candidate_error'
    expected_type='dict' if language=='python' else 'object'
    result=record.get('result')
    if (record.get('result_type')!=expected_type or type(result)is not dict
            or set(result)!={'observed_return_kind'} or type(result['observed_return_kind'])is not str):
        return False,False,'native_diagnostic_protocol'
    void=result['observed_return_kind']=='void'
    if not o.exact(record.get('args_before'),case['args']):return False,void,'before_args'
    if not cases.post_matches(pid,case['args'],record.get('args_after'),case['expected']):return False,void,'native_argument_effect'
    if record.get('alias_edges')!=[]:return False,void,'native_argument_alias'
    return True,void,None


def complete_rows(raw,count):
    """Count complete captured observations, even when the interpreter was killed."""
    rows=[];done=[];invalid=[]
    def unique(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate field')
            result[key]=value
        return result
    for i,line in enumerate(raw.splitlines()):
        try:row=json.loads(line,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
        except (ValueError,UnicodeError):invalid.append(i);continue
        if type(row)is dict and set(row)=={'done'} and type(row['done'])is int:done.append(row['done']);continue
        required={'i','error'} if type(row)is dict and 'error'in row else {'i','result','result_type','args_before','args_after','alias_edges'}
        if type(row)is dict and set(row)==required and type(row.get('i'))is int and row['i']==len(rows) and len(rows)<count:rows.append(row)
        else:invalid.append(i)
    return rows,not invalid and len(rows)==count and done==[count],invalid


def evaluate(unit,values,indices,metadata,stdout):
    rows,protocol_complete,invalid=complete_rows(stdout,len(indices))
    process_ok=metadata['exit_code']==0 and not metadata['timed_out'] and not metadata['output_limit_exceeded']
    counts={'requested_call_slots':len(indices),'complete_observation_rows':len(rows),'normal_result_rows':sum('result'in r for r in rows),
            'candidate_error_rows':sum('error'in r for r in rows),'successful_process_exits':int(process_ok),
            'successful_complete_streams':int(process_ok and protocol_complete),'requested_interpreter_streams':1,
            'effect_conforming_rows':0,'void_return_rows':0,'nontrivial_mutation_rows':0,'nontrivial_mutation_rejections':0,'degenerate_effect_conforming_rows':0}
    failures=[]
    for index,record in zip(indices,rows):
        case=values[index]
        if unit['mode']=='native_void':
            ok,void,reason=native_effect(case,record,unit['language'],unit['problem_id'])
            counts['void_return_rows']+=int(void)
            nontrivial=case['requires_native_effect_change'];counts['nontrivial_mutation_rows']+=int(nontrivial)
            if nontrivial and not ok:counts['nontrivial_mutation_rejections']+=1
            if not nontrivial and ok:counts['degenerate_effect_conforming_rows']+=1
            # The official effect adapter ignores return values. Selected repaired modules
            # additionally promise None/undefined; record/check that claim independently.
            if ok and not void and not unit['negative_control']:reason='declared_void_not_observed'
        else:
            ok,reason=o.compare(unit['problem_id'],case['args'],case['expected'],record,unit['language']);void=False
        counts['effect_conforming_rows']+=int(ok)
        if not ok or (unit['mode']=='native_void' and not void and not unit['negative_control']):
            failures.append({'case':index,'reason':reason})
    if not process_ok or not protocol_complete:
        failures.append({'batch_failure':'sandbox_process_failure' if not process_ok else 'observation_protocol',
                         'requested_slots':len(indices),'complete_rows':len(rows),'invalid_or_partial_lines':invalid})
    return counts,failures


def summarize(unit,values,counts,failures):
    success=counts['successful_complete_streams']==counts['requested_interpreter_streams']
    if unit['negative_control']:
        expected=sum(values[i]['requires_native_effect_change'] for batch in batches(values) for i in batch)
        passed=(success and expected>0 and counts['nontrivial_mutation_rows']==expected
                and counts['nontrivial_mutation_rejections']==expected)
    else:passed=success and not failures and counts['complete_observation_rows']==counts['requested_call_slots']
    row=selection()[(unit['problem_id'],unit['language'])];prefix='selected' if unit['source_kind']=='selected' else 'original'
    return dict(unit,case_count=len(values),counts=counts,failures=failures,passed=passed,
                source_path=row[prefix+'_source_path'],source_sha256=row[prefix+'_source_sha256'],
                native_interface='solve' if unit['mode']=='free_solve' else row['method'] if unit['entry_form']=='named' else 'Solution.'+row['method'],
                return_policy='ignored for effect correctness; selected void promise separately checked' if unit['mode']=='native_void' else 'typed value result',
                production_service_verified=False,canonical_promotion=False)


def summarize_report(rows,freeze_sha):
    selected=[r for r in rows if r['source_kind']=='selected' and r['mode']!='free_solve' and r['entry_form']=='class']
    named=[r for r in rows if r['source_kind']=='selected' and r['entry_form']=='named']
    free=[r for r in rows if r['mode']=='free_solve'];controls=[r for r in rows if r['negative_control']]
    totals={key:sum(r['counts'][key] for r in rows) for key in rows[0]['counts']}
    return {'schema':'gamma.cohort68-native-named-class-execution-report.v2','freeze_sha256':freeze_sha,'units':rows,
            'selected_official_js_named_interfaces':len(named),'selected_official_js_named_interfaces_passed':sum(r['passed'] for r in named),
            'selected_class_interfaces':len(selected),'selected_class_interfaces_passed':sum(r['passed'] for r in selected),
            'new_module_free_solve_interfaces':len(free),'new_module_free_solve_passed':sum(r['passed'] for r in free),
            'original_native_controls':len(controls),'original_native_controls_successfully_discriminated':sum(r['passed'] for r in controls),
            'all_execution_units_passed':all(r['passed'] for r in rows),'totals':totals,
            'production_service_verified':False,'canonical_promotions':0,'root_review_required':True}


def freeze(args):
    pins=json.loads(args.pins.read_bytes());values=load_cases(args.statements,pins)
    contract={'schema':'gamma.cohort68-native-independent-freeze.v1','created_at':datetime.now(timezone.utc).isoformat(),
              'artifact_hashes':artifacts(),'runtime':runtime(),'limits':asdict(LIMITS),'argv':ARGV,
              'statement_pins':pins,'cases_sha256':sha(encoded(values)),
              'case_counts':{str(pid):len(rows) for pid,rows in values.items()},
              'batch_plan':{str(pid):list(batches(rows)) for pid,rows in values.items()},
              'units':units(),'interface_contracts':contracts(),'adapter_sha256':{u['id']:sha(adapter(u)) for u in units()},
              'host':platform.node(),'judge_preflight_sha256':sha(args.preflight.read_bytes()),
              'sandbox_loaded_from':str(Path(sandbox.__file__).resolve()),
              'scope':'Python Solution methods, JavaScript class compatibility plus actual official named entries for five native mutators, and free-solve evidence; no production service admission',
              'call_entry_events_instrumented':False}
    assert '37 passed' in args.preflight.read_text()
    write(args.freeze,contract);print('FROZEN',sha(args.freeze.read_bytes()),flush=True)


def run(args):
    raw=args.freeze.read_bytes();assert sha(raw)==args.freeze_sha256;contract=json.loads(raw)
    assert artifacts()==contract['artifact_hashes'] and runtime()==contract['runtime']
    assert str(Path(sandbox.__file__).resolve())==contract['sandbox_loaded_from']
    assert asdict(LIMITS)==contract['limits'] and ARGV==contract['argv'] and units()==contract['units']
    values=load_cases(args.statements,contract['statement_pins']);assert sha(encoded(values))==contract['cases_sha256']
    args.output.mkdir(parents=True,exist_ok=False)
    write(args.output/'run-identity.json',{'freeze_sha256':sha(raw),'artifact_hashes':artifacts(),'host':platform.node(),'started_at':datetime.now(timezone.utc).isoformat()})
    summaries=[]
    for unit in units():
        pid,language=unit['problem_id'],unit['language'];counts={};failures=[]
        for number,indices in enumerate(contract['batch_plan'][str(pid)]):
            entry='solve' if unit['mode']=='free_solve' else 'gamma_entry'
            packet={'entry':entry,'calls':[{'args':values[pid][i]['args']} for i in indices]};program=source(unit);stem=unit['id']+f'-{number:03d}'
            write(args.output/(stem+'.start.json'),{'unit':unit,'indices':indices,'inputs_sha256':sha(encoded(packet)),
                                                  'program_packet_sha256':sha(program),'adapter_sha256':sha(adapter(unit))})
            extension,harness=('py','harness.py') if language=='python' else ('js','harness.cjs')
            helper=(HERE/'harness.py').read_bytes() if language=='python' else (ROOT/TRANSPORT/'harness.cjs').read_bytes()
            try:result=sandbox.run(ARGV[language],files={'program.'+extension:program,harness:helper,'inputs.json':encoded(packet)},limits=LIMITS)
            except Exception as error:
                write(args.output/'infrastructure-failure.json',{'unit':unit,'batch':number,'error_type':type(error).__name__,'error':str(error)[:2000]});raise
            metadata=asdict(result)
            for stream in ('stdout','stderr'):
                payload=metadata.pop(stream);(args.output/(stem+'.'+stream)).write_bytes(payload);metadata[stream+'_sha256']=sha(payload)
            write(args.output/(stem+'.result.json'),metadata)
            observed,rejected=evaluate(unit,values[pid],indices,metadata,result.stdout)
            for key,value in observed.items():counts[key]=counts.get(key,0)+value
            failures+=rejected
        row=summarize(unit,values[pid],counts,failures);summaries.append(row);write(args.output/(unit['id']+'.summary.json'),row)
        print(json.dumps({'unit':unit['id'],'passed':row['passed'],'requested_slots':counts['requested_call_slots'],
                          'complete_rows':counts['complete_observation_rows'],'complete_streams':counts['successful_complete_streams'],
                          'nontrivial_mutation_rejections':counts['nontrivial_mutation_rejections'],
                          'degenerate_effect_conforming':counts['degenerate_effect_conforming_rows']}),flush=True)
    write(args.output/'report.json',summarize_report(summaries,sha(raw)))


def replay(args):
    raw=args.freeze.read_bytes();contract=json.loads(raw);assert artifacts()==contract['artifact_hashes']
    identity=json.loads((args.output/'run-identity.json').read_bytes());assert identity['freeze_sha256']==sha(raw) and identity['artifact_hashes']==contract['artifact_hashes']
    values=load_cases(args.statements,contract['statement_pins']);assert sha(encoded(values))==contract['cases_sha256'];summaries=[]
    for unit in contract['units']:
        pid=unit['problem_id'];counts={};failures=[]
        for number,indices in enumerate(contract['batch_plan'][str(pid)]):
            stem=unit['id']+f'-{number:03d}';packet={'entry':'solve' if unit['mode']=='free_solve' else 'gamma_entry','calls':[{'args':values[pid][i]['args']} for i in indices]}
            assert json.loads((args.output/(stem+'.start.json')).read_bytes())=={'unit':unit,'indices':indices,'inputs_sha256':sha(encoded(packet)),
                    'program_packet_sha256':sha(source(unit)),'adapter_sha256':sha(adapter(unit))}
            metadata=json.loads((args.output/(stem+'.result.json')).read_bytes())
            for stream in ('stdout','stderr'):assert sha((args.output/(stem+'.'+stream)).read_bytes())==metadata[stream+'_sha256']
            observed,rejected=evaluate(unit,values[pid],indices,metadata,(args.output/(stem+'.stdout')).read_bytes())
            for key,value in observed.items():counts[key]=counts.get(key,0)+value
            failures+=rejected
        row=summarize(unit,values[pid],counts,failures);assert json.loads((args.output/(unit['id']+'.summary.json')).read_bytes())==row;summaries.append(row)
    expected=summarize_report(summaries,sha(raw));assert json.loads((args.output/'report.json').read_bytes())==expected
    return {'schema':'gamma.cohort68-native-independent-raw-replay.v1','freeze_sha256':sha(raw),
            'execution_units_replayed':len(summaries),'totals':expected['totals'],'all_execution_units_passed':expected['all_execution_units_passed'],
            'selected_class_interfaces_passed':expected['selected_class_interfaces_passed'],
            'selected_official_js_named_interfaces_passed':expected['selected_official_js_named_interfaces_passed'],
            'new_module_free_solve_passed':expected['new_module_free_solve_passed'],
            'original_controls_discriminated':expected['original_native_controls_successfully_discriminated'],
            'raw_artifact_hashes':{p.name:sha(p.read_bytes()) for p in sorted(args.output.iterdir()) if p.is_file() and p.name!='replay.json'},
            'production_service_verified':False,'canonical_promotions':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=('freeze','run','replay'))
    for name in ('statements','freeze'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('pins','preflight','output'):parser.add_argument('--'+name,type=Path)
    parser.add_argument('--freeze-sha256');args=parser.parse_args()
    if args.operation=='freeze':freeze(args)
    elif args.operation=='run':run(args)
    else:
        result=replay(args);write(args.output/'replay.json',result);print(json.dumps({k:v for k,v in result.items() if k!='raw_artifact_hashes'}))
