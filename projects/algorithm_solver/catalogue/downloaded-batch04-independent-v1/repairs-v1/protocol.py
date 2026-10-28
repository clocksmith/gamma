"""Freeze, execute and replay distinct repaired identities; preserve original baseline."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
import cases
import oracles as o
import qualify as original

ROOT = original.ROOT
LIMITS = original.LIMITS
ARGV = original.ARGV
encoded, sha, write = original.encoded, original.sha, original.write
SELECTED = (406, 418, 433, 442, 443, 502)


def inventory():
    data = json.loads((HERE/'sources.json').read_bytes())
    assert len(data['source_inventory']) == 12
    result = {}
    for row in data['source_inventory']:
        pid, language = row['problem_id'], row['language']
        assert pid in SELECTED and language in ('python','javascript')
        assert sha((BASE/row['source_path']).read_bytes()) == row['source_sha256']
        assert sha((ROOT/row['original_path']).read_bytes()) == row['original_sha256']
        result[(pid,language)] = row
    assert len(result) == 12
    return result


def artifacts():
    result = original.artifacts()
    result[str((BASE/'frozen-contract.json').relative_to(ROOT))] = sha((BASE/'frozen-contract.json').read_bytes())
    paths = [HERE/name for name in ('protocol.py','harness.py','native443.py','native443.js',
                                    'README.md','sources.json','test_contract.py')]
    paths += [BASE/row['source_path'] for row in inventory().values()]
    result.update({str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in paths})
    return dict(sorted(result.items()))


def units():
    result = []
    for pid in SELECTED:
        for language in ('python','javascript'):
            result.append({'id':f'{pid}-{language}-solve','problem_id':pid,'language':language,
                           'mode':'solve','source_kind':'repaired','negative_control':False})
    for language in ('python','javascript'):
        for source_kind in ('repaired','original'):
            result.append({'id':f'443-{language}-native-{source_kind}','problem_id':443,'language':language,
                           'mode':'native443','source_kind':source_kind,'negative_control':source_kind=='original'})
    return result


def data(statements, pins):
    all_cases = original.load_cases(statements,pins)
    return {pid:all_cases[pid] for pid in SELECTED}


def native_compare(args,want,record,language):
    if 'error' in record: return False,'candidate_error'
    if record.get('result_type') != ('dict' if language=='python' else 'object'):
        return False,'native_result_type'
    result = record.get('result')
    if (type(result) is not dict or set(result) != {'length','prefix'}
            or type(result['length']) is not int or result['length'] != len(want)
            or not o.exact(result['prefix'],want)):
        return False,'native_result_value'
    if not o.exact(record.get('args_before'),args): return False,'native_before_args'
    after = record.get('args_after')
    if (type(after) is not list or len(after) != 1 or type(after[0]) is not list
            or len(after[0]) < len(want) or not o.exact(after[0][:len(want)],want)
            or not all(type(c) is str and len(c)==1 for c in after[0])):
        return False,'native_prefix_mutation'
    if not o.exact(record.get('alias_edges'),[]): return False,'native_return_alias'
    return True,None


def compare(unit,case,record):
    if unit['mode'] == 'native443':
        return native_compare(case['args'],case['expected'],record,unit['language'])
    return o.compare(unit['problem_id'],case['args'],case['expected'],record,unit['language'])


def observations(unit,values,indices,metadata,stdout):
    if not (metadata['exit_code']==0 and not metadata['timed_out'] and not metadata['output_limit_exceeded']):
        return [{'case':i,'reason':'sandbox_process_failure'} for i in indices],0
    try: records=original.parse(stdout,len(indices))
    except (ValueError,UnicodeError,TypeError):
        return [{'case':i,'reason':'observation_protocol'} for i in indices],0
    failures=[];conforming=0
    for index,record in zip(indices,records):
        ok,reason=compare(unit,values[index],record)
        conforming+=int(ok)
        if not ok: failures.append({'case':index,'reason':reason})
    return failures,conforming


def source_packet(unit):
    row=inventory()[(unit['problem_id'],unit['language'])]
    path=(BASE/row['source_path']) if unit['source_kind']=='repaired' else ROOT/row['original_path']
    payload=path.read_bytes()
    if unit['mode']=='native443':
        extension='py' if unit['language']=='python' else 'js'
        payload+=b'\n\n'+(HERE/f'native443.{extension}').read_bytes()
    return payload


def summarize(unit,values,total,failures,conforming):
    negative=unit['negative_control']
    # A negative control passes only when every parsed call was rejected, without process/protocol failure.
    control_ok=negative and conforming==0 and len(failures)==total and all(f['reason'] not in ('sandbox_process_failure','observation_protocol') for f in failures)
    return dict(unit,generated_cases=len(values),executed_calls=total,conforming_calls=conforming,
                failures=failures,passed=control_ok if negative else not failures,
                definition_failure=o.DEFINITION_FAILURES.get(unit['problem_id']),
                source_sha256=inventory()[(unit['problem_id'],unit['language'])]['source_sha256' if unit['source_kind']=='repaired' else 'original_sha256'],
                input_effect_contract='temporarily mutable, restored on return; exclusive access' if unit['problem_id']==442 else 'native prefix mutation' if unit['mode']=='native443' else 'unchanged on return; fresh mutable output')


def report(rows,freeze_sha):
    native={r['language']:r['passed'] for r in rows if r['mode']=='native443' and not r['negative_control']}
    selected=[]
    for row in rows:
        if row['mode'] != 'solve': continue
        selected.append({'problem_id':row['problem_id'],'language':row['language'],
                         'source_sha256':row['source_sha256'],'functional_tests_passed':row['passed'],
                         'definition_failure':row['definition_failure'],
                         'native443_tests_passed':native.get(row['language']) if row['problem_id']==443 else None,
                         'qualified':row['passed'] and row['definition_failure'] is None and (row['problem_id']!=443 or native[row['language']])})
    return {'freeze_sha256':freeze_sha,'units':rows,'repaired_sources':selected,
            'source_slots_qualified':sum(r['qualified'] for r in selected),
            'all_execution_units_passed':all(r['passed'] for r in rows),
            'canonical_admission_changed':False,'original_sources_modified':False}


def freeze(args):
    pins=json.loads(args.pins.read_bytes());values=data(args.statements,pins)
    contract={'schema':'gamma.batch04-repaired-source-freeze.v1','created_at':datetime.now(timezone.utc).isoformat(),
              'artifact_hashes':artifacts(),'runtime':original.runtime(),'argv':ARGV,'limits':asdict(LIMITS),
              'statement_pins':pins,'cases_sha256':sha(encoded(values)),
              'batch_plan':{str(pid):list(original.batches(cases)) for pid,cases in values.items()},
              'source_inventory':list(inventory().values()),'units':units(),
              'baseline_freeze_sha256':sha((BASE/'frozen-contract.json').read_bytes()),
              'host':platform.node(),'judge_preflight_sha256':sha(args.preflight.read_bytes())}
    assert '37 passed' in args.preflight.read_text()
    write(args.freeze,contract);print('FROZEN',sha(args.freeze.read_bytes()),flush=True)


def execute(args):
    raw=args.freeze.read_bytes();assert sha(raw)==args.freeze_sha256;contract=json.loads(raw)
    assert artifacts()==contract['artifact_hashes'] and original.runtime()==contract['runtime']
    assert asdict(LIMITS)==contract['limits'] and ARGV==contract['argv'] and units()==contract['units']
    values=data(args.statements,contract['statement_pins']);assert sha(encoded(values))==contract['cases_sha256']
    args.output.mkdir(parents=True,exist_ok=False)
    write(args.output/'run-identity.json',{'freeze_sha256':sha(raw),'artifact_hashes':artifacts(),'started_at':datetime.now(timezone.utc).isoformat(),'host':platform.node()})
    summaries=[]
    for unit in units():
        pid,language=unit['problem_id'],unit['language'];total=conforming=0;failures=[]
        for batch,indices in enumerate(contract['batch_plan'][str(pid)]):
            packet={'entry':'gamma_native443' if unit['mode']=='native443' else 'solve','calls':[{'args':values[pid][i]['args']} for i in indices]}
            program=source_packet(unit);stem=unit['id']+f'-{batch:03d}'
            write(args.output/(stem+'.start.json'),{'unit':unit,'indices':indices,'inputs_sha256':sha(encoded(packet)),'program_packet_sha256':sha(program)})
            extension,harness=('py','harness.py') if language=='python' else ('js','harness.cjs')
            transport=(HERE/'harness.py').read_bytes() if language=='python' else (ROOT/original.TRANSPORT/'harness.cjs').read_bytes()
            result=original.sandbox.run(ARGV[language],files={'program.'+extension:program,harness:transport,'inputs.json':encoded(packet)},limits=LIMITS)
            metadata=asdict(result)
            for stream in ('stdout','stderr'):
                payload=metadata.pop(stream);(args.output/(stem+'.'+stream)).write_bytes(payload);metadata[stream+'_sha256']=sha(payload)
            write(args.output/(stem+'.result.json'),metadata)
            rejected,accepted=observations(unit,values[pid],indices,metadata,result.stdout)
            failures+=rejected;conforming+=accepted;total+=len(indices)
        summary=summarize(unit,values[pid],total,failures,conforming);summaries.append(summary)
        write(args.output/(unit['id']+'.summary.json'),summary)
        print(json.dumps({k:v for k,v in summary.items() if k!='failures'}),flush=True)
    write(args.output/'report.json',report(summaries,sha(raw)))


def replay(args):
    raw=args.freeze.read_bytes();contract=json.loads(raw)
    assert artifacts()==contract['artifact_hashes']
    identity=json.loads((args.output/'run-identity.json').read_bytes())
    assert identity['freeze_sha256']==sha(raw) and identity['artifact_hashes']==contract['artifact_hashes']
    values=data(args.statements,contract['statement_pins']);assert sha(encoded(values))==contract['cases_sha256']
    summaries=[];count=0
    for unit in contract['units']:
        pid=unit['problem_id'];total=conforming=0;failures=[]
        for batch,indices in enumerate(contract['batch_plan'][str(pid)]):
            stem=unit['id']+f'-{batch:03d}';packet={'entry':'gamma_native443' if unit['mode']=='native443' else 'solve','calls':[{'args':values[pid][i]['args']} for i in indices]}
            assert json.loads((args.output/(stem+'.start.json')).read_bytes())=={'unit':unit,'indices':indices,'inputs_sha256':sha(encoded(packet)),'program_packet_sha256':sha(source_packet(unit))}
            metadata=json.loads((args.output/(stem+'.result.json')).read_bytes())
            for stream in ('stdout','stderr'): assert sha((args.output/(stem+'.'+stream)).read_bytes())==metadata[stream+'_sha256']
            rejected,accepted=observations(unit,values[pid],indices,metadata,(args.output/(stem+'.stdout')).read_bytes())
            failures+=rejected;conforming+=accepted;total+=len(indices);count+=1
        summary=summarize(unit,values[pid],total,failures,conforming)
        assert json.loads((args.output/(unit['id']+'.summary.json')).read_bytes())==summary;summaries.append(summary)
    expected=report(summaries,sha(raw));assert json.loads((args.output/'report.json').read_bytes())==expected
    result={'schema':'gamma.batch04-repair-raw-replay.v1','freeze_sha256':sha(raw),'execution_units_replayed':len(summaries),
            'sandbox_batches_replayed':count,'calls_replayed':sum(r['executed_calls'] for r in summaries),
            'all_execution_units_passed':expected['all_execution_units_passed'],'source_slots_qualified':expected['source_slots_qualified'],
            'raw_artifact_hashes':{p.name:sha(p.read_bytes()) for p in sorted(args.output.iterdir()) if p.is_file() and p.name!='replay.json'},
            'canonical_admission_changed':False}
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=('freeze','run','replay'))
    for name in ('statements','freeze'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('pins','preflight','output'):parser.add_argument('--'+name,type=Path)
    parser.add_argument('--freeze-sha256');args=parser.parse_args()
    if args.operation=='freeze':freeze(args)
    elif args.operation=='run':execute(args)
    else:
        result=replay(args);write(args.output/'replay.json',result)
        print(json.dumps({k:v for k,v in result.items() if k!='raw_artifact_hashes'}))
