#!/usr/bin/env python3
"""Compare P/K/A/D exact INT4 substreams; no inference or corpus credit."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import time
from fx2_weight_neighbor_model_audit_v1 import binding

ROOT = Path(__file__).resolve().parents[1]
ARMS = ('P', 'K', 'A', 'D')


def audit(model, output, extractor, probe, expected, bounds):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    deadline = time.monotonic() + bounds['elapsed_seconds']
    commands, rows = [], []

    def phase(name, args):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('aggregate elapsed stop')
        def limits():
            for key, value in ((resource.RLIMIT_AS, bounds['address_space_bytes']),
                               (resource.RLIMIT_CPU, bounds['cpu_seconds_per_phase']),
                               (resource.RLIMIT_FSIZE, bounds['per_file_bytes'])):
                resource.setrlimit(key, (value, value))
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        start = time.monotonic()
        with (output / (name + '.stdout')).open('xb') as stdout, (output / (name + '.stderr')).open('xb') as stderr:
            child = subprocess.run([str(a) for a in args], stdout=stdout, stderr=stderr,
                                   timeout=min(remaining, bounds['phase_elapsed_seconds']), preexec_fn=limits)
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        record = dict(name=name, command=list(map(str, args)), returncode=child.returncode,
                      elapsed_seconds=time.monotonic() - start,
                      cpu_seconds=after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
                      cumulative_child_peak_rss_kib=after.ru_maxrss)
        commands.append(record)
        with (output / 'commands.jsonl').open('a') as stream:
            stream.write(json.dumps(record) + '\n')
        if child.returncode:
            raise ValueError('phase failed: ' + name)
        return json.loads((output / (name + '.stdout')).read_text())

    manifest = phase('extract', [extractor, model, output / 'symbols'])
    if any(manifest.get(k) != v for k, v in expected.items()):
        raise ValueError('population differs')
    if not manifest.get('canonical_original_regeneration'):
        raise ValueError('original model regeneration missing')
    for tensor in manifest['rows']:
        raw = output / 'symbols' / (str(tensor['index']) + '.raw')
        original = binding(raw)
        if original['bytes'] != tensor['symbols']:
            raise ValueError('symbol length differs')
        row = dict(tensor=tensor, original=original, arms={})
        for arm in ARMS:
            stem = str(tensor['index']) + '-' + arm
            archive, restored, repeat = [output / (stem + suffix) for suffix in ('.bin', '.raw', '.repeat')]
            phase(stem + '-encode', [probe, arm, raw, archive, tensor['width']])
            phase(stem + '-decode', [probe, 'restore', archive, restored])
            phase(stem + '-repeat', [probe, arm, raw, repeat, tensor['width']])
            a, r, d = binding(archive), binding(repeat), binding(restored)
            if any(a[k] != r[k] for k in ('bytes', 'sha256')):
                raise ValueError('repeat differs: ' + stem)
            if any(original[k] != d[k] for k in ('bytes', 'sha256')):
                raise ValueError('inverse differs: ' + stem)
            table = 60 if arm in ('P', 'K') else 0
            row['arms'][arm] = dict(archive=a, repeat=r, restored=d, count_table_bytes=table,
                                   framing_bytes=17, range_stream_bytes=a['bytes'] - table - 17)
        if row['arms']['P']['archive']['sha256'] != row['arms']['K']['archive']['sha256']:
            raise ValueError('P/K identity differs')
        rows.append(row)
        if sum(p.stat().st_blocks * 512 for p in output.rglob('*') if p.is_file()) > bounds['scratch_bytes']:
            raise ValueError('scratch stop')
        if time.monotonic() >= deadline:
            raise TimeoutError('aggregate elapsed stop')
    totals = {arm: sum(row['arms'][arm]['archive']['bytes'] for row in rows) for arm in ARMS}
    result = dict(schema='gamma.enwiki9.fx2-weight-adaptive-neighbor-model.v1', model=binding(model),
                  population=manifest, rows=rows, totals=totals, phase_count=len(commands),
                  substream_bytes_saved=totals['P'] - totals['D'], neighbor_bytes_saved=totals['A'] - totals['D'],
                  all_independent_inverses=True, all_deterministic_repeats=True, parent_bookkeeping_identity=True,
                  complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0)
    temporary = output / 'receipt.partial'
    temporary.write_text(json.dumps(result, indent=2) + '\n')
    temporary.rename(output / 'receipt.json')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inputs', 'admission', 'output', 'extractor', 'probe'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    plan = json.loads((ROOT / 'operations/provenance/fx2_weight_adaptive_neighbor_model_v1_plan.json').read_text())
    admission = json.loads(Path(args.admission).read_text())
    if admission.get('id') != plan['id'] or admission.get('admitted') is not True:
        raise ValueError('matching admission required')
    if sorted(os.sched_getaffinity(0)) != plan['bounds']['cpu_set']:
        raise ValueError('CPU assignment differs')
    inputs = json.loads(Path(args.inputs).read_text())
    for row in inputs['inputs'] + [plan['model']]:
        actual = binding(ROOT / row['path'])
        if any(actual[k] != row[k] for k in ('bytes', 'sha256')):
            raise ValueError('changed input: ' + row['path'])
    for key in ('extractor', 'probe'):
        actual = binding(getattr(args, key))
        if any(actual[k] != admission[key][k] for k in ('bytes', 'sha256')):
            raise ValueError('changed executable: ' + key)
    result = audit(ROOT / plan['model']['path'], args.output, args.extractor, args.probe, plan['expected'], plan['bounds'])
    print(json.dumps({k: result[k] for k in ('totals', 'substream_bytes_saved', 'neighbor_bytes_saved', 'phase_count')}))


if __name__ == '__main__':
    main()
