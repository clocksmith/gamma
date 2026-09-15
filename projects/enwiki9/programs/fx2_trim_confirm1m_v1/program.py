#!/usr/bin/env python3
"""Confirm frozen source trimming on an independently selected native population."""
import io
import json
from pathlib import Path
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate, require, sha
from tools.fx2_expert_release250k_v3 import equal, source_zip

ID = 'fx2_trim_confirm1m_v1'
PLAN = 'operations/provenance/' + ID + '_plan.json'
PROFILE = 'operations/provenance/fx2_kda_carry_toolchain_20260913.json'
RELEASE = 'results/fx2_expert_release250k_v3/'
ORIGINAL = 'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
RAW = 'operations/evidence/fixtures/opcode_field_confirmation1m_v1.raw'
REFERENCE = 'results/matched_frontier_reserved_q0_v1/confirmation-FX2/archive.bin'
CAPS = dict(cpus=[2], memory_bytes=9999998976, swap_bytes=0,
            scratch_bytes=16000000000, wall_seconds=3600)


class NativeGate(BaseGate):
    def verify(self):
        self.toolchain = json.loads(self.buffers[PROFILE])
        super().verify()


def members(data):
    """Only the authenticated regular-file source format is admitted."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        require(names and len(names) == len(set(names)), 'empty or duplicate source ZIP')
        result = {}
        for info in z.infolist():
            p = Path(info.filename)
            require(not p.is_absolute() and '..' not in p.parts and
                    str(p) == info.filename and not info.is_dir(), 'unsafe ZIP name')
            require(stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG), 'nonregular source')
            result[info.filename] = z.read(info)
    return result


def clean_scratch(g, native, label):
    g.closure()
    p = native / 'ppm.temp'
    row = dict(child_closure=True, present=p.exists(), content_hashed=False)
    if p.exists():
        require(p.is_file() and p.resolve() == p, 'aliased PPM scratch')
        s = p.stat()
        row.update(logical_bytes=s.st_size, allocated_bytes=s.st_blocks * 512)
        p.unlink()
    row['cleanup_complete'] = not p.exists()
    g.write(label + '-cleanup.json', row)


def execute(g):
    plan = json.loads(g.buffers[PLAN])
    require(plan['caps'] == CAPS, 'resource contract differs')
    require(len(g.buffers[RAW]) == 1000000, 'confirmation length differs')
    previous = json.loads(g.buffers[RELEASE + 'package.json'])
    original = json.loads(g.buffers[ORIGINAL + 'package.json'])
    original_binary = next(r for r in original['runtime_members'] if r['path'].endswith('/cmix'))
    archives = dict(P=RELEASE + 'original-source.zip', D=RELEASE + 'P-source.zip')
    sources = {a: members(g.buffers[p]) for a, p in archives.items()}
    require(set(sources['D']).issubset(sources['P']), 'trim unexpectedly adds source members')
    for name in ['models/6m-q4-fp32.tfwc2', 'dictionary/english.dic', 'LICENSE']:
        require(sources['P'][name] == sources['D'][name], 'paid asset or license differs')
    g.write('source-comparison.json', dict(
        removed=sorted(set(sources['P']) - set(sources['D'])),
        changed=sorted(n for n in sources['D'] if sources['P'][n] != sources['D'][n]),
        hypothesis='Previously frozen trimming only; source ZIP bytes are immutable inputs.'))
    arms, deliveries = {}, {}
    for arm in 'PD':
        native = g.work / arm
        native.mkdir()
        for name, data in sources[arm].items():
            path = native / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        source_zip(g.result / (arm + '-source.zip'), sources[arm])
        equal(g.result / (arm + '-source.zip'), ROOT / archives[arm])
        g.copy(RAW, native / 'population.raw')
        for key in ['model', 'dictionary']:
            row = previous[key]
            target = native / row['path'].split('/work/native/')[1]
            require(target.stat().st_size == row['bytes'] and
                    sha(target) == row['sha256'].removeprefix('sha256:'), 'asset differs')
        command = plan['compile_command']
        g.run(arm + '-compile', command, 360, work=native)
        first = (native / 'cmix').read_bytes()
        g.run(arm + '-clean-repeat', ['/usr/bin/make', 'clean'], 30, work=native)
        g.run(arm + '-compile-repeat', command, 360, work=native)
        require((native / 'cmix').read_bytes() == first, 'clean build repeat differs')
        expected = original_binary if arm == 'P' else previous['deliveries']['P']['binary']
        require(sha(native / 'cmix') == expected['sha256'].removeprefix('sha256:') and
                len(first) == expected['bytes'], 'frozen executable identity differs')
        binary = native / 'cmix'
        g.binaries[str(binary)] = sha(binary)
        try:
            g.run(arm + '-preprocess', [str(binary), '-s', 'dictionary/english.dic',
                                       'population.raw', 'population.stored'], 180, work=native)
        finally:
            clean_scratch(g, native, arm + '-preprocess')
        if arm == 'D':
            equal(native / 'population.stored', g.work / 'P/population.stored')
        for phase in ['encode', 'decode', 'repeat']:
            label = arm + '-' + phase
            if phase == 'decode':
                args = ['-d', 'dictionary/english.dic', 'encode.arc', 'decoded.raw']
            else:
                args = ['-c', 'dictionary/english.dic',
                        'decoded.raw' if phase == 'repeat' else 'population.raw', phase + '.arc']
            try:
                g.run(label, [str(binary), *args, '--transformer', 'models/6m-q4-fp32.tfwc2'],
                      600, work=native)
            finally:
                clean_scratch(g, native, label)
            if phase == 'decode': equal(native / 'decoded.raw', native / 'population.raw')
            if phase == 'repeat': equal(native / 'repeat.arc', native / 'encode.arc')
        equal(native / 'encode.arc', ROOT / REFERENCE)
        arc = native / 'encode.arc'
        arms[arm] = dict(archive=g.artifact(arc), archive_bytes=arc.stat().st_size,
                         restored=g.artifact(native / 'decoded.raw'),
                         repeat=g.artifact(native / 'repeat.arc'),
                         stored=g.artifact(native / 'population.stored'),
                         independent_inverse=True, archive_repeat_byte_equal=True,
                         retained_parent_archive_byte_equal=True)
        deliveries[arm] = dict(binary=g.artifact(binary), source_zip=g.artifact(g.result / (arm + '-source.zip')),
                               source_members=len(sources[arm]),
                               compile_command=command, clean_build_repeat_byte_equal=True)
        g.write('completed-arms.json', dict(arms=arms, deliveries=deliveries, complete=False))
    equal(g.work / 'P/encode.arc', g.work / 'D/encode.arc')
    gain = arms['P']['archive_bytes'] - arms['D']['archive_bytes']
    source_gain = deliveries['P']['source_zip']['bytes'] - deliveries['D']['source_zip']['bytes']
    binary_gain = deliveries['P']['binary']['bytes'] - deliveries['D']['binary']['bytes']
    require(gain == 0 and source_gain == 5348 and binary_gain == 45056, 'frozen component comparison differs')
    g.write('package.json', dict(deliveries=deliveries, model=previous['model'], dictionary=previous['dictionary'],
                                 source_component_reduction_bytes=source_gain,
                                 executable_component_reduction_bytes=binary_gain,
                                 extra_required_options_bytes=0, complete_submission_package=False,
                                 complete_package_bytes=None, unresolved=previous['unresolved'],
                                 boundary='Source ZIP and executable prices are alternatives. Official multiplicities, runtime, license/notice and option closure remain unresolved. Shared models and dictionary are not free.'))
    return dict(arms=arms, archive_gain_bytes=gain, source_component_gain_bytes=source_gain,
                executable_component_gain_bytes=binary_gain, all_archives_identical=True,
                preprocessing_identical=True, all_builds_frozen_and_repeated=True,
                release_confirmation_pass=True,
                state_evidence='Independent native inverses/repeats and full archive identity. No internal probability or optimizer state is serialized; equivalence beyond this population is not empirically asserted.',
                verdict='Frozen trimming transfers to this cold reserved1MB with exact native archives and unchanged component savings; full package and full corpus remain unproved.')


def main():
    validate = sys.argv[1:] == ['--validate']
    require(validate or not sys.argv[1:], 'unsupported arguments')
    g = NativeGate(ROOT, ID, CAPS, validate_only=validate)
    if validate:
        print(json.dumps(dict(status='preflight_passed', inputs=len(g.inputs))))
        return 0
    result = dict(schema='gamma.enwiki9.trim-confirmation.v1', candidate_id=ID, experiment=g.reference,
                  raw_bytes=1000000, raw_population='[713000000,714000000)', initialization='cold',
                  prior_exposure='Previously tested by native FX2 and opcode baselines; not globally unseen. Not used to select or tune the frozen trimming.',
                  objective_credit_bytes=0, complete_package_bytes=None, full_corpus_score_bytes=None,
                  larger_gate_authorized=False)
    try:
        result.update(execute(g), status='passed')
        g.verify()
    except Exception as e:
        result.update(status='execution_failed', failure_class=getattr(e, 'category', 'correctness_or_evidence_failure'),
                      error=str(e), verdict='Incomplete release confirmation; preserve completed measurements.')
    try:
        for arm in 'PD': clean_scratch(g, g.work / arm, 'terminal-' + arm)
        g.verify()
        result['child_closure_ok'] = True
    except Exception as e:
        result.update(status='execution_failed', cleanup_error=str(e), child_closure_ok=False)
    result['commands'] = g.commands
    g.write('artifacts.json', dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*'))
                                         if p.is_file() and p.name != 'ppm.temp'], errors=[]))
    result['artifacts'] = g.artifact(g.result / 'artifacts.json')
    g.write('decision.json', result)
    print(json.dumps({k: result[k] for k in ['status', 'verdict', 'archive_gain_bytes', 'error'] if k in result}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
