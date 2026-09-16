#!/usr/bin/env python3
"""One native test of an online correction trained on final coded-bit residuals."""
import io
import json
import math
from pathlib import Path
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate, require, sha

ID = 'fx2_final_bit_head250k_v1'
PLAN = 'operations/provenance/' + ID + '_plan.json'
ADAPTER = 'operations/provenance/fx2_final_bit_head_adapter_v1.json'
RELEASE = 'results/fx2_expert_release250k_v3/'
ZIP = RELEASE + 'P-source.zip'
PROFILE = 'operations/provenance/fx2_kda_carry_toolchain_20260913.json'
FIXTURE = 'results/fx2_weight_native_transfer250k_q0_v1/'
RAW = FIXTURE + 'work/native/opening.raw'
STORED = FIXTURE + 'work/native/opening.stored'
ARCHIVE = FIXTURE + 'opening/P/archive.bin'
TRACE = FIXTURE + 'work/native/opening-P-encode.trace'
N = 151210
STATE_RECORD = 393267
CAPS = dict(cpus=[2], memory_bytes=9999998976, swap_bytes=0,
            scratch_bytes=16000000000, wall_seconds=3600)


class NativeGate(BaseGate):
    def verify(self):
        self.toolchain = json.loads(self.buffers[PROFILE])
        super().verify()


def equal(a, b):
    require(a.stat().st_size == b.stat().st_size, 'different sizes: ' + str(a))
    with a.open('rb') as x, b.open('rb') as y:
        while block := x.read(1 << 20):
            require(block == y.read(len(block)), 'different bytes: ' + str(a))


def cleanup(g, label):
    g.closure()
    path = g.work / 'native/ppm.temp'
    row = dict(present=path.exists(), content_hashed=False)
    if path.exists():
        require(path.resolve() == path and path.is_file(), 'transient alias')
        s = path.stat()
        row.update(logical_bytes=s.st_size, allocated_bytes=s.st_blocks * 512)
        path.unlink()
    row['cleanup_complete'] = not path.exists()
    g.write(label + '-cleanup.json', row)


def states(path):
    size = path.stat().st_size
    require(size == (N // 2048 + 1) * STATE_RECORD, 'state population differs')
    with path.open('rb') as f:
        for i in range(size // STATE_RECORD):
            row = f.read(STATE_RECORD)
            pos, predictions, updates, resets = struct.unpack_from('<4Q', row)
            prefix, previous, parent, candidate = struct.unpack_from('<4I', row, 32)
            require(pos == min((i + 1) * 16384, N * 8) and predictions == pos,
                    'head clock differs')
            require(updates <= pos and resets <= N and prefix == 1 and previous < 256,
                    'head state invalid')
            require(0 < parent < 65536 and 0 < candidate < 65536 and row[50] == 0,
                    'invalid boundary probabilities')
            values = struct.unpack_from('<49152d', row, 51)
            require(all(map(math.isfinite, values)), 'nonfinite introduced state')
            require(sum(x*x for x in values[:192]) <= 1.00000001, 'feature norm')
            for start in range(192, len(values), 192):
                require(sum(x*x for x in values[start:start+192]) <= 16.00000001,
                        'row norm')
    return size // STATE_RECORD


def base_state(path):
    raw = path.read_bytes()
    require(raw and len(raw) % 40 == 0, 'base digest framing')
    last = struct.unpack_from('<Q', raw, len(raw) - 40)[0]
    require(N // 2 < last <= N, 'base feature coverage')
    for i in range(len(raw) // 40):
        require(struct.unpack_from('<Q', raw, i*40)[0] == min((i+1)*1024, last),
                'base digest clock')
    require(len(raw) // 40 == (last+1023)//1024, 'base digest count')
    return last


def parent_trajectory(a, b):
    with a.open('rb') as x, b.open('rb') as y:
        while block := x.read(28 * 8192):
            other = y.read(len(block))
            require(len(other) == len(block), 'trajectory length')
            for u, v in zip(struct.iter_unpack('<7I', block), struct.iter_unpack('<7I', other)):
                require(u[0] == v[0] and u[6] == v[6], 'original probability/truth changed')
        require(not y.read(1), 'extra trajectory')


def source_zip(path, members):
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data, compresslevel=9)


def execute(g):
    plan = json.loads(g.buffers[PLAN])
    require(plan['caps'] == CAPS, 'resource contract differs')
    require(len(g.buffers[RAW]) == 250000 and len(g.buffers[STORED]) == N + 10,
            'population differs')
    native = g.work / 'native'
    native.mkdir()
    with zipfile.ZipFile(io.BytesIO(g.buffers[ZIP])) as z:
        names = z.namelist()
        require(len(names) == len(set(names)) == 127, 'source ZIP population')
        original = {name: z.read(name) for name in names}
    for name, data in original.items():
        p = Path(name)
        require(not p.is_absolute() and '..' not in p.parts and not name.endswith('/'),
                'unsafe source name')
        target = native / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    g.adapter(ADAPTER, native)
    adapter = json.loads(g.buffers[ADAPTER])
    for row in adapter['added_files']:
        g.copy(row['source']['path'], native / row['target'])
    changed = {name: (native / name).read_bytes() for name in original}
    changed.update({r['target']: (native / r['target']).read_bytes() for r in adapter['added_files']})
    for arm, members in [('P', original), ('D', changed)]:
        source_zip(g.result / (arm+'-source.zip'), members)
        source_zip(g.result / (arm+'-source-repeat.zip'), members)
        equal(g.result / (arm+'-source.zip'), g.result / (arm+'-source-repeat.zip'))
    g.copy(RAW, native / 'population.raw')
    command = plan['compile_command']
    g.run('compile', command, 360, work=native)
    first = sha(native / 'cmix')
    (g.work / 'cmix.first').write_bytes((native / 'cmix').read_bytes())
    g.run('clean-repeat', ['/usr/bin/make', 'clean'], 30, work=native)
    g.run('compile-repeat', command, 360, work=native)
    require(sha(native / 'cmix') == first, 'clean build repeat differs')
    g.binaries[str(native / 'cmix')] = first
    released = json.loads(g.buffers[RELEASE+'package.json'])
    delta = (g.result / 'D-source.zip').stat().st_size - (g.result / 'P-source.zip').stat().st_size
    option = 'GAMMA_FX2_FINAL_BIT_ARM=D'
    binary_delta = (native / 'cmix').stat().st_size - released['deliveries']['P']['binary']['bytes']
    package = dict(source_zip_increment_bytes=delta, option_increment_bytes=len(option),
                   binary_increment_bytes=binary_delta, source_and_option_increment_bytes=delta+len(option),
                   source_zip_repeats_exact=True, clean_build_repeat_exact=True,
                   observer_included=True, alternative_forms_not_added=True,
                   complete_package_bytes=None, objective_credit_bytes=0,
                   unresolved=released['unresolved'], option_text=option,
                   source_zips={a:g.artifact(g.result / (a+'-source.zip')) for a in 'PD'},
                   binary=g.artifact(native/'cmix'))
    require(delta+len(option) <= 65536, 'component budget exceeded')
    g.write('package.json', package)
    env_arm = lambda arm: dict(GAMMA_FX2_FINAL_BIT_ARM=arm)
    try:
        g.run('preprocess', [str(native/'cmix'), '-s', 'dictionary/english.dic',
                            'population.raw', 'population.stored'], 180,
              env=env_arm('P'), work=native)
        equal(native/'population.stored', ROOT/STORED)
    finally:
        cleanup(g, 'preprocess')
    arms = {}
    for arm in 'PKDS':
        for phase in ('encode', 'decode', 'repeat'):
            name = arm+'-'+phase
            if phase == 'decode':
                args = ['-d', 'dictionary/english.dic', arm+'-encode.arc', arm+'-decode.raw']
            else:
                args = ['-c', 'dictionary/english.dic',
                        arm+'-decode.raw' if phase == 'repeat' else 'population.raw', name+'.arc']
            env = dict(**env_arm(arm), GAMMA_FX2_CODER_TRACE=str(native/(name+'.coder')),
                       GAMMA_FX2_FINAL_BIT_STATE=str(native/(name+'.state')),
                       GAMMA_FX2_FINAL_BIT_BASE=str(native/(name+'.base')))
            try:
                g.run(name, [str(native/'cmix'), *args, '--transformer', 'models/6m-q4-fp32.tfwc2'],
                      300, env=env, work=native)
            finally:
                cleanup(g, name)
            require((native/(name+'.coder')).stat().st_size == N*8*28, 'coder population')
            state_count = states(native/(name+'.state'))
            feature_count = base_state(native/(name+'.base'))
            if phase != 'encode':
                for suffix in ('.coder', '.state', '.base'):
                    equal(native/(arm+'-encode'+suffix), native/(name+suffix))
                equal(native/(arm+'-decode.raw') if phase == 'decode' else native/(name+'.arc'),
                      native/'population.raw' if phase == 'decode' else native/(arm+'-encode.arc'))
        arms[arm] = dict(archive_bytes=(native/(arm+'-encode.arc')).stat().st_size,
                         archive=g.artifact(native/(arm+'-encode.arc')),
                         repeat=g.artifact(native/(arm+'-repeat.arc')),
                         restored=g.artifact(native/(arm+'-decode.raw')),
                         exact_inverse=True, repeat_byte_identical=True,
                         state_boundaries=state_count, feature_predictions=feature_count)
        equal(native/(arm+'-encode.base'), native/'P-encode.base')
        parent_trajectory(native/(arm+'-encode.coder'), ROOT/TRACE)
    equal(native/'P-encode.arc', ROOT/ARCHIVE)
    equal(native/'P-encode.coder', ROOT/TRACE)
    equal(native/'P-encode.arc', native/'K-encode.arc')
    equal(native/'K-encode.state', native/'D-encode.state')
    try:
        g.run('D-untraced', [str(native/'cmix'), '-c', 'dictionary/english.dic',
                            'population.raw', 'D-untraced.arc', '--transformer', 'models/6m-q4-fp32.tfwc2'],
              300, env=env_arm('D'), work=native)
        equal(native/'D-untraced.arc', native/'D-encode.arc')
    finally:
        cleanup(g, 'D-untraced')
    gp = arms['P']['archive_bytes'] - arms['D']['archive_bytes']
    gs = arms['S']['archive_bytes'] - arms['D']['archive_bytes']
    net = gp - package['source_and_option_increment_bytes']
    verdict = ('Retire fixed final-bit learner: required archive/control separation failed.'
               if gp <= 0 or gs <= 0 else
               'Hold positive archive/control result: measured source component remains unpaid.'
               if net <= 0 else 'Paid source-component gain; consider frozen confirmation, no full score.')
    return dict(arms=arms, g_P=gp, g_S=gs, source_component_net_bytes=net,
                binary_component_net_bytes=gp-binary_delta-len(option),
                scientific_verdict=verdict, source_component_gate_pass=gp>0 and gs>0 and net>0,
                PK_archive_identity=True, KD_introduced_state_identity=True,
                protected_parent_probability_truth_identity=True, frozen_hidden_logit_digests_equal=True,
                D_trace_on_off_identity=True, original_model_state_serialized=False)


def main():
    validate = sys.argv[1:] == ['--validate']
    require(not sys.argv[1:] or validate, 'unsupported arguments')
    g = NativeGate(ROOT, ID, CAPS, validate_only=validate)
    if validate:
        print(json.dumps(dict(status='preflight_passed', inputs=len(g.inputs))))
        return 0
    result = dict(schema='gamma.enwiki9.final-bit-head-terminal.v1', candidate_id=ID,
                  experiment=g.reference, raw_population='[0,250000)', raw_bytes=250000,
                  complete_package_bytes=None, full_corpus_score_bytes=None,
                  objective_credit_bytes=0, larger_gate_authorized=False)
    try:
        result.update(execute(g), status='passed')
        g.verify()
    except Exception as e:
        result.update(status='execution_failed', error=str(e),
                      failure_class=getattr(e, 'category', 'correctness_or_evidence_failure'),
                      scientific_verdict='Incomplete execution; no compression verdict.')
    try:
        cleanup(g, 'terminal'); g.verify(); result['child_closure_ok'] = True
    except Exception as e:
        result.update(status='execution_failed', cleanup_error=str(e), child_closure_ok=False)
    result['commands'] = g.commands
    g.write('artifacts.json', dict(files=[g.artifact(p) for p in sorted(g.result.rglob('*'))
                                        if p.is_file() and p.name != 'ppm.temp'], errors=[]))
    result['artifacts'] = g.artifact(g.result/'artifacts.json')
    g.write('decision.json', result)
    print(json.dumps({k:result[k] for k in ('status','scientific_verdict','g_P','g_S','error') if k in result}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
