"""Count requested slots and actually captured complete observations separately."""
import ast
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[3]
RUN=ROOT/'projects/algorithm_solver/runs/downloaded-batch04-independent-20261027'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def unique(items):
    result={}
    for key,value in items:
        if key in result:raise ValueError('duplicate observation field')
        result[key]=value
    return result


def phase(name,directory,freeze):
    replay=json.loads((directory/'replay.json').read_bytes())
    for relative,digest in replay['raw_artifact_hashes'].items():
        assert sha((directory/relative).read_bytes())==digest,(name,relative)
    streams=[]
    for meta_path in sorted(directory.glob('*.result.json')):
        stem=meta_path.name.removesuffix('.result.json');metadata=json.loads(meta_path.read_bytes())
        if name=='owned_buffer_probe':
            # Read the exact frozen packet builder, rather than infer request size from successful output.
            builder=BASE/'repairs-v1/ownership-v1/proof.py'
            contract=json.loads(freeze.read_bytes())
            assert sha(builder.read_bytes())==contract['artifact_hashes'][str(builder.relative_to(ROOT))]
            function=next(n for n in ast.parse(builder.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='packet')
            counts=[n.args[0].value for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='range' and len(n.args)==1 and isinstance(n.args[0],ast.Constant)]
            assert counts==[16];requested=counts[0]
        else:
            requested=len(json.loads((directory/(stem+'.start.json')).read_bytes())['indices'])
        stdout=(directory/(stem+'.stdout')).read_bytes()
        assert sha(stdout)==metadata['stdout_sha256']
        rows=[];done=[];invalid=[]
        for line_index,line in enumerate(stdout.splitlines()):
            try:
                row=json.loads(line,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
            except (ValueError,UnicodeError):invalid.append(line_index);continue
            if type(row)is dict and set(row)=={'done'} and type(row['done'])is int:
                done.append(row['done']);continue
            required={'i','error'} if type(row)is dict and 'error'in row else {'i','result','result_type','args_before','args_after','alias_edges'}
            if (type(row)is dict and set(row)==required and type(row.get('i'))is int and row['i']==len(rows) and len(rows)<requested):rows.append(row)
            else:invalid.append(line_index)
        process_ok=metadata['exit_code']==0 and not metadata['timed_out'] and not metadata['output_limit_exceeded']
        complete=not invalid and len(rows)==requested and done==[requested]
        streams.append({'stem':stem,'requested_call_slots':requested,'complete_observation_rows':len(rows),
                        'normal_result_rows':sum('result'in r for r in rows),'candidate_error_rows':sum('error'in r for r in rows),
                        'requested_slots_without_complete_observation':requested-len(rows),
                        'successful_process_exit':process_ok,'complete_protocol_stream':complete,
                        'successful_complete_stream':process_ok and complete,'completion_records':done,
                        'invalid_or_partial_line_indices':invalid,'exit_code':metadata['exit_code'],
                        'signal':metadata['signal'],'wall_seconds':metadata['wall_seconds'],
                        'timed_out':metadata['timed_out'],'output_limit_exceeded':metadata['output_limit_exceeded'],
                        'stdout_sha256':metadata['stdout_sha256'],'metadata_sha256':sha(meta_path.read_bytes())})
    totals={key:sum(row[key] for row in streams) for key in ('requested_call_slots','complete_observation_rows','normal_result_rows','candidate_error_rows','requested_slots_without_complete_observation','successful_process_exit','complete_protocol_stream','successful_complete_stream')}
    totals.update({'requested_interpreter_streams':len(streams),'failed_or_incomplete_streams':sum(not r['successful_complete_stream'] for r in streams)})
    return {'name':name,'freeze_sha256':sha(freeze.read_bytes()),'raw_replay_sha256':sha((directory/'replay.json').read_bytes()),
            'totals':totals,'streams':streams,'call_entry_events_instrumented':False,
            'interpretation':'Requested slots are planned input indices, not evidence that each call began or completed. Complete observation rows are captured result/error records. A killed first call can leave later repeated slots unstarted; neither is counted as a completed observation.'}


def audit():
    phases=[phase('original_baseline',RUN/'results',BASE/'frozen-contract.json'),
            phase('repaired_variants_and_native_controls',RUN/'repair-results',BASE/'repairs-v1/frozen-contract.json'),
            phase('owned_buffer_probe',RUN/'ownership-results',BASE/'repairs-v1/ownership-v1/frozen-contract.json')]
    return {'schema':'gamma.batch04-measured-observation-counts.v1','phases':phases,
            'original_frozen_reports_modified':False,'audit_source_sha256':sha(Path(__file__).read_bytes()),
            'terminology':'Do not describe planned indices or request slots as completed executions. No per-call entry marker exists, so begun-but-unfinished and never-started slots cannot be distinguished from these artifacts.'}


if __name__=='__main__':
    result=audit();(BASE/'MEASURED_OBSERVATIONS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({r['name']:r['totals'] for r in result['phases']},indent=2))
