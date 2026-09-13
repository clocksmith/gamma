#!/usr/bin/env python3
"""Complete two missing control checks without replacing failed resource evidence."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
CID = 'wrt_suffix_control_completion250k_q0_v1'
OLD = 'wrt_suffix_alphabet250k_q0_v2'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = ROOT / 'results' / CID
    experiment = json.loads((ROOT / 'operations/adaptive/experiments' / (CID + '.json')).read_text())
    for row in experiment['inputs']:
        assert digest(ROOT / row['path']) == row['sha256'].removeprefix('sha256:')
    snapshot = Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    assert (snapshot / 'program.py').read_bytes() == Path(__file__).read_bytes()
    prior = ROOT / 'results' / OLD
    base = ROOT / 'operations/evidence/wrt_suffix_alphabet_v1'
    raw = ROOT / 'operations/evidence/fixtures/dualstream_opening250k_v1.raw'
    for arm in 'PKD':
        assert (prior / (arm + '.raw')).read_bytes() == raw.read_bytes()
        assert (prior / (arm + '.repeat.arc')).read_bytes() == (prior / (arm + '.arc')).read_bytes()
    assert (prior / 'P.arc').read_bytes() == (prior / 'K.arc').read_bytes()
    assert digest(prior / 'P.arc') == '8159fad519e0d409dbda296b3f6bbe348a541e59a090a5001b18b8bfe655ca0d'
    env = os.environ.copy()
    env.update(CMIX_PRETRAIN_FILE=str(base / 'english.dic'), CMIX_MMAP_ALLOC='0',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', TMPDIR=str(out))
    phases = []
    marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
    for action, flag, source, destination in [
        ('decode', '-d', prior / 'S.arc', out / 'S.raw'),
        ('repeat', '-t', raw, out / 'S.repeat.arc'),
    ]:
        phase = 'S-' + action
        with marker.open('a') as stream:
            stream.write(json.dumps(dict(phase=phase, event='start')) + '\n')
        command = [str(base / 'cmix.bin'), flag, str(prior / 'S.dic'), str(source), str(destination)]
        started = time.monotonic()
        with (out / (phase + '.stdout')).open('wb') as stdout, (out / (phase + '.stderr')).open('wb') as stderr:
            process = subprocess.run(command, cwd=out, env=env, stdout=stdout, stderr=stderr, timeout=270)
        row = dict(phase=phase, command=command, returncode=process.returncode, elapsed_seconds=time.monotonic() - started)
        (out / (phase + '.execution.json')).write_text(json.dumps(row, indent=2) + '\n')
        assert process.returncode == 0, phase
        expected = raw if action == 'decode' else prior / 'S.arc'
        assert destination.read_bytes() == expected.read_bytes(), phase
        phases.append(row)
        with marker.open('a') as stream:
            stream.write(json.dumps(dict(phase=phase, event='end')) + '\n')
    arms = {arm: dict(archive_bytes=(prior / (arm + '.arc')).stat().st_size,
                     archive_sha256=digest(prior / (arm + '.arc')), inverse=True, repeat=True)
            for arm in 'PKDS'}
    result = dict(schema='gamma.enwiki9.suffix-control-completion.v1', candidate_id=CID,
                  raw_population='[0,250000)', input_bytes=raw.stat().st_size, input_sha256=digest(raw),
                  arms=arms, g_P=arms['P']['archive_bytes'] - arms['D']['archive_bytes'],
                  g_S=arms['S']['archive_bytes'] - arms['D']['archive_bytes'],
                  PK_archive_byte_identity=True, all_exact_inverses=True, all_archive_repeats=True,
                  completed_new_phases=2, retained_completed_phases=10, phases=phases,
                  original_execution_resource_status='failed/incomplete; terminal guard unavailable',
                  completion_execution_resource_status='see separate terminal guard',
                  internal_state_witness=None, complete_package_bytes=None, full_corpus_score_bytes=None,
                  objective_credit_bytes=0,
                  verdict='Archive regression on exposed opening250k; control evidence completed across separate executions. Original resource failure remains. No predictive-state or prize confirmation.')
    (out / 'decision.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['g_P', 'g_S', 'verdict']}))


if __name__ == '__main__':
    main()
