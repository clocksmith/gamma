"""Judge rejection measurement: seeded wrong variants of passing J/K originals.

Runs on the Linux executor after the J/K qualification run and its host replay.
It reuses that lane's exact frozen cases, batch plans, observers, sandbox limits,
access gate and verdict function. The only changed bytes are the program file:
the original source plus one fixed wrapper from variants.py. Expected results
stay on the host, and raw streams are saved before any verdict.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'continuation-jk-qualification-20261028-v1'))
sys.path.insert(0, str(HERE))
import protocol as jk  # noqa: E402
from variants import OPERATORS, triggers, variant_source  # noqa: E402

SCHEMA = 'gamma.continuation-jk-rejection.v1'
SCOPE = ('Judge rejection of seeded wrong variants on the frozen J/K finite cases. Variants are wrappers '
         'around passing originals, not candidates. No candidate qualification, adoption or claim about '
         'defects outside these operators.')


def baseline(args, raw):
    report = jk.read_json(args.baseline/'report.json'); replay = jk.read_json(args.baseline/'replay.json')
    if (report.get('freeze_sha256') != jk.sha(raw) or replay.get('freeze_sha256') != jk.sha(raw)
            or replay.get('all_observations_match_report') is not True):
        raise ValueError('host-replayed J/K baseline bound to this exact freeze required')
    return {(row['problem_id'], row['language']): row for row in report['programs']}


def plan(data, contract, eligible):
    entries = []
    for key in jk.IDS:
        for pid in jk.IDS[key]:
            rows = data[pid]; batches = contract['batch_plans'][str(pid)]['batches']
            for language in jk.LANGUAGES:
                base = eligible.get((pid, language))
                for op, (kind, reasons) in OPERATORS.items():
                    entry = {'problem_id': pid, 'language': language, 'operator': op, 'kind': kind,
                             'confirming_reasons': list(reasons)}
                    if base is None or base.get('admitted_cases_passed') is not True:
                        entry.update(status='original_not_passing', triggered_cases=[], batches=[])
                    else:
                        fired = [[index for position, index in enumerate(batch['indices'])
                                  if triggers(op, language, rows[index]['args'], position, rows[index]['expected'])]
                                 for batch in batches]
                        entry['triggered_cases'] = sorted({index for found in fired for index in found})
                        entry['batches'] = (list(range(len(batches))) if op == 'control-copy'
                                            else [n for n, found in enumerate(fired) if found])
                        entry['status'] = 'planned' if entry['batches'] else 'not_triggered'
                    entries.append(entry)
    return entries


def program_files(contract, gate, pid, language, op, directory):
    ext = 'py' if language == 'python' else 'js'
    jk.access(gate, pid, language, 'source'); path = directory/language/f'{pid}.{ext}'
    source = jk.bounded_regular_read(path, maximum_bytes=1024**2)
    if jk.sha(source) != contract['artifact_hashes'][str(path.relative_to(jk.ROOT))]:
        raise ValueError('original source changed before variant construction')
    files = {'program.'+ext: variant_source(source, language, op)}
    observers = ((('harness.py', jk.TRANSPORT/'harness.py'),) if language == 'python' else
                 (('harness.cjs', jk.FUNCTION_TRANSPORT), ('observer.cjs', jk.TRANSPORT/'harness.cjs')))
    for name, relative in observers:
        files[name] = (jk.ROOT/relative).read_bytes()
        if jk.sha(files[name]) != contract['artifact_hashes'][str(relative)]:
            raise ValueError('observer changed before dispatch')
    return files, jk.sha(source)


def classify(entry, failures):
    triggered = set(entry['triggered_cases'])
    if entry['operator'] == 'control-copy':
        return 'control_accepted' if not failures else 'control_rejected'
    if not failures:
        return 'false_acceptance'
    if any(f['case'] in triggered and f['reason'] in entry['confirming_reasons'] for f in failures):
        return 'rejected_confirming'
    return 'rejected_other'


def summarize(entries):
    totals = {}
    for entry in entries:
        for scope in ('all', entry['language']):
            bucket = totals.setdefault(scope, {}).setdefault(entry['operator'], {})
            bucket[entry['status']] = bucket.get(entry['status'], 0)+1
    return totals


def execute(args):
    raw, contract, pop, gate, data, owners = jk.verified_inputs(args, True)
    eligible = baseline(args, raw)
    args.output.mkdir(parents=True, exist_ok=False)
    entries = plan(data, contract, eligible)
    jk.write(args.output/'plan.json', {'schema': SCHEMA+'.plan', 'freeze_sha256': jk.sha(raw), 'entries': entries})
    jk.write(args.output/'run-identity.json', {'freeze_sha256': jk.sha(raw), 'artifact_hashes': contract['artifact_hashes'],
        'runtime': contract['runtime'], 'variants_sha256': jk.sha((HERE/'variants.py').read_bytes()),
        'rejection_sha256': jk.sha((HERE/'rejection.py').read_bytes()), 'host': platform.node(),
        'started_at': datetime.now(timezone.utc).isoformat()})
    for entry in entries:
        if entry['status'] != 'planned':
            continue
        pid, language, op = entry['problem_id'], entry['language'], entry['operator']
        key = next(k for k in jk.IDS if pid in jk.IDS[k]); directory = jk.ROOT/jk.DIRECTORIES[key]
        rows = data[pid]; batches = contract['batch_plans'][str(pid)]['batches']
        failures = []; executed = []
        for n in entry['batches']:
            indices = batches[n]['indices']; wire = jk.encoded(jk.packet(rows, indices))
            if len(wire) != batches[n]['input_bytes']:
                raise ValueError('input packet plan differs')
            files, source_sha = program_files(contract, gate, pid, language, op, directory)
            files['inputs.json'] = wire
            stem = f'{pid}-{language}-{op}-{n:03d}'
            jk.write(args.output/(stem+'.start.json'), {'problem_id': pid, 'language': language, 'operator': op,
                'batch': n, 'indices': indices, 'inputs_sha256': jk.sha(wire), 'source_sha256': source_sha,
                'variant_sha256': jk.sha(files['program.'+('py' if language == 'python' else 'js')])})
            result = jk.sandbox.run(jk.ARGV[language], files=files, limits=jk.LIMITS)
            metadata = asdict(result)
            for name in ('stdout', 'stderr'):
                stream = metadata.pop(name)
                with (args.output/(stem+'.'+name)).open('xb') as handle:
                    handle.write(stream); handle.flush(); os.fsync(handle.fileno())
                metadata[name+'_sha256'] = jk.sha(stream); metadata[name+'_bytes'] = len(stream)
            metadata['input_bytes'] = len(wire)
            jk.write(args.output/(stem+'.result.json'), metadata)
            found = jk.verdict(pid, language, rows, indices, metadata, result.stdout, owners[pid])
            failures.extend(dict(f, batch=n) for f in found); executed.append(n)
            # One observed failure settles a seeded variant; controls run every batch.
            if found and op != 'control-copy':
                break
        entry.update(executed_batches=executed, failures=failures)
        entry['status'] = classify(entry, failures)
    report = {'schema': SCHEMA, 'freeze_sha256': jk.sha(raw), 'scope': SCOPE, 'entries': entries,
              'totals': summarize(entries), 'canonical_admission_changed': False}
    jk.write(args.output/'report.json', report)
    return {'entries': len(entries), 'totals': report['totals']['all']}


def replay(args):
    """Rebuild every verdict from saved streams on the host; never executes programs."""
    raw, contract, pop, gate, data, owners = jk.verified_inputs(args, False)
    eligible = baseline(args, raw)
    saved = jk.read_json(args.output/'report.json')
    if saved.get('freeze_sha256') != jk.sha(raw):
        raise ValueError('saved report is bound to another freeze')
    expected_plan = plan(data, contract, eligible)
    if not jk.exact(jk.read_json(args.output/'plan.json')['entries'], expected_plan):
        raise ValueError('saved plan differs from regenerated plan')
    entries = []; batches_replayed = 0
    for planned, recorded in zip(expected_plan, saved['entries']):
        entry = dict(planned)
        if planned['status'] == 'planned':
            pid, language, op = planned['problem_id'], planned['language'], planned['operator']
            key = next(k for k in jk.IDS if pid in jk.IDS[k]); directory = jk.ROOT/jk.DIRECTORIES[key]
            rows = data[pid]; batches = contract['batch_plans'][str(pid)]['batches']; failures = []; hits = []
            executed = recorded.get('executed_batches', [])
            if executed != planned['batches'][:len(executed)]:
                raise ValueError('executed batches are not a prefix of the plan')
            for n in executed:
                indices = batches[n]['indices']; wire = jk.encoded(jk.packet(rows, indices))
                files, source_sha = program_files(contract, gate, pid, language, op, directory)
                stem = f'{pid}-{language}-{op}-{n:03d}'
                start = {'problem_id': pid, 'language': language, 'operator': op, 'batch': n, 'indices': indices,
                         'inputs_sha256': jk.sha(wire), 'source_sha256': source_sha,
                         'variant_sha256': jk.sha(files['program.'+('py' if language == 'python' else 'js')])}
                if not jk.exact(jk.read_json(args.output/(stem+'.start.json')), start):
                    raise ValueError('saved start binding differs')
                metadata = jk.read_json(args.output/(stem+'.result.json')); streams = {}
                for name in ('stdout', 'stderr'):
                    streams[name] = (args.output/(stem+'.'+name)).read_bytes()
                    if jk.sha(streams[name]) != metadata.get(name+'_sha256') or len(streams[name]) != metadata.get(name+'_bytes'):
                        raise ValueError('saved raw stream differs')
                found = jk.verdict(pid, language, rows, indices, metadata, streams['stdout'], owners[pid])
                failures.extend(dict(f, batch=n) for f in found); hits.append(bool(found)); batches_replayed += 1
            # Seeded variants stop at their first failing batch; controls run every batch.
            stops = [i for i, hit in enumerate(hits) if hit]
            complete = len(executed) == len(planned['batches'])
            if op == 'control-copy' and not complete:
                raise ValueError('control did not run every planned batch')
            if op != 'control-copy' and ((stops and stops[0] != len(executed)-1) or (not stops and not complete)):
                raise ValueError('saved run does not follow the stop rule')
            entry.update(executed_batches=executed, failures=failures)
            entry['status'] = classify(entry, failures)
        entries.append(entry)
    expected = {'schema': SCHEMA, 'freeze_sha256': jk.sha(raw), 'scope': SCOPE, 'entries': entries,
                'totals': summarize(entries), 'canonical_admission_changed': False}
    if not jk.exact(saved, expected):
        raise ValueError('saved report differs from host replay')
    result = {'schema': SCHEMA+'.replay', 'freeze_sha256': jk.sha(raw), 'batches_replayed': batches_replayed,
              'all_observations_match_report': True, 'candidate_execution_on_replay_host': False,
              'totals': expected['totals']}
    jk.write(args.output/'replay.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('run', 'replay'))
    for name in ('gate', 'statements', 'freeze', 'baseline', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    for name in ('gate-sha256', 'freeze-sha256'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    result = execute(args) if args.operation == 'run' else replay(args)
    print(jk.encoded(result).decode())


if __name__ == '__main__':
    main()
