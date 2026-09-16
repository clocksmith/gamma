#!/usr/bin/env python3
"""Bound native P/K/D/S archives for the fixed value-feedback realization."""
import io
import json
from pathlib import Path
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate, require, sha
from lib.fx2_value_feedback_native_v1 import materialize
from lib.fx2_value_feedback_evidence_v1 import observe_sources, residual_stream, pack_stream
from tools.fx2_expert_release250k_v3 import source_zip, equal

ID = 'fx2_value_feedback250k_v1'
PLAN = 'operations/provenance/' + ID + '_plan.json'
PROFILE = 'operations/provenance/fx2_kda_carry_toolchain_20260913.json'
RELEASE = 'results/fx2_expert_release250k_v3/'
ZIP = RELEASE + 'P-source.zip'
DELIVERY = 'results/fx2_value_feedback_native_preflight_v1/delivery/'
FIXTURE = 'results/fx2_weight_native_transfer250k_q0_v1/'
RAW = FIXTURE + 'work/native/opening.raw'
STORED = FIXTURE + 'work/native/opening.stored'
ARCHIVE = FIXTURE + 'opening/P/archive.bin'
CODER_ADAPTER = 'operations/provenance/fx2_value_feedback_coder_adapter_v1.json'
N = 151210
CAPS = dict(cpus=[2], memory_bytes=9999998976, swap_bytes=0,
            scratch_bytes=20000000000, wall_seconds=7200)


class NativeGate(BaseGate):
    def verify(self):
        self.toolchain = json.loads(self.buffers[PROFILE])
        super().verify()


def source_members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        require(names and len(names) == len(set(names)), 'duplicate or empty source ZIP')
        result = {}
        for info in z.infolist():
            p = Path(info.filename)
            require(not p.is_absolute() and '..' not in p.parts and str(p) == info.filename
                    and not info.is_dir(), 'unsafe source name')
            require(stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG), 'nonregular source')
            result[info.filename] = z.read(info)
        return result


def cleanup(g, native, label):
    g.closure()
    path = native / 'ppm.temp'
    row = dict(children_closed=True, present=path.exists(), content_hashed=False)
    if path.exists():
        require(path.is_file() and path.resolve() == path, 'aliased PPM scratch')
        s = path.stat()
        row.update(logical_bytes=s.st_size, allocated_bytes=s.st_blocks * 512)
        path.unlink()
    row['cleanup_complete'] = not path.exists()
    g.write(label + '-cleanup.json', row)


def write_sources(native, source, previous):
    for name in set(previous) - set(source):
        (native / name).unlink()
    for name, content in source.items():
        path = native / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def execute(g):
    plan = json.loads(g.buffers[PLAN])
    require(plan['caps'] == CAPS, 'resource contract differs')
    require(len(g.buffers[RAW]) == 250000 and len(g.buffers[STORED]) == N + 10,
            'population length differs')
    base = source_members(g.buffers[ZIP])
    native = g.work / 'native'
    native.mkdir()
    g.copy(RAW, native / 'population.raw')
    header = g.buffers['lib/fx2_value_feedback_v1.h']
    observer = g.buffers['lib/fx2_value_feedback_observer_v1.h']
    coder_header = g.buffers['tools/fx2_coder_trace_v1.hpp']
    adapter = json.loads(g.buffers[CODER_ADAPTER])
    parent_package = json.loads(g.buffers[RELEASE + 'package.json'])
    previous = {}
    arms, deliveries, state_rows = {}, {}, {}
    for arm in 'PKDS':
        source = materialize(base, arm, header)
        source_zip(g.result / (arm + '-source.zip'), source)
        equal(g.result / (arm + '-source.zip'), ROOT / (DELIVERY + arm + '-source.zip'))
        if arm == 'P': equal(g.result / 'P-source.zip', ROOT / ZIP)
        else: require((g.result / (arm + '-source.zip')).stat().st_size - len(g.buffers[ZIP]) == 1498,
                      'frozen source-component price differs')
        write_sources(native, source, previous)
        previous = source
        if arm != 'P': g.run(arm + '-clean-source', ['/usr/bin/make', 'clean'], 30, work=native)
        g.run(arm + '-compile', plan['compile_command'], 360, work=native)
        first = (native / 'cmix').read_bytes()
        g.run(arm + '-clean-repeat', ['/usr/bin/make', 'clean'], 30, work=native)
        g.run(arm + '-compile-repeat', plan['compile_command'], 360, work=native)
        require((native / 'cmix').read_bytes() == first, 'clean build differs')
        binary = native / ('delivery-' + arm)
        binary.write_bytes(first); binary.chmod(0o755)
        g.binaries[str(binary)] = sha(binary)
        if arm == 'P':
            expected = parent_package['deliveries']['P']['binary']
            require(sha(binary) == expected['sha256'].removeprefix('sha256:') and
                    binary.stat().st_size == expected['bytes'], 'parent executable differs')
            try:
                g.run('P-preprocess', [str(binary), '-s', 'dictionary/english.dic',
                      'population.raw', 'population.stored'], 180, work=native)
            finally: cleanup(g, native, 'P-preprocess')
            equal(native / 'population.stored', ROOT / STORED)
        for phase in ('clean-encode', 'clean-decode'):
            label = arm + '-' + phase
            args = (['-c', 'dictionary/english.dic', 'population.raw', label + '.arc']
                    if phase == 'clean-encode' else
                    ['-d', 'dictionary/english.dic', arm + '-clean-encode.arc', label + '.raw'])
            try:
                g.run(label, [str(binary), *args, '--transformer',
                      'models/6m-q4-fp32.tfwc2'], 300, work=native)
            finally: cleanup(g, native, label)
            if phase == 'clean-decode': equal(native / (label + '.raw'), native / 'population.raw')
        observed = observe_sources(source, arm, adapter, coder_header, observer)
        write_sources(native, observed, previous); previous = observed
        g.run(arm + '-clean-observer', ['/usr/bin/make', 'clean'], 30, work=native)
        g.run(arm + '-compile-observer', plan['compile_command'], 360, work=native)
        traced = native / ('observed-' + arm)
        traced.write_bytes((native / 'cmix').read_bytes()); traced.chmod(0o755)
        g.binaries[str(traced)] = sha(traced)
        for phase in ('encode', 'decode', 'repeat'):
            label = arm + '-' + phase
            args = (['-d', 'dictionary/english.dic', arm + '-encode.arc', label + '.raw']
                    if phase == 'decode' else ['-c', 'dictionary/english.dic',
                    arm + '-decode.raw' if phase == 'repeat' else 'population.raw', label + '.arc'])
            env = {'GAMMA_FX2_CODER_TRACE': str(native / (label + '.coder'))}
            if arm != 'P': env['GAMMA_VALUE_FEEDBACK_TRACE'] = str(native / (label + '.residual'))
            try:
                g.run(label, [str(traced), *args, '--transformer',
                      'models/6m-q4-fp32.tfwc2'], 300, env=env, work=native)
            finally: cleanup(g, native, label)
            if phase == 'decode': equal(native / (label + '.raw'), native / 'population.raw')
            else: equal(native / (label + '.arc'), native / (arm + '-clean-encode.arc'))
            require((native / (label + '.coder')).stat().st_size == N * 8 * 28,
                    'coder trace population differs')
            if arm != 'P':
                state_rows[label] = residual_stream(native / (label + '.residual'))
                require(state_rows[label]['tokens'] <= N and state_rows[label]['nonzero_residuals'] > 0,
                        'residual observer inactive or oversized')
            if phase != 'encode':
                equal(native / (label + '.coder'), native / (arm + '-encode.coder'))
                if arm != 'P':
                    equal(native / (label + '.residual'), native / (arm + '-encode.residual'))
                    require(state_rows[label] == state_rows[arm + '-encode'], 'state rows differ')
        if arm == 'P': equal(native / 'P-clean-encode.arc', ROOT / ARCHIVE)
        if arm == 'K':
            equal(native / 'K-encode.arc', native / 'P-encode.arc')
            equal(native / 'K-encode.coder', native / 'P-encode.coder')
        if arm in 'DS':
            require(state_rows[arm + '-encode']['tokens'] == state_rows['K-encode']['tokens'] and
                    state_rows[arm + '-encode']['resets'] == state_rows['K-encode']['resets'],
                    'feedback visit/reset population differs')
        residual_manifest = None
        if arm != 'P':
            raw_state = native / (arm + '-encode.residual')
            residual_manifest = pack_stream(raw_state, g.result / (arm + '-residual-stream'))
            preservation = dict(manifest=g.artifact(residual_manifest), phases={})
            for phase in ('encode', 'decode', 'repeat'):
                path = native / (arm + '-' + phase + '.residual')
                preservation['phases'][phase] = g.artifact(path)
            require(len({r['sha256'] for r in preservation['phases'].values()}) == 1,
                    'residual preservation identities differ')
            g.write(arm + '-residual-preservation.json', preservation)
            # Exact chunk inversion preserves every original diagnostic byte.
            for phase in ('encode', 'decode', 'repeat'):
                (native / (arm + '-' + phase + '.residual')).unlink()
        arms[arm] = dict(archive=g.artifact(native / (arm + '-clean-encode.arc')),
            archive_bytes=(native / (arm + '-clean-encode.arc')).stat().st_size,
            restored=g.artifact(native / (arm + '-clean-decode.raw')),
            observed_archive=g.artifact(native / (arm + '-encode.arc')),
            observed_restored=g.artifact(native / (arm + '-decode.raw')),
            repeat=g.artifact(native / (arm + '-repeat.arc')),
            coder=g.artifact(native / (arm + '-encode.coder')),
            residual=g.artifact(residual_manifest) if arm != 'P' else None,
            exact_inverse=True, repeat_identity=True, observed_delivery_identity=True,
            coder_encode_decode_repeat_identity=True,
            residual_encode_decode_repeat_identity=arm != 'P')
        deliveries[arm] = dict(binary=g.artifact(binary), source_zip=g.artifact(g.result / (arm + '-source.zip')),
            clean_build_repeat=True, source_members=len(source))
        g.write('completed-arms.json', dict(arms=arms, deliveries=deliveries, complete=False))
    gp = arms['P']['archive_bytes'] - arms['D']['archive_bytes']
    gs = arms['S']['archive_bytes'] - arms['D']['archive_bytes']
    dz = deliveries['D']['source_zip']['bytes'] - deliveries['P']['source_zip']['bytes']
    db = deliveries['D']['binary']['bytes'] - deliveries['P']['binary']['bytes']
    prices = dict(deliveries=deliveries, source_zip_increment_bytes=dz, binary_increment_bytes=db,
        unchanged_paid_model=g.artifact(native / 'models/6m-q4-fp32.tfwc2'),
        unchanged_dictionary=g.artifact(native / 'dictionary/english.dic'),
        additional_required_options_bytes=0, complete_submission_package=False,
        complete_package_bytes=None, unresolved=parent_package['unresolved'],
        boundary='Only delivered clean binaries and source ZIPs are component prices, as alternatives. Observation sources/files are test-only; exact delivered/observed archive and inverse checks justify their exclusion. Official form, runtime and multiplicities remain unresolved.')
    g.write('package.json', prices); g.write('residual-summary.json', state_rows)
    return dict(arms=arms, g_P=gp, g_S=gs, source_zip_increment_bytes=dz,
        binary_increment_bytes=db, source_component_net_bytes=gp-dz,
        binary_component_net_bytes=gp-db, PK_coder_and_archive_identity=True,
        parent_archive_and_delivery_identity=True,
        confirmation_authorized=gp > 0 and gs > 0 and max(dz, db) <= 65536,
        state_boundary='All feedback residuals/reset boundaries and final coder float/count/interval/truth records match within each arm. P/K coder records match. Full parent/optimizer memory is not serialized; D/S downstream trajectories intentionally differ from P.',
        scientific_verdict='Positive native parent/control separation authorizes unchanged reserved confirmation with package costs retained.' if gp > 0 and gs > 0 and max(dz, db) <= 65536 else 'This fixed feedback realization does not pass the native parent/control archive and component-ceiling comparison.')


def main():
    validate = sys.argv[1:] == ['--validate']
    require(validate or not sys.argv[1:], 'unsupported arguments')
    g = NativeGate(ROOT, ID, CAPS, validate_only=validate)
    if validate:
        print(json.dumps(dict(status='preflight_passed', inputs=len(g.inputs)))); return 0
    result = dict(schema='gamma.enwiki9.value-feedback-terminal.v1', candidate_id=ID,
        experiment=g.reference, raw_population='[0,250000)', raw_bytes=250000,
        complete_package_bytes=None, full_corpus_score_bytes=None,
        objective_credit_bytes=0, larger_gate_authorized=False)
    try: result.update(execute(g), status='passed'); g.verify()
    except Exception as e:
        result.update(status='execution_failed', failure_class=getattr(e, 'category', 'correctness_or_evidence_failure'),
                      error=str(e), scientific_verdict='Incomplete comparison; preserve valid completed observations.')
    try: cleanup(g, g.work / 'native', 'terminal'); g.verify(); result['child_closure_ok'] = True
    except Exception as e: result.update(status='execution_failed', cleanup_error=str(e), child_closure_ok=False)
    result['commands'] = g.commands
    g.write('artifacts.json', dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*'))
        if p.is_file() and p.name != 'ppm.temp'], errors=[]))
    result['artifacts'] = g.artifact(g.result / 'artifacts.json')
    g.write('decision.json', result)
    print(json.dumps({k: result[k] for k in ('status', 'g_P', 'g_S', 'scientific_verdict', 'error') if k in result}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__': raise SystemExit(main())
