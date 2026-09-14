#!/usr/bin/env python3
"""Bounded repeated development selection; native FX2 is not run or modified."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CID = 'fx2_paid_odds_cost250k_v1'


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    out = ROOT / 'results' / CID
    e = json.loads((ROOT / 'operations/adaptive/experiments' / (CID + '.json')).read_text())
    for r in e['inputs']:
        if digest(ROOT / r['path']) != r['sha256'].removeprefix('sha256:'):
            raise ValueError('bound input differs: ' + r['path'])
    snapshot = Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    if (snapshot / 'program.py').read_bytes() != (ROOT / 'tools/fx2_paid_odds_cost250k_v1.py').read_bytes():
        raise ValueError('sealed source differs')
    native = ROOT / 'results/fx2_kda_carry_opening250k_v1/work/native'
    for suffix in ('coder', 'arc'):
        expected = digest(native / ('P-encode.' + suffix))
        for phase in ('P-repeat', 'K-encode', 'K-repeat'):
            if digest(native / (phase + '.' + suffix)) != expected:
                raise ValueError('retained parent identity differs')
    env = {**os.environ, 'PYTHONPATH': str(ROOT), 'PYTHONDONTWRITEBYTECODE': '1'}
    marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
    phases = []
    for label in ('first', 'repeat'):
        with marker.open('a') as f:
            f.write(json.dumps(dict(phase=label, event='start')) + '\n')
        cmd = [sys.executable, str(snapshot / 'program.py'), str(ROOT), str(out / (label + '.json'))]
        started = time.monotonic()
        with (out / (label + '.stdout')).open('xb') as stdout, (out / (label + '.stderr')).open('xb') as stderr:
            r = subprocess.run(cmd, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=150)
        row = dict(phase=label, command=cmd, returncode=r.returncode, elapsed_seconds=time.monotonic() - started)
        (out / (label + '.execution.json')).write_text(json.dumps(row, indent=2) + '\n')
        phases.append(row)
        with marker.open('a') as f:
            f.write(json.dumps(dict(phase=label, event='end')) + '\n')
        if r.returncode:
            raise ValueError('selection subprocess failed')
    for suffix in ('.json', '.policy'):
        if (out / ('first' + suffix)).read_bytes() != (out / ('repeat' + suffix)).read_bytes():
            raise ValueError('repeated result differs')
    result = json.loads((out / 'first.json').read_text())
    result.update(candidate_id=CID, numerical_receipt_byte_repeat=True,
                  policy_byte_repeat=True, retained_PK_archive_and_trace_identity=True, phases=phases)
    (out / 'decision.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: result[k] for k in ('paid_ideal_gain_lower_bits', 'paid_ideal_gain_upper_bits', 'policy_bytes')}))


if __name__ == '__main__':
    main()
