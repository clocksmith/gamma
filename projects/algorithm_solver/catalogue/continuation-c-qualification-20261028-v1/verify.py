"""Independent host replay of frozen raw streams; never executes candidates."""
from __future__ import annotations
from protocol import (DIRECTORIES, IDS, LANGUAGES, ROOT, encoded, exact, packet,
                      program_summary, read_json, sha, verdict, verified_inputs, write)


def verify(args):
    raw,contract,pop,gate,data,owners=verified_inputs(args,False)
    identity=read_json(args.output/'run-identity.json')
    if (identity.get('freeze_sha256')!=sha(raw) or not exact(identity.get('artifact_hashes'),contract['artifact_hashes'])
            or not exact(identity.get('runtime'),contract['runtime'])):
        raise ValueError('saved execution identity differs from freeze')
    summaries=[];batches=0;raw_evidence={}
    for key in IDS:
        directory=ROOT/DIRECTORIES[key]
        for pid in IDS[key]:
            rows=data[pid];plan=contract['batch_plans'][str(pid)]
            for language in LANGUAGES:
                failures=[];total=0;suffix='py' if language=='python' else 'js'
                source_pin=contract['artifact_hashes'][str((directory/language/f'{pid}.{suffix}').relative_to(ROOT))]
                for index,entry in enumerate(plan['batches']):
                    stem=f'{pid}-{language}-{index:03d}';indices=entry['indices'];wire=encoded(packet(rows,indices))
                    expected_start={'problem_id':pid,'language':language,'indices':indices,
                        'inputs_sha256':sha(wire),'source_sha256':source_pin,'planned':entry}
                    if not exact(read_json(args.output/(stem+'.start.json')),expected_start):
                        raise ValueError('saved batch start/input/source binding differs')
                    metadata=read_json(args.output/(stem+'.result.json'))
                    if type(metadata.get('input_bytes')) is not int or metadata['input_bytes']!=len(wire):
                        raise ValueError('saved input byte count differs')
                    streams={}
                    for name in ('stdout','stderr'):
                        path=args.output/(stem+'.'+name);streams[name]=path.read_bytes()
                        if (sha(streams[name])!=metadata.get(name+'_sha256') or
                                type(metadata.get(name+'_bytes')) is not int or len(streams[name])!=metadata[name+'_bytes']):
                            raise ValueError('saved raw stream hash or byte count differs')
                        raw_evidence[path.name]=sha(streams[name])
                    failures.extend(verdict(pid,language,rows,indices,metadata,streams['stdout'],owners[pid]));total+=len(indices);batches+=1
                summary=program_summary(pid,language,rows,plan,failures,total,contract['manual_reviews'][f'{pid}:{language}'])
                if not exact(read_json(args.output/f'{pid}-{language}.summary.json'),summary):
                    raise ValueError('saved program summary differs from raw replay')
                summaries.append(summary)
    expected_report={'schema':'gamma.continuation-c-execution-report.v1','freeze_sha256':sha(raw),
        'programs':summaries,'canonical_admission_changed':False,'scope':contract['scope']}
    if not exact(read_json(args.output/'report.json'),expected_report):
        raise ValueError('saved aggregate differs from independently regenerated replay')
    result={'schema':'gamma.continuation-c-host-replay.v1','freeze_sha256':sha(raw),
        'programs_replayed':len(summaries),'sandbox_batches_replayed':batches,
        'calls_replayed':sum(row['executed_calls'] for row in summaries),
        'admitted_case_passes':sum(row['admitted_cases_passed'] for row in summaries),
        'qualified_finite_suite_programs':sum(row['qualified'] for row in summaries),
        'raw_stream_hashes':raw_evidence,'all_observations_match_report':True,
        'canonical_admission_changed':False,'candidate_execution_on_replay_host':False,
        'replay_gate_sha256':args.gate_sha256,'original_execution_gate_sha256':contract['execution_gate_sha256']}
    write(args.output/'replay.json',result)
    return {key:value for key,value in result.items() if key!='raw_stream_hashes'}
