#!/usr/bin/env python3
"""Isolate an undeclared working-directory dictionary in an unchanged decoder."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from fx2_trim_auxiliary_ppm_v1 import NativeGate, sandbox, RUNTIME
from fx2_trim_confirm1m_v1 import clean_scratch, equal

ID = 'fx2_ambient_dictionary_probe_v1'
CAPS = dict(cpus=[2], memory_bytes=9999998976, swap_bytes=0,
            scratch_bytes=16000000000, wall_seconds=1200)
BASE = 'results/fx2_trim_auxiliary_ppm_v1/work/P/'
PLAN = 'operations/provenance/' + ID + '_plan.json'
MEMBERS = {
    'archive9': BASE + 'isolated-decoder/archive9',
    'dictionary.bin': BASE + 'dictionary/english.dic',
    '.tfweights': BASE + 'models/6m-q4-fp32.tfwc2',
    '.ready4cmix_decomp': BASE + 'encode.arc',
}


def execute(g):
    plan = json.loads(g.buffers[PLAN])
    assert plan['caps'] == CAPS
    runtime = json.loads(g.buffers[RUNTIME])
    helper = g.work / 'bootstrap'
    g.copy(BASE + 'bootstrap', helper)
    helper.chmod(0o755)
    rows = {}
    for label, ambient in [('absent-A', False), ('present', True), ('absent-B', False)]:
        directory = g.work / label
        directory.mkdir()
        for name, source in MEMBERS.items():
            g.copy(source, directory / name)
        (directory / 'archive9').chmod(0o755)
        if ambient:
            g.copy(MEMBERS['dictionary.bin'], directory / '.dict')
        command = sandbox(runtime, directory, helper, ['./archive9', '-d',
                          'dictionary.bin', '.ready4cmix_decomp', 'restored.raw',
                          '--transformer', '.tfweights'])
        try:
            g.run(label, command, 300, accepted=(0, 139) if ambient else (0,), work=directory)
        finally:
            clean_scratch(g, directory, label)
        restored = directory / 'restored.raw'
        exact = restored.is_file() and restored.read_bytes() == g.buffers[BASE + 'population.raw']
        if not ambient:
            equal(restored, ROOT / (BASE + 'population.raw'))
        rows[label] = dict(ambient_dictionary=ambient, returncode=g.commands[-1]['returncode'],
                           exact_inverse=exact,
                           restored=g.artifact(restored) if restored.is_file() else None)
        g.write('completed-arms.json', dict(arms=rows, complete=False))
    supported = (rows['absent-A']['exact_inverse'] and rows['absent-B']['exact_inverse']
                 and not rows['present']['exact_inverse'])
    equal(g.work / 'absent-A/restored.raw', g.work / 'absent-B/restored.raw')
    return dict(status='passed', arms=rows, ambient_dependency_reproduced=supported,
                verdict=('Same decoder and declared assets reconstruct exactly without ambient .dict; '
                         'adding only that file changes the result.' if supported else
                         'The specified presence/absence control does not reproduce the proposed cause.'),
                correction_authorized=supported, compression_gain_claim=False)


def main():
    validate = sys.argv[1:] == ['--validate']
    assert validate or not sys.argv[1:]
    g = NativeGate(ROOT, ID, CAPS, validate_only=validate)
    if validate:
        print(json.dumps(dict(status='preflight_passed', inputs=len(g.inputs))))
        return 0
    result = dict(schema='gamma.enwiki9.ambient-dictionary-probe.v1', candidate_id=ID,
                  experiment=g.reference, objective_credit_bytes=0, raw_bytes=250000,
                  full_corpus_score_bytes=None, complete_submission_package=False)
    try:
        result.update(execute(g)); g.verify()
    except Exception as exc:
        result.update(status='execution_failed', error=str(exc),
                      failure_class=getattr(exc, 'category', 'correctness_or_evidence_failure'))
    try:
        for p in g.work.rglob('ppm.temp'):
            clean_scratch(g, p.parent, 'terminal-' + p.parent.name)
        g.closure(); g.verify(); result['child_closure_ok'] = True
    except Exception as exc:
        result.update(status='execution_failed', cleanup_error=str(exc), child_closure_ok=False)
    result['commands'] = g.commands
    g.write('artifacts.json', dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*'))
                                         if p.is_file() and p.name != 'ppm.temp'], errors=[]))
    result['artifacts'] = g.artifact(g.result / 'artifacts.json')
    g.write('decision.json', result)
    print(json.dumps({k: result[k] for k in ['status', 'error', 'verdict'] if k in result}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
