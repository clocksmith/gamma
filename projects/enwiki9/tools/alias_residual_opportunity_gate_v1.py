#!/usr/bin/env python3
"""Bounded repeated census over an existing exact strong-parent trace."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CID = 'alias_residual_opportunity1m_q0_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = ROOT / 'results' / CID
    experiment = json.loads((ROOT / 'operations/adaptive/experiments' / (CID + '.json')).read_text())
    for row in experiment['inputs']:
        assert digest(ROOT / row['path']) == row['sha256'].removeprefix('sha256:')
    snapshot = Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    assert (snapshot / 'program.py').read_bytes() == (ROOT / 'tools/alias_residual_opportunity_v1.py').read_bytes()
    trace = ROOT / 'results/typed_event_sleeping_bayes_parent_trace_q0_v1'
    assert (trace / 'native_a.p1').read_bytes() == (trace / 'native_b.p1').read_bytes()
    assert (trace / 'archive_a.bin').read_bytes() == (trace / 'archive_b.bin').read_bytes()
    marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'tools')
    phases = []
    for label in ['first', 'repeat']:
        phase = label + '-census'
        with marker.open('a') as stream:
            stream.write(json.dumps(dict(phase=phase, event='start')) + '\n')
        command = [sys.executable, str(snapshot / 'program.py'),
                   str(ROOT / 'data/enwik9_1000000.bin'),
                   str(ROOT / 'operations/evidence/alias_residual_opportunity_v1/opening1m.store'),
                   str(ROOT / 'operations/evidence/wrt_suffix_alphabet_v1/english.dic'),
                   str(trace / 'native_a.p1'), str(out / (label + '.json'))]
        started = time.monotonic()
        with (out / (label + '.stdout')).open('wb') as stdout, (out / (label + '.stderr')).open('wb') as stderr:
            process = subprocess.run(command, env=env, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=60)
        row = dict(phase=phase, command=command, returncode=process.returncode, elapsed_seconds=time.monotonic() - started)
        (out / (label + '.execution.json')).write_text(json.dumps(row, indent=2) + '\n')
        assert process.returncode == 0, phase
        phases.append(row)
        with marker.open('a') as stream:
            stream.write(json.dumps(dict(phase=phase, event='end')) + '\n')
    assert (out / 'first.json').read_bytes() == (out / 'repeat.json').read_bytes()
    result = json.loads((out / 'first.json').read_text())
    result.update(candidate_id=CID, numerical_receipt_byte_repeat=True,
                  analysis_source_bytes=(snapshot / 'program.py').stat().st_size,
                  analysis_source_note='Observer implementation size, not a measured final decoder or incremental package.',
                  new_native_compression_runs=0, phases=phases,
                  verdict='Natural-text opportunity census only; no new compression gain or search-improvement claim.')
    (out / 'decision.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: result[key] for key in ['counts', 'D', 'S', 'verdict']}))


if __name__ == '__main__':
    main()
