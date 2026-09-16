#!/usr/bin/env python3
"""Confirm the unchanged released mixture on the reserved native one-million-byte population."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate, require, sha
from tools.fx2_expert_release250k_v3 import equal, source_zip
from tools.fx2_trim_confirm1m_v1 import members, clean_scratch

ID = 'fx2_expert_confirm1m_v1'
PLAN = 'operations/provenance/' + ID + '_plan.json'
PROFILE = 'operations/provenance/fx2_kda_carry_toolchain_20260913.json'
RELEASE = 'results/fx2_expert_release250k_v3/'
RAW = 'operations/evidence/fixtures/opcode_field_confirmation1m_v1.raw'
STORED = 'results/fx2_trim_confirm1m_v1/work/D/population.stored'
REFERENCE = 'results/matched_frontier_reserved_q0_v1/confirmation-FX2/archive.bin'
CAPS = dict(cpus=[2], memory_bytes=9999998976, swap_bytes=0,
            scratch_bytes=16000000000, wall_seconds=3600)


class NativeGate(BaseGate):
    def verify(self):
        self.toolchain = json.loads(self.buffers[PROFILE])
        super().verify()


def execute(g):
    plan = json.loads(g.buffers[PLAN])
    require(plan['caps'] == CAPS, 'resource contract differs')
    require(len(g.buffers[RAW]) == 1000000, 'confirmation population length differs')
    package = json.loads(g.buffers[RELEASE + 'package.json'])
    sources = {a: members(g.buffers[RELEASE + a + '-source.zip']) for a in 'PD'}
    require(set(sources['D']) - set(sources['P']) == {'src/gamma-expert-release.h'}
            and set(sources['P']).issubset(sources['D']), 'released member delta differs')
    require(all(sources['P'][p] == sources['D'][p] for p in sources['P']),
            'released shared source or paid assets differ')
    arms, deliveries = {}, {}
    for arm in 'PD':
        native = g.work / arm
        native.mkdir()
        for name, data in sources[arm].items():
            p = native / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        source_zip(g.result / (arm + '-source.zip'), sources[arm])
        equal(g.result / (arm + '-source.zip'), ROOT / (RELEASE + arm + '-source.zip'))
        g.copy(RAW, native / 'population.raw')
        command = plan['compile_commands'][arm]
        require(command == package['deliveries'][arm]['compile_command'],
                'released compile command differs')
        g.run(arm + '-compile', command, 360, work=native)
        first = (native / 'cmix').read_bytes()
        g.run(arm + '-clean-repeat', ['/usr/bin/make', 'clean'], 30, work=native)
        g.run(arm + '-compile-repeat', command, 360, work=native)
        require((native / 'cmix').read_bytes() == first, 'clean builds differ')
        expected = package['deliveries'][arm]['binary']
        binary = native / 'cmix'
        require(sha(binary) == expected['sha256'].removeprefix('sha256:') and
                len(first) == expected['bytes'], 'released executable identity differs')
        g.binaries[str(binary)] = sha(binary)
        try:
            g.run(arm + '-preprocess', [str(binary), '-s', 'dictionary/english.dic',
                  'population.raw', 'population.stored'], 180, work=native)
        finally:
            clean_scratch(g, native, arm + '-preprocess')
        equal(native / 'population.stored', ROOT / STORED)
        for phase in ['encode', 'decode', 'repeat']:
            label = arm + '-' + phase
            args = (['-d', 'dictionary/english.dic', 'encode.arc', 'restored.raw']
                    if phase == 'decode' else ['-c', 'dictionary/english.dic',
                    'restored.raw' if phase == 'repeat' else 'population.raw', phase + '.arc'])
            try:
                g.run(label, [str(binary), *args, '--transformer',
                      'models/6m-q4-fp32.tfwc2'], 600, work=native)
            finally:
                clean_scratch(g, native, label)
            if phase == 'decode': equal(native / 'restored.raw', native / 'population.raw')
            if phase == 'repeat': equal(native / 'repeat.arc', native / 'encode.arc')
        if arm == 'P': equal(native / 'encode.arc', ROOT / REFERENCE)
        arms[arm] = dict(archive=g.artifact(native / 'encode.arc'),
            archive_bytes=(native / 'encode.arc').stat().st_size,
            restored=g.artifact(native / 'restored.raw'),
            repeat=g.artifact(native / 'repeat.arc'),
            stored=g.artifact(native / 'population.stored'),
            exact_inverse=True, archive_repeat_byte_equal=True)
        deliveries[arm] = dict(binary=g.artifact(binary),
            source_zip=g.artifact(g.result / (arm + '-source.zip')),
            clean_build_repeat_identical=True, released_binary_identical=True,
            compile_command=command)
        g.write('completed-arms.json', dict(arms=arms, deliveries=deliveries, complete=False))
    require(len(g.commands) == 14, 'phase count differs')
    gain = arms['P']['archive_bytes'] - arms['D']['archive_bytes']
    dz = deliveries['D']['source_zip']['bytes'] - deliveries['P']['source_zip']['bytes']
    db = deliveries['D']['binary']['bytes'] - deliveries['P']['binary']['bytes']
    require((dz, db, package['compile_option_increment_bytes']) == (1167, 4096, 21),
            'frozen component economics changed')
    g.write('package.json', dict(deliveries=deliveries, model=package['model'],
        dictionary=package['dictionary'], source_zip_increment_bytes=dz,
        binary_increment_bytes=db, compile_option_increment_bytes=21,
        source_form_increment_bytes=1188, complete_package_bytes=None,
        complete_submission_package=False, unresolved=package['unresolved'],
        boundary='Existing paid-component hold remains. Source ZIP plus required compile option and executable are alternative forms; no inherited trimming or full-corpus gain.'))
    return dict(status='passed', arms=arms, g_P=gain,
        source_component_net_bytes=gain-1188, binary_component_net_bytes=gain-db,
        predictive_transfer_pass=gain > 0, source_component_gate_pass=gain > 1188,
        package_hold_preserved=True,
        state_evidence='Fresh native inverses/repeats, immutable released executable identity and retained parent archive identity. Development P/K/S state controls are inherited evidence, not rerun or claimed on this population.',
        verdict=('The unchanged mixture pays the measured source-and-option increment on this cold1MB sample; consider a separately admitted10MB comparison while complete package closure remains unresolved.' if gain > 1188 else
                 'Positive archive transfer on cold1MB, but the measured source-and-option increment remains unpaid; hold unchanged implementation without automatic scale.' if gain > 0 else
                 'The unchanged mixture does not improve this cold1MB population; retire this fixed confirmation configuration without tuning or population rescue.'))


def main():
    validate = sys.argv[1:] == ['--validate']
    require(validate or not sys.argv[1:], 'unsupported arguments')
    g = NativeGate(ROOT, ID, CAPS, validate_only=validate)
    if validate:
        print(json.dumps(dict(status='preflight_passed', inputs=len(g.inputs))))
        return 0
    result = dict(schema='gamma.enwiki9.expert-confirm-native.v1', candidate_id=ID,
        experiment=g.reference, raw_bytes=1000000, raw_population='[713000000,714000000)',
        initialization='cold', prior_exposure='Previously tested by native FX2, opcode baselines and trim confirmation; not used to fit or select this expert mixture. Not globally untouched.',
        complete_package_bytes=None, full_corpus_score_bytes=None,
        objective_credit_bytes=0, larger_gate_authorized=False)
    try:
        result.update(execute(g)); g.verify()
    except Exception as exc:
        result.update(status='execution_failed', failure_class=getattr(exc, 'category', 'correctness_or_evidence_failure'),
                      error=str(exc), verdict='Incomplete comparison; preserve completed observations without a compression inference.')
    try:
        for arm in 'PD': clean_scratch(g, g.work / arm, 'terminal-' + arm)
        g.closure(); g.verify(); result['child_closure_ok'] = True
    except Exception as exc:
        result.update(status='execution_failed', cleanup_error=str(exc), child_closure_ok=False)
    result['commands'] = g.commands
    g.write('artifacts.json', dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*'))
        if p.is_file() and p.name != 'ppm.temp'], errors=[]))
    result['artifacts'] = g.artifact(g.result / 'artifacts.json')
    g.write('decision.json', result)
    print(json.dumps({k: result[k] for k in ['status', 'g_P', 'error', 'verdict'] if k in result}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
