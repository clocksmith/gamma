"""Official named JS443 execution; old class-only source remains immutable."""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import json
from pathlib import Path
import platform
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
import qualify as q
import oracles as o
ROOT=q.ROOT
sha,encoded,write=q.sha,q.encoded,q.write
LIMITS,ARGV=q.LIMITS,q.ARGV
assert Path(q.sandbox.__file__).resolve()==(ROOT/'projects/algorithm_solver/algsolve/judge/sandbox.py').resolve()


def inventory():
    j=json.loads((HERE/'source.json').read_bytes())
    for prefix in ('source','prior_class_only_source'):
        assert sha((ROOT/j[prefix+'_path']).read_bytes())==j[prefix+'_sha256']
    return j


def units():
    return [{'id':'new-named','source_kind':'new','entry_form':'named','negative_control':False},
            {'id':'old-named-control','source_kind':'old','entry_form':'named','negative_control':True},
            {'id':'new-class-compatibility','source_kind':'new','entry_form':'class','negative_control':False},
            {'id':'new-free-solve','source_kind':'new','entry_form':'free','negative_control':False}]


def adapter(unit):
    if unit['entry_form']=='free':return b''
    call='compress(chars)' if unit['entry_form']=='named' else 'new Solution().compress(chars)'
    return ('\nfunction gamma_entry(chars) { const length = '+call+'; if (!Number.isInteger(length)) return {bad_length_type: typeof length}; return {length, prefix: chars.slice(0,length)}; }\n').encode()


def source(unit):
    j=inventory();prefix='source' if unit['source_kind']=='new' else 'prior_class_only_source'
    return (ROOT/j[prefix+'_path']).read_bytes()+adapter(unit)


def artifacts():
    result=q.artifacts()
    j=inventory();paths=[HERE/name for name in ('protocol.py','test_contract.py','README.md','source.json','443.js','443-starter.json','starter-pin.json')]
    paths+=[ROOT/j['prior_class_only_source_path']]
    result.update({str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in paths});return dict(sorted(result.items()))


def values(statements,pins):
    pin=json.loads((HERE/'starter-pin.json').read_bytes());raw=(HERE/'443-starter.json').read_bytes();question=json.loads(raw)['data']['question']
    assert sha(raw)==pin['snapshot_sha256'] and question['questionFrontendId']=='443'
    snippets={r['langSlug']:r['code'] for r in question['codeSnippets']}
    assert sha(snippets['javascript'].encode())==pin['javascript_starter_sha256'] and 'var compress = function' in snippets['javascript']
    meta=json.loads(question['metaData']);assert meta['name']=='compress' and meta['return']['type']=='integer' and meta['output']=={'paramindex':0,'size':'ret'}
    return q.load_cases(statements,pins)[443]


def compare(unit,case,row):
    if unit['entry_form']=='free':return o.compare(443,case['args'],case['expected'],row,'javascript')
    if 'error'in row:return False,'candidate_error'
    result=row.get('result');want=case['expected'];post=row.get('args_after')
    if row.get('result_type')!='object' or type(result)is not dict or set(result)!={'length','prefix'} or type(result['length'])is not int or result['length']!=len(want) or not o.exact(result['prefix'],want):return False,'native_length_or_prefix_result'
    if not o.exact(row.get('args_before'),case['args']):return False,'before_args'
    if type(post)is not list or len(post)!=1 or type(post[0])is not list or len(post[0])<len(want) or not o.exact(post[0][:len(want)],want):return False,'native_prefix_effect'
    if row.get('alias_edges')!=[]:return False,'return_alias'
    return True,None


def observed(raw,count):
    # Count complete valid-prefix observation rows independently from planned slots.
    rows=[]
    for line in raw.splitlines():
        try:
            row=json.loads(line,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
            required={'i','error'} if type(row)is dict and 'error'in row else {'i','result','result_type','args_before','args_after','alias_edges'}
            if type(row)is dict and set(row)==required and type(row.get('i'))is int and row['i']==len(rows) and len(rows)<count:rows.append(row)
            else:break
        except (ValueError,UnicodeError):break
    try:complete=q.parse(raw,count)==rows
    except (ValueError,UnicodeError,TypeError):complete=False
    return rows,complete


def evaluate(unit,data,indices,metadata,stdout):
    rows,complete=observed(stdout,len(indices));process=metadata['exit_code']==0 and not metadata['timed_out'] and not metadata['output_limit_exceeded']
    counts={'requested_call_slots':len(indices),'complete_observation_rows':len(rows),'successful_complete_streams':int(process and complete),'requested_interpreter_streams':1,'conforming_rows':0,'candidate_error_rows':sum('error'in r for r in rows)};failures=[]
    for index,row in zip(indices,rows):
        ok,reason=compare(unit,data[index],row);counts['conforming_rows']+=int(ok)
        if not ok:failures.append({'case':index,'reason':reason})
    if not process or not complete:failures.append({'batch_failure':'process_or_protocol_failure'})
    return counts,failures


def summarize(unit,data,counts,failures):
    full=counts['requested_call_slots']==counts['complete_observation_rows'] and counts['requested_interpreter_streams']==counts['successful_complete_streams']
    passed=full and (counts['conforming_rows']==0 and all('batch_failure'not in f for f in failures) if unit['negative_control'] else not failures)
    j=inventory();prefix='source' if unit['source_kind']=='new' else 'prior_class_only_source'
    return dict(unit,counts=counts,failures=failures,passed=passed,distinct_case_count=len(data),source_sha256=j[prefix+'_sha256'],source_path=j[prefix+'_path'],adapter_sha256=sha(adapter(unit)),production_service_verified=False,canonical_promotion=False)


def report(rows,digest):
    return {'schema':'gamma.batch04-js443-named-execution.v2','freeze_sha256':digest,'units':rows,'all_execution_units_passed':all(r['passed']for r in rows),'totals':{k:sum(r['counts'][k]for r in rows)for k in rows[0]['counts']},'production_service_verified':False,'canonical_promotions':0,'prior_class_only_proof_scope_corrected':True}


def freeze(args):
    pins=json.loads(args.pins.read_bytes());data=values(args.statements,pins)
    assert '37 passed'in args.preflight.read_text()
    contract={'artifact_hashes':artifacts(),'runtime':q.runtime(),'limits':asdict(LIMITS),'argv':ARGV['javascript'],'statement_pins':pins,'cases_sha256':sha(encoded(data)),'batch_plan':list(q.batches(data)),'units':units(),'created_at':datetime.now(timezone.utc).isoformat(),'host':platform.node(),'preflight_sha256':sha(args.preflight.read_bytes()),'call_entry_events_instrumented':False,'expected_outputs_outside_sandbox':True,'contract':'Official JS named compress(chars) returns integer prefix length and mutates chars prefix; arbitrary tail ignored. Constant workspace mandatory. Separate class compatibility and immutable-input fresh-output free solve. Prior v1 named functional alias must fail native integer/prefix contract.'}
    write(args.freeze,contract);print('FROZEN',sha(args.freeze.read_bytes()),flush=True)


def run(args):
    raw=args.freeze.read_bytes();assert sha(raw)==args.freeze_sha256;c=json.loads(raw);assert artifacts()==c['artifact_hashes'] and q.runtime()==c['runtime'] and asdict(LIMITS)==c['limits'] and ARGV['javascript']==c['argv'] and units()==c['units'];data=values(args.statements,c['statement_pins']);assert sha(encoded(data))==c['cases_sha256'];args.output.mkdir(exist_ok=False,parents=True)
    write(args.output/'run-identity.json',{'freeze_sha256':sha(raw),'artifact_hashes':artifacts(),'host':platform.node(),'started_at':datetime.now(timezone.utc).isoformat()});summaries=[]
    for unit in units():
        counts={};failures=[]
        for number,indices in enumerate(c['batch_plan']):
            packet={'entry':'solve'if unit['entry_form']=='free'else'gamma_entry','calls':[{'args':data[i]['args']}for i in indices]};program=source(unit);stem=unit['id']+f'-{number:03d}'
            write(args.output/(stem+'.start.json'),{'unit':unit,'indices':indices,'inputs_sha256':sha(encoded(packet)),'program_packet_sha256':sha(program),'adapter_sha256':sha(adapter(unit))})
            result=q.sandbox.run(ARGV['javascript'],files={'program.js':program,'harness.cjs':(ROOT/q.TRANSPORT/'harness.cjs').read_bytes(),'inputs.json':encoded(packet)},limits=LIMITS);metadata=asdict(result)
            for stream in ('stdout','stderr'):
                payload=metadata.pop(stream);(args.output/(stem+'.'+stream)).write_bytes(payload);metadata[stream+'_sha256']=sha(payload)
            write(args.output/(stem+'.result.json'),metadata);measured,rejected=evaluate(unit,data,indices,metadata,result.stdout)
            for k,v in measured.items():counts[k]=counts.get(k,0)+v
            failures+=rejected
        summary=summarize(unit,data,counts,failures);summaries.append(summary);write(args.output/(unit['id']+'.summary.json'),summary);print(json.dumps({k:v for k,v in summary.items()if k!='failures'}),flush=True)
    write(args.output/'report.json',report(summaries,sha(raw)))


def replay(args):
    raw=args.freeze.read_bytes();c=json.loads(raw);assert artifacts()==c['artifact_hashes'];identity=json.loads((args.output/'run-identity.json').read_bytes());assert identity['freeze_sha256']==sha(raw)and identity['artifact_hashes']==c['artifact_hashes'];data=values(args.statements,c['statement_pins']);assert sha(encoded(data))==c['cases_sha256'];summaries=[]
    for unit in c['units']:
        counts={};failures=[]
        for number,indices in enumerate(c['batch_plan']):
            stem=unit['id']+f'-{number:03d}';packet={'entry':'solve'if unit['entry_form']=='free'else'gamma_entry','calls':[{'args':data[i]['args']}for i in indices]}
            assert json.loads((args.output/(stem+'.start.json')).read_bytes())=={'unit':unit,'indices':indices,'inputs_sha256':sha(encoded(packet)),'program_packet_sha256':sha(source(unit)),'adapter_sha256':sha(adapter(unit))};metadata=json.loads((args.output/(stem+'.result.json')).read_bytes())
            for stream in ('stdout','stderr'):assert sha((args.output/(stem+'.'+stream)).read_bytes())==metadata[stream+'_sha256']
            measured,rejected=evaluate(unit,data,indices,metadata,(args.output/(stem+'.stdout')).read_bytes())
            for k,v in measured.items():counts[k]=counts.get(k,0)+v
            failures+=rejected
        summary=summarize(unit,data,counts,failures);assert json.loads((args.output/(unit['id']+'.summary.json')).read_bytes())==summary;summaries.append(summary)
    result=report(summaries,sha(raw));assert json.loads((args.output/'report.json').read_bytes())==result
    return {'freeze_sha256':sha(raw),'all_execution_units_passed':result['all_execution_units_passed'],'totals':result['totals'],'execution_units_replayed':len(summaries),'raw_artifact_hashes':{p.name:sha(p.read_bytes())for p in sorted(args.output.iterdir())if p.is_file()and p.name!='replay.json'}}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=('freeze','run','replay'))
    for n in ('statements','freeze'):parser.add_argument('--'+n,type=Path,required=True)
    for n in ('pins','preflight','output'):parser.add_argument('--'+n,type=Path)
    parser.add_argument('--freeze-sha256');args=parser.parse_args()
    if args.operation=='freeze':freeze(args)
    elif args.operation=='run':run(args)
    else:result=replay(args);write(args.output/'replay.json',result);print(json.dumps({k:v for k,v in result.items()if k!='raw_artifact_hashes'}))
