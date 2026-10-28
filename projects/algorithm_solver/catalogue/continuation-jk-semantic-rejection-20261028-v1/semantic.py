"""Targeted wrong programs for the J/K review gaps, judged by a frozen lane.

Each variant in variants.json is an exact original source with one realistic
defect. It runs on the Linux executor through the chosen lane's unchanged
freeze: J/K (original cases) or the boundary lane (original plus repaired cases).
Batches run in plan order until the first failure; an all-pass is a false
acceptance. Raw streams are saved before verdicts and replay never executes.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import platform

HERE = Path(__file__).resolve().parent
LANES = {'jk': HERE.parent/'continuation-jk-qualification-20261028-v1',
         'boundary': HERE.parent/'continuation-jk-boundary-20261028-v1'}
SCHEMA = 'gamma.continuation-jk-semantic-rejection.v1'
SCOPE = ('Judge outcome for targeted wrong variants of exact originals on one frozen lane. Variants are not '
         'candidates; no qualification, adoption or claim about defects outside variants.json.')


def lane_module(name):
    spec = importlib.util.spec_from_file_location('semantic_lane_'+name, LANES[name]/'protocol.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def variants(lane):
    manifest = lane.read_json(HERE/'variants.json')
    if manifest.get('schema') != 'gamma.continuation-jk-semantic-variants.v1':
        raise ValueError('variant manifest schema')
    selected = [v for v in manifest['variants'] if any(v['problem_id'] in ids for ids in lane.IDS.values())]
    return manifest, selected


def program(lane, contract, gate, variant):
    pid, language = variant['problem_id'], variant['language']
    key = next(k for k in lane.IDS if pid in lane.IDS[k]); ext = 'py' if language == 'python' else 'js'
    original = lane.ROOT/lane.DIRECTORIES[key]/language/f'{pid}.{ext}'
    lane.access(gate, pid, language, 'source')
    if contract['artifact_hashes'][str(original.relative_to(lane.ROOT))] != variant['original_sha256']:
        raise ValueError('variant is not derived from the frozen original')
    raw = lane.bounded_regular_read(HERE/variant['path'], maximum_bytes=1024**2)
    if lane.sha(raw) != variant['variant_sha256']:
        raise ValueError('variant bytes differ from manifest')
    files = {'program.'+ext: raw}
    observers = ((('harness.py', lane.TRANSPORT/'harness.py'),) if language == 'python' else
                 (('harness.cjs', lane.FUNCTION_TRANSPORT), ('observer.cjs', lane.TRANSPORT/'harness.cjs')))
    for name, relative in observers:
        files[name] = (lane.ROOT/relative).read_bytes()
        if lane.sha(files[name]) != contract['artifact_hashes'][str(relative)]:
            raise ValueError('observer changed before dispatch')
    return files


def stem(variant, n):
    return f"{variant['problem_id']}-{variant['language']}-{variant['name']}-{n:03d}"


def outcome(variant, failures, executed, planned):
    entry = {key: variant[key] for key in ('problem_id', 'language', 'name', 'variant_sha256')}
    entry.update(executed_batches=executed, planned_batches=planned, failures=failures,
                 status='rejected' if failures else 'false_acceptance')
    return entry


def execute(args):
    lane = lane_module(args.lane)
    raw, contract, pop, gate, data, owners = lane.verified_inputs(args, True)
    manifest, selected = variants(lane)
    args.output.mkdir(parents=True, exist_ok=False)
    lane.write(args.output/'run-identity.json', {'lane': args.lane, 'freeze_sha256': lane.sha(raw),
        'variants_manifest_sha256': lane.sha((HERE/'variants.json').read_bytes()),
        'semantic_sha256': lane.sha((HERE/'semantic.py').read_bytes()), 'runtime': contract['runtime'],
        'host': platform.node(), 'started_at': datetime.now(timezone.utc).isoformat()})
    entries = []
    for variant in selected:
        pid, language = variant['problem_id'], variant['language']
        rows = data[pid]; batches = contract['batch_plans'][str(pid)]['batches']; failures = []; executed = []
        for n, batch in enumerate(batches):
            wire = lane.encoded(lane.packet(rows, batch['indices']))
            if len(wire) != batch['input_bytes']:
                raise ValueError('input packet plan differs')
            files = program(lane, contract, gate, variant); files['inputs.json'] = wire
            lane.write(args.output/(stem(variant, n)+'.start.json'), {'variant_sha256': variant['variant_sha256'],
                'batch': n, 'indices': batch['indices'], 'inputs_sha256': lane.sha(wire)})
            result = lane.sandbox.run(lane.ARGV[language], files=files, limits=lane.LIMITS)
            metadata = asdict(result)
            for name in ('stdout', 'stderr'):
                stream = metadata.pop(name)
                with (args.output/(stem(variant, n)+'.'+name)).open('xb') as handle:
                    handle.write(stream); handle.flush(); os.fsync(handle.fileno())
                metadata[name+'_sha256'] = lane.sha(stream); metadata[name+'_bytes'] = len(stream)
            metadata['input_bytes'] = len(wire)
            lane.write(args.output/(stem(variant, n)+'.result.json'), metadata)
            found = lane.verdict(pid, language, rows, batch['indices'], metadata, result.stdout, owners[pid])
            failures.extend(dict(f, batch=n) for f in found); executed.append(n)
            if found:
                break
        entries.append(outcome(variant, failures, executed, len(batches)))
    report = {'schema': SCHEMA, 'lane': args.lane, 'freeze_sha256': lane.sha(raw), 'scope': SCOPE, 'entries': entries,
              'rejected': sum(e['status'] == 'rejected' for e in entries),
              'false_acceptances': sum(e['status'] == 'false_acceptance' for e in entries)}
    lane.write(args.output/'report.json', report)
    return {key: report[key] for key in ('lane', 'rejected', 'false_acceptances')}


def replay(args):
    lane = lane_module(args.lane)
    raw, contract, pop, gate, data, owners = lane.verified_inputs(args, False)
    manifest, selected = variants(lane); saved = lane.read_json(args.output/'report.json'); entries = []; batches_replayed = 0
    for variant, recorded in zip(selected, saved['entries']):
        pid, language = variant['problem_id'], variant['language']
        rows = data[pid]; batches = contract['batch_plans'][str(pid)]['batches']; failures = []; hits = []
        executed = recorded['executed_batches']
        if executed != list(range(len(executed))):
            raise ValueError('executed batches are not a plan prefix')
        program(lane, contract, gate, variant)
        for n in executed:
            wire = lane.encoded(lane.packet(rows, batches[n]['indices']))
            start = {'variant_sha256': variant['variant_sha256'], 'batch': n, 'indices': batches[n]['indices'], 'inputs_sha256': lane.sha(wire)}
            if not lane.exact(lane.read_json(args.output/(stem(variant, n)+'.start.json')), start):
                raise ValueError('saved start binding differs')
            metadata = lane.read_json(args.output/(stem(variant, n)+'.result.json')); streams = {}
            for name in ('stdout', 'stderr'):
                streams[name] = (args.output/(stem(variant, n)+'.'+name)).read_bytes()
                if lane.sha(streams[name]) != metadata.get(name+'_sha256') or len(streams[name]) != metadata.get(name+'_bytes'):
                    raise ValueError('saved raw stream differs')
            found = lane.verdict(pid, language, rows, batches[n]['indices'], metadata, streams['stdout'], owners[pid])
            failures.extend(dict(f, batch=n) for f in found); hits.append(bool(found)); batches_replayed += 1
        stops = [i for i, hit in enumerate(hits) if hit]
        if (stops and stops != [len(executed)-1]) or (not stops and len(executed) != len(batches)):
            raise ValueError('saved run does not follow the stop rule')
        entries.append(outcome(variant, failures, executed, len(batches)))
    expected = {'schema': SCHEMA, 'lane': args.lane, 'freeze_sha256': lane.sha(raw), 'scope': SCOPE, 'entries': entries,
                'rejected': sum(e['status'] == 'rejected' for e in entries),
                'false_acceptances': sum(e['status'] == 'false_acceptance' for e in entries)}
    if not lane.exact(saved, expected):
        raise ValueError('saved report differs from host replay')
    result = {'schema': SCHEMA+'.replay', 'lane': args.lane, 'freeze_sha256': lane.sha(raw), 'batches_replayed': batches_replayed,
              'all_observations_match_report': True, 'candidate_execution_on_replay_host': False,
              'rejected': expected['rejected'], 'false_acceptances': expected['false_acceptances']}
    lane.write(args.output/'replay.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('run', 'replay'))
    parser.add_argument('--lane', choices=tuple(LANES), required=True)
    for name in ('gate', 'statements', 'freeze', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    for name in ('gate-sha256', 'freeze-sha256'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    result = execute(args) if args.operation == 'run' else replay(args)
    lane = lane_module(args.lane)
    print(lane.encoded(result).decode())


if __name__ == '__main__':
    main()
