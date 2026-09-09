#!/usr/bin/env python3
"""Bounded, fresh-process comparison of exact INT4 substreams, not inference."""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'operations/provenance/fx2_weight_neighbor_model_v1_plan.json'


def binding(path):
    path = Path(path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest)


def audit(model, output, extractor, probe, expected, bounds):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    deadline = time.monotonic() + bounds['elapsed_seconds']
    commands = []

    def phase(name, args):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('aggregate elapsed stop')
        def limits():
            resource.setrlimit(resource.RLIMIT_AS, (bounds['address_space_bytes'],) * 2)
            resource.setrlimit(resource.RLIMIT_CPU, (bounds['cpu_seconds_per_phase'],) * 2)
            resource.setrlimit(resource.RLIMIT_FSIZE, (bounds['per_file_bytes'],) * 2)
        start = time.monotonic()
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        with (output / (name + '.stdout')).open('wb') as stdout, (output / (name + '.stderr')).open('wb') as stderr:
            result = subprocess.run([str(a) for a in args], stdout=stdout, stderr=stderr,
                                    timeout=min(remaining, bounds['phase_elapsed_seconds']), preexec_fn=limits)
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        row = dict(name=name, command=[str(a) for a in args], returncode=result.returncode,
                   elapsed_seconds=time.monotonic() - start,
                   cpu_seconds=after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
                   cumulative_child_peak_rss_kib=after.ru_maxrss)
        commands.append(row)
        with (output / 'commands.jsonl').open('a') as log:
            log.write(json.dumps(row) + '\n')
        if result.returncode:
            raise ValueError('phase failed: ' + name)
        return json.loads((output / (name + '.stdout')).read_text())

    manifest = phase('extract', [extractor, model, output / 'symbols'])
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError('population differs: ' + key)
    if not manifest.get('canonical_original_regeneration'):
        raise ValueError('original-model regeneration missing')
    rows = []
    allocated = 0
    for tensor in manifest['rows']:
        index = str(tensor['index'])
        raw = output / 'symbols' / (index + '.raw')
        original = binding(raw)
        if original['bytes'] != tensor['symbols']:
            raise ValueError('extracted symbol length differs')
        row = dict(tensor=tensor, original=original, arms={})
        for arm in ('P', 'K', 'D'):
            stem = index + '-' + arm
            archive, restored, repeat = [output / (stem + suffix) for suffix in ('.bin', '.raw', '.repeat')]
            phase(stem + '-encode', [probe, arm, raw, archive, tensor['width']])
            phase(stem + '-decode', [probe, 'restore', archive, restored])
            phase(stem + '-repeat', [probe, arm, raw, repeat, tensor['width']])
            a, r, d = binding(archive), binding(repeat), binding(restored)
            if (a['bytes'], a['sha256']) != (r['bytes'], r['sha256']):
                raise ValueError('repeat differs: ' + stem)
            if (d['bytes'], d['sha256']) != (original['bytes'], original['sha256']):
                raise ValueError('inverse differs: ' + stem)
            table = 960 if arm == 'D' else 60
            row['arms'][arm] = dict(archive=a, repeat=r, restored=d, count_table_bytes=table,
                                    framing_bytes=17, range_stream_bytes=a['bytes'] - table - 17)
        if row['arms']['P']['archive']['sha256'] != row['arms']['K']['archive']['sha256']:
            raise ValueError('P/K identity differs')
        rows.append(row)
        allocated = sum(p.stat().st_blocks * 512 for p in output.rglob('*') if p.is_file())
        if allocated > bounds['scratch_bytes']:
            raise ValueError('scratch stop')
        if time.monotonic() >= deadline:
            raise TimeoutError('aggregate elapsed stop')
    totals = {arm: sum(row['arms'][arm]['archive']['bytes'] for row in rows) for arm in ('P', 'K', 'D')}
    result = dict(schema='gamma.enwiki9.fx2-weight-neighbor-model-audit.v1', model=binding(model),
                  population=manifest, rows=rows, totals=totals, substream_bytes_saved=totals['P'] - totals['D'],
                  all_independent_inverses=True, all_deterministic_repeats=True, parent_bookkeeping_identity=True,
                  phase_count=len(commands), allocated_scratch_bytes=allocated,
                  complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
                  scope='All INT4 substreams with paid tables and framing; not a complete FX2 model container or native archive.')
    temporary = output / 'receipt.partial'
    temporary.write_text(json.dumps(result, indent=2) + '\n')
    temporary.rename(output / 'receipt.json')
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--admission', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--extractor', required=True)
    parser.add_argument('--probe', required=True)
    args = parser.parse_args()
    plan = json.loads(PLAN.read_text())
    admission = json.loads(Path(args.admission).read_text())
    if admission.get('id') != plan['id'] or admission.get('admitted') is not True:
        raise ValueError('missing matching admission')
    if sorted(os.sched_getaffinity(0)) != plan['bounds']['cpu_set']:
        raise ValueError('CPU assignment differs')
    inputs = json.loads(Path(args.inputs).read_text())
    for row in inputs['inputs']:
        actual = binding(ROOT / row['path'])
        if actual['bytes'] != row['bytes'] or actual['sha256'] != row['sha256']:
            raise ValueError('changed input: ' + row['path'])
    for key in ('extractor', 'probe'):
        actual = binding(getattr(args, key))
        if actual['sha256'] != admission[key]['sha256'] or actual['bytes'] != admission[key]['bytes']:
            raise ValueError('executable differs: ' + key)
    model = ROOT / plan['model']['path']
    actual = binding(model)
    if any(actual[k] != plan['model'][k] for k in ('bytes', 'sha256')):
        raise ValueError('model identity differs')
    result = audit(model, args.output, args.extractor, args.probe, plan['expected'], plan['bounds'])
    print(json.dumps({key: result[key] for key in ('totals', 'substream_bytes_saved', 'phase_count')}))
