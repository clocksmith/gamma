"""Independent Q boundary-lane raw-stream replay; no candidate process or sandbox dispatch."""
import importlib.util
from pathlib import Path
S=importlib.util.spec_from_file_location('q_boundary_replay_protocol',Path(__file__).with_name('protocol.py'))
P=importlib.util.module_from_spec(S);S.loader.exec_module(P)


def read_stream(path,metadata,name):
    # Bound the actual regular file BEFORE hashing, decoding or parsing. The
    # existing sandbox cap is per stream; no aggregate-output assumption.
    raw=P.bounded_regular_read(path,maximum_bytes=P.PER_STREAM_OUTPUT_BYTES)
    if P.sha(raw)!=metadata.get(name+'_sha256') or type(metadata.get(name+'_bytes')) is not int or len(raw)!=metadata[name+'_bytes']:raise ValueError('raw stream hash or byte count differs')
    return raw


def verify(args):
    raw,contract,pop,gate,data,owners=P.verified_inputs(args,False)
    identity=P.read_json(args.output/'run-identity.json')
    if identity.get('freeze_sha256')!=P.sha(raw) or not P.exact(identity.get('artifact_hashes'),contract['artifact_hashes']) or not P.exact(identity.get('runtime'),contract['runtime']) or not P.exact(identity.get('selected_programs'),contract['selected_programs']):raise ValueError('saved run identity differs from exact freeze')
    summaries=[];batch_count=0;raw_pins={}
    for program in pop['programs']:
        pid,language=program['problem_id'],program['language'];rows=data[pid];plan=contract['batch_plans'][str(pid)];failures=[];total=0
        review=contract['manual_reviews'].get(f'{pid}:{language}',{'approved':False,'record':{},'reason':'missing mandatory review'})
        if review.get('approved') is not True:
            for batch_index in range(len(plan['batches'])):
                stem=f'{pid}-{language}-{batch_index:04d}'
                if any((args.output/(stem+suffix)).exists() for suffix in ('.start.json','.result.json','.stdout','.stderr','.launch-error.json')):raise ValueError('unexpected dispatch evidence for review-blocked source')
        for batch_index,entry in enumerate(plan['batches'] if review.get('approved') is True else []):
            indices=entry['indices'];wire=P.encoded(P.packet(pid,rows,indices));stem=f'{pid}-{language}-{batch_index:04d}'
            expected={'problem_id':pid,'language':language,'origin':program['origin'],'source_sha256':program['source_sha256'],'indices':indices,'inputs_sha256':P.sha(wire),'planned':entry}
            if not P.exact(P.read_json(args.output/(stem+'.start.json')),expected):raise ValueError('batch start/source/packet binding differs')
            if (args.output/(stem+'.launch-error.json')).exists():raise ValueError('launch outcome not confirmed; inspect retained evidence, never re-execute automatically')
            metadata=P.read_json(args.output/(stem+'.result.json'))
            if type(metadata.get('input_bytes')) is not int or metadata['input_bytes']!=len(wire):raise ValueError('saved input byte count differs')
            streams={}
            for name in ('stdout','stderr'):
                path=args.output/(stem+'.'+name);streams[name]=read_stream(path,metadata,name)
                raw_pins[path.name]=P.sha(streams[name])
            failures.extend(P.verdict(pid,language,rows,indices,metadata,streams['stdout'],owners[pid]));total+=len(indices);batch_count+=1
        summary=P.program_summary(program,rows,plan,failures,total,review)
        if not P.exact(P.read_json(args.output/f'{pid}-{language}.summary.json'),summary):raise ValueError('source-bound summary differs from regenerated raw replay')
        summaries.append(summary)
    report=P.aggregate_report(raw,contract,summaries)
    if not P.exact(P.read_json(args.output/'report.json'),report):raise ValueError('dynamic program/pair counts or report differ')
    result={'schema':'gamma.q-boundary-independent-host-replay.v1','freeze_sha256':P.sha(raw),'program_count':len(summaries),'sandbox_batches_replayed':batch_count,
            'calls_replayed':sum(row['executed_calls'] for row in summaries),'dispatch_blocked_program_count':report['dispatch_blocked_program_count'],'qualified_program_count':report['qualified_program_count'],'qualified_problem_pair_count':report['qualified_problem_pair_count'],
            'raw_stream_hashes':raw_pins,'all_raw_observations_match_report':True,'candidate_execution_on_replay_host':False,'canonical_admission_changed':False,
            'original_execution_gate_sha256':contract['execution_gate_sha256'],'replay_gate_sha256':args.gate_sha256}
    P.write(args.output/'replay.json',result)
    return {key:value for key,value in result.items() if key!='raw_stream_hashes'}
