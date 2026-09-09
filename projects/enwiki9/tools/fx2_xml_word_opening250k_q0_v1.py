#!/usr/bin/env python3
"""Bounded native XML word-context comparison on the retained opening250KB."""
import hashlib
import json
from pathlib import Path
import re
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate as BaseGate, require, sha
from lib.native_trace_cache_v1 import release_closed_file, memory_snapshot
from lib import driver

ID = 'fx2_xml_word_opening250k_q0_v1'
PLAN = 'operations/provenance/' + ID + '_plan.json'
PARENT = 'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
ADAPTER = 'results/fx2_xml_word_context_v1_unit/attempt02/adapter.json'
BINARY = 'results/fx2_xml_word_native_build_v1/attempt02/work/cmix'
SUPPORT = 'tools/fx2_weight_native_transfer250k_q0_v1.py'
# These are the exact retained coordinates of the ratio opening comparison.
RAW = 'results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.raw'
STORED = 'results/fx2_weight_native_transfer250k_q0_v1/work/native/opening.stored'
ARCHIVE = 'results/fx2_weight_native_transfer250k_q0_v1/opening/P/archive.bin'
TRACE = 'results/fx2_weight_native_transfer250k_q0_v1/work/native/opening-P-encode.trace'
CAPS = dict(cpus=[2], memory_bytes=9999998976, swap_bytes=0,
            scratch_bytes=32000000000, wall_seconds=1800)
PHASE_CAP = 180
ARMS = ('P', 'K', 'D', 'S')
PHASES = ('encode', 'decode', 'repeat')
N, RAW_BYTES = 151210, 250000
STATE_BYTES, RECORD_BYTES = 4212, 4217
RING_START, OBSERVER_START = 42, 4138
MASK = (1 << 64) - 1
FIELD_MULTIPLIER = 0x9e3779b97f4a7c15


def write_new(path, data):
    with path.open('xb') as stream:
        stream.write(data)


def equal_files(left, right):
    require(left.stat().st_size == right.stat().st_size, 'file sizes differ')
    offset = 0
    with left.open('rb') as a, right.open('rb') as b:
        while chunk := a.read(1 << 20):
            other = b.read(len(chunk))
            if chunk != other:
                first = next(i for i, (x, y) in enumerate(zip(chunk, other)) if x != y)
                raise ValueError('first file divergence at byte ' + str(offset + first))
            offset += len(chunk)


class NativeGate(BaseGate):
    def release_observations(self, label):
        self.closure()
        before = memory_snapshot(self.group)
        released = []
        for arm in ARMS:
            for phase in PHASES:
                for suffix in ('.xml', '.coder'):
                    path = self.work / 'native' / (arm + '-' + phase + suffix)
                    if path.exists():
                        released.append(release_closed_file(path))
        if not hasattr(self, 'cache_events'):
            self.cache_events = []
        self.cache_events.append(dict(label=label, before=before,
                                     after=memory_snapshot(self.group), files=released))
        self.write('closed-trace-cache.json', dict(events=self.cache_events,
                   advisory_only=True, guard_unchanged=True))

    def run(self, name, argv, cap, env=None, accepted=(0,), work=None):
        self.release_observations('before-' + name)
        try:
            return super().run(name, argv, cap, env, accepted, work)
        finally:
            # Never advise pages while a native writer may still be alive.
            self.release_observations('after-' + name)

    def artifact(self, path):
        require(Path(path).name != 'ppm.temp', 'PPM transient must never be hashed')
        result = super().artifact(path)
        if Path(path).is_relative_to(self.result) and Path(path).suffix in ('.xml', '.coder'):
            self.closure()
            release_closed_file(path)
        return result


def bound_support(g):
    module = types.ModuleType('bound_xml_cleanup_support')
    module.__file__ = str(ROOT / SUPPORT)
    exec(compile(g.buffers[SUPPORT], module.__file__, 'exec'), module.__dict__)
    # The retained helper normally obtains require through its own launcher.
    module.require = require
    return module


def cleanup(g, support, name):
    closed = False
    try:
        g.closure()
        closed = True
    finally:
        record = support.cleanup_native_transient(g, closed)
        g.write(name + '-cleanup.json', record)
    require(record['cleanup_complete'], 'native transient cleanup incomplete')
    return record


def validate(g):
    plan = json.loads(g.buffers[PLAN])
    require(plan['id'] == ID and plan['caps'] == CAPS and
            plan['phase_elapsed_seconds'] == PHASE_CAP, 'plan identity or caps differ')
    require(plan['files']['binary']['path'] == BINARY, 'cached binary path differs')
    for row in plan['files'].values():
        data = g.buffers[row['path']]
        require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() ==
                row['sha256'].removeprefix('sha256:'), 'plan file binding differs')
    for row in plan['runtime_files']:
        path = Path(row['path'])
        require(path.stat().st_size == row['bytes'] and
                sha(path) == row['sha256'].removeprefix('sha256:'), 'runtime binding differs')
    for path in (RAW, STORED, ARCHIVE, TRACE, ADAPTER, SUPPORT, PARENT + 'package.json'):
        require(path in g.buffers, 'missing consumed input: ' + path)
    require(len(g.buffers[RAW]) == RAW_BYTES and len(g.buffers[STORED]) == N + 10 and
            g.buffers[STORED][:10] == bytes.fromhex('8000000000070003d090') and
            len(g.buffers[TRACE]) == N * 8 * 28, 'retained population coordinates differ')
    package = json.loads(g.buffers[PARENT + 'package.json'])
    adapter = json.loads(g.buffers[ADAPTER])
    for row in package['source_members'] + package['runtime_members']:
        require(row['path'] in g.buffers and sha(ROOT / row['path']) ==
                row['sha256'].removeprefix('sha256:'), 'parent member differs')
    for row in adapter['added_files']:
        ref = row['source']
        data = g.buffers[ref['path']]
        require(len(data) == ref['bytes'] and hashlib.sha256(data).hexdigest() ==
                ref['sha256'].removeprefix('sha256:'), 'added native source differs')
    dictionary = g.buffers[PARENT + 'work/dictionary/english.dic']
    words = re.findall(rb'[a-z]+', dictionary)
    ordered = hashlib.sha256(b'field-WRT-dictionary-v1\0')
    for word in words:
        ordered.update(len(word).to_bytes(4, 'little'))
        ordered.update(word)
    expected = plan['ordered_dictionary']
    require(dictionary.endswith(b'\n') and hashlib.sha256(dictionary).hexdigest() == expected['raw_sha256'] and
            len(words) == expected['words'] and sum(map(len, words)) == expected['word_bytes'] and
            max(map(len, words)) == expected['longest_word'] and ordered.hexdigest() == expected['sha256'],
            'ordered dictionary identity differs')
    return plan


def xml_records(path, arm, modeled=N, raw_bytes=RAW_BYTES):
    """Validate every serialized field, observer boundary and delay-ring update."""
    require(arm in ('K', 'D', 'S'), 'XML trace arm differs')
    require(path.stat().st_size == (modeled + 2) * RECORD_BYTES, 'XML trace length differs')
    ring = bytearray(4096)
    previous = None
    with path.open('rb') as stream:
        for i in range(modeled + 2):
            record = stream.read(RECORD_BYTES)
            event = ord('I') if i == 0 else ord('F') if i == modeled + 1 else ord('B')
            count = min(i, modeled)
            state = record[5:]
            u64 = lambda at: int.from_bytes(state[at:at + 8], 'little')
            observer = state[OBSERVER_START:4204]
            require(record[0] == event and int.from_bytes(record[1:5], 'little') == STATE_BYTES,
                    'XML record framing differs at ' + str(i))
            require(state[:4] == b'XWC1' and state[4] == ord(arm) and state[5] == 1 and
                    state[6] == int(event == ord('F')) and u64(10) == count and
                    u64(18) == count % 4096, 'XML context header differs at ' + str(i))
            require(observer[:4] == b'XFO1' and observer[4] == int(count > 0) and
                    observer[5] == 0 and observer[6] == int(event == ord('F')) and
                    observer[7] <= 1 and observer[8] <= 1 and observer[9] <= 2 and
                    int.from_bytes(observer[13:21], 'little') == raw_bytes and
                    int.from_bytes(observer[29:37], 'little') == count and
                    int.from_bytes(observer[21:29], 'little') <= raw_bytes and
                    observer[38] <= 27, 'XML observer state differs at ' + str(i))
            current, delayed, effective = state[7:10]
            require(current <= 6 and delayed <= 6 and observer[37] == current,
                    'XML field state differs')
            if event == ord('B'):
                slot = (count - 1) % 4096
                require(delayed == ring[slot], 'XML causal delay differs')
                ring[slot] = current
            elif event == ord('I'):
                require(current == delayed == effective == 0 and not any(observer[7:13]) and
                        int.from_bytes(observer[21:29], 'little') == 0,
                        'XML initial state differs')
            else:
                require(previous is not None and state[7:OBSERVER_START] == previous[7:OBSERVER_START]
                        and observer[7:] == previous[OBSERVER_START + 7:4204] and
                        u64(4204) == int.from_bytes(previous[4204:], 'little') and
                        observer[9] == 0 and int.from_bytes(observer[21:29], 'little') == raw_bytes,
                        'XML terminal state differs')
            require(state[RING_START:OBSERVER_START] == ring, 'XML ring contents differ')
            want = current if arm == 'D' else delayed if arm == 'S' else 0
            require(effective == want and u64(34) == (u64(26) ^ ((effective * FIELD_MULTIPLIER) & MASK)),
                    'XML context law differs')
            if event != ord('I'):
                require(u64(4204) == u64(34), 'external native context scalar differs')
            previous = state
            yield event, state


def compare_shared_xml(paths, modeled=N, raw_bytes=RAW_BYTES):
    streams = [xml_records(paths[arm], arm, modeled, raw_bytes) for arm in ('K', 'D', 'S')]
    contingency = [[0] * 7 for _ in range(7)]
    disagreements = 0
    for rows in zip(*streams):
        event, k = rows[0]
        for other_event, state in rows[1:]:
            # Exclude only arm, effective field, derived context and external scalar.
            require(event == other_event and k[:4] + k[5:9] + k[10:34] + k[42:4204] ==
                    state[:4] + state[5:9] + state[10:34] + state[42:4204],
                    'K/D/S observer, ring or original word coordinate differs')
        if event == ord('B'):
            current, delayed = rows[1][1][7], rows[2][1][8]
            contingency[current][delayed] += 1
            disagreements += current != delayed
    # A permutation merely renames buckets. Require an observed nonfunctional
    # direction in the joint table, as well as actual temporal disagreement.
    row_split = any(sum(value > 0 for value in row) > 1 for row in contingency)
    column_split = any(sum(contingency[i][j] > 0 for i in range(7)) > 1 for j in range(7))
    return dict(records=modeled + 2, shared_observer_ring_parent_context_equal=True,
                contingency_current_by_delayed=contingency, disagreements=disagreements,
                current_maps_to_multiple_delayed=row_split,
                delayed_maps_to_multiple_current=column_split,
                delayed_field_active=any(sum(row[1:]) for row in contingency),
                control_adequate=bool(disagreements and (row_split or column_split) and
                                      any(sum(row[1:]) for row in contingency)))


def validate_activation(stderr, arm):
    found = re.findall(rb'Gamma XML selected=([KDS])\r?\n', stderr)
    require(found == ([] if arm == 'P' else [arm.encode()]) and
            stderr.count(b'Gamma XML selected=') == len(found), 'native XML activation differs')


class Codec:
    def __init__(self, g, arm, support):
        require(arm in ARMS, 'unknown arm')
        self.g, self.arm, self.support = g, arm, support
        self.native, self.calls, self.restored = g.work / 'native', 0, None

    def invoke(self, phase, args):
        name = self.arm + '-' + phase
        env = dict(GAMMA_FX2_XML_ARM=self.arm,
                   GAMMA_FX2_CODER_TRACE=str(self.native / (name + '.coder')))
        if self.arm != 'P':
            env.update(GAMMA_FX2_XML_TRACE=str(self.native / (name + '.xml')),
                       GAMMA_FX2_XML_RAW=str(self.native / (name + '.observed.raw')))
        try:
            self.g.run(name, [str(self.native / 'cmix'), *args], PHASE_CAP,
                       env=env, work=self.native)
            validate_activation((self.g.result / (name + '.stderr')).read_bytes(), self.arm)
        finally:
            cleanup(self.g, self.support, name)

    def compress(self, raw):
        require(self.calls < 2, 'unexpected third encoder')
        require(raw == self.g.buffers[RAW], 'encoder population differs')
        phase = 'encode' if self.calls == 0 else 'repeat'
        if self.calls == 0:
            source = self.native / (self.arm + '-encode.raw')
            write_new(source, raw)
        else:
            require(self.restored is not None and self.restored.read_bytes() == raw,
                    'repeat physical decoded source differs')
            source = self.restored
        self.calls += 1
        target = self.native / (self.arm + '-' + phase + '.cmix')
        require(not target.exists(), 'archive output exists')
        self.invoke(phase, ['-c', 'dictionary/english.dic', str(source), str(target),
                           '--transformer', 'models/6m-q4-fp32.tfwc2'])
        require(source.read_bytes() == raw, 'native encoder input changed')
        return target.read_bytes()

    def decompress(self, archive):
        require(self.calls == 1 and self.restored is None, 'unexpected decoder')
        source = self.native / (self.arm + '-decode.cmix')
        output = self.native / (self.arm + '-decode.raw')
        write_new(source, archive)
        require(not output.exists(), 'decoded output exists')
        self.invoke('decode', ['-d', 'dictionary/english.dic', str(source), str(output),
                              '--transformer', 'models/6m-q4-fp32.tfwc2'])
        require(source.read_bytes() == archive, 'native decoder archive changed')
        require(output.read_bytes() == self.g.buffers[RAW], 'native raw inverse differs')
        self.restored = output
        return output.read_bytes()


def decision(archives, control_adequate, local_delta, budget_pass):
    saving = archives['P'] - archives['D']
    separated = all(archives['D'] < archives[arm] for arm in ('P', 'K', 'S'))
    return dict(archive_saving_bytes=saving, control_margin_bytes=archives['S'] - archives['D'],
                treatment_beats_all_controls=separated, control_adequate=control_adequate,
                local_package_budget_pass=budget_pass,
                diagnostic_local_net_bytes=saving - local_delta,
                scientific_verdict='positive_native_diagnostic' if separated and control_adequate and budget_pass else 'hold_fixed_realization',
                larger_gate_authorized=False, complete_package_bytes=None,
                full_corpus_score_bytes=None, objective_credit_bytes=0)


def execute(g, support):
    plan = validate(g)
    native = g.work / 'native'
    native.mkdir()
    package = json.loads(g.buffers[PARENT + 'package.json'])
    adapter = json.loads(g.buffers[ADAPTER])
    for row in package['source_members'] + package['runtime_members']:
        if row['path'] == PARENT + 'work/cmix':
            continue
        target = native / row['path'].removeprefix(PARENT + 'work/')
        if not target.exists():
            g.copy(row['path'], target)
    g.adapter(ADAPTER, native)
    for row in adapter['added_files']:
        g.copy(row['source']['path'], native / row['target'])
    g.copy(BINARY, native / 'cmix')
    (native / 'cmix').chmod(0o555)
    g.binaries[str(native / 'cmix')] = sha(native / 'cmix')
    g.copy(RAW, native / 'population.raw')
    try:
        g.run('preprocess', [str(native / 'cmix'), '-s', 'dictionary/english.dic',
                            'population.raw', 'population.stored'], PHASE_CAP, work=native)
        equal_files(native / 'population.stored', ROOT / STORED)
    finally:
        cleanup(g, support, 'preprocess')
    sources = [native / row['path'].removeprefix(PARENT + 'work/') for row in package['source_members']]
    sources += [native / row['target'] for row in adapter['added_files']]
    runtime = [native / row['path'].removeprefix(PARENT + 'work/') for row in package['runtime_members']]
    source_refs, runtime_refs = [g.artifact(p) for p in sources], [g.artifact(p) for p in runtime]
    options = ('-c dictionary/english.dic input archive --transformer models/6m-q4-fp32.tfwc2\n'
               '-d dictionary/english.dic archive output --transformer models/6m-q4-fp32.tfwc2\n'
               'GAMMA_FX2_XML_ARM=D\n')
    source_delta = sum(row['bytes'] for row in source_refs) - package['source_member_bytes']
    binary_delta = (native / 'cmix').stat().st_size - next(row['bytes'] for row in package['runtime_members'] if row['path'].endswith('/cmix'))
    local_delta = source_delta + binary_delta + len(options.encode()) - package['option_bytes']
    inventory = source_refs + runtime_refs
    counted = [(row['path'], row['bytes']) for row in inventory] + [('required-options', len(options.encode()))]
    local_package = dict(source_files=source_refs, runtime_files=runtime_refs,
                         system_runtime_inventory=plan['runtime_files'], counted_files=inventory,
                         counted_bytes=sum(size for _, size in counted), option_text=options,
                         source_runtime_overlap_counted_twice=True, source_delta_bytes=source_delta,
                         binary_delta_bytes=binary_delta, added_local_component_bytes=local_delta,
                         complete_submission_package=False, unresolved=package['unresolved'])
    budget_pass = (local_package['counted_bytes'] <= 10000000 and
                   local_delta <= plan['accounting']['maximum_added_local_component_bytes'])
    require(budget_pass, 'local package or added-component budget exceeded')
    require(source_delta == plan['accounting']['source_delta_bytes'] and
            binary_delta == plan['accounting']['binary_delta_bytes'], 'measured component deltas differ from plan')
    g.write('package.json', local_package)
    rows, archives = {}, {}
    for arm in ARMS:
        result = driver.run(ID, native / 'population.raw', RAW_BYTES, True,
                            run_purpose='diagnostic', run_scope_label=arm + '-opening250k',
                            run_context='One native base word context conditioned by completed XML fields',
                            run_source='canonical-tool', module=Codec(g, arm, support),
                            artifact_dir=g.result / arm, package_inventory=(counted, local_package))
        result.update(arm=arm, codec_process_state='fresh-native-process-per-encode-decode-repeat')
        g.write(arm + '/result.json', result)
        require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'],
                'native inverse or archive repeat differs')
        checks = []
        for phase in PHASES:
            stem = arm + '-' + phase
            checks.append(g.compare_trace(native / (arm + '-encode.coder'), native / (stem + '.coder'), N * 8 * 28))
            if arm != 'P':
                equal_files(native / (arm + '-encode.xml'), native / (stem + '.xml'))
                equal_files(native / (stem + '.observed.raw'), native / 'population.raw')
                require(sum(1 for _ in xml_records(native / (stem + '.xml'), arm)) == N + 2,
                        'XML record population differs')
        if arm in ('P', 'K'):
            equal_files(g.result / arm / 'archive.bin', ROOT / ARCHIVE)
            g.compare_trace(ROOT / TRACE, native / (arm + '-encode.coder'), N * 8 * 28)
        g.write(arm + '-coder-comparisons.json', dict(comparisons=checks))
        archives[arm] = result['compressed_size']
        rows[arm] = dict(result=g.artifact(g.result / arm / 'result.json'), archive_bytes=archives[arm],
                         native_raw_inverse=True, exact_repeat=True, exact_same_arm_coder=True,
                         xml_observer_checked=arm != 'P')
        g.release_observations('validated-' + arm)
    equal_files(g.result / 'P/archive.bin', g.result / 'K/archive.bin')
    shared = compare_shared_xml({arm: native / (arm + '-encode.xml') for arm in ('K', 'D', 'S')})
    g.write('shared-xml-state.json', shared)
    g.release_observations('after-shared-comparison')
    require(len(g.commands) == 13, 'native phase count differs')
    return dict(correctness_pass=True, raw_bytes=RAW_BYTES, modeled_bytes=N, raw_offset=0,
                arms=rows, archive_bytes=archives, control_aliases={'G': 'K'},
                parent_and_bookkeeping_match_retained=True, shared_xml_state=shared,
                compile_processes=0, source_delta_bytes=source_delta, binary_delta_bytes=binary_delta,
                added_local_component_bytes=local_delta, native_binary=g.artifact(native / 'cmix'),
                **decision(archives, shared['control_adequate'], local_delta, budget_pass))


def main():
    require(sys.argv[1:] in ([], ['--validate-only']), 'unexpected arguments')
    g = NativeGate(ROOT, ID, CAPS, validate_only=bool(sys.argv[1:]))
    validate(g)
    if sys.argv[1:]:
        print(json.dumps(dict(status='preflight_pass', inputs=len(g.inputs), codec_executed=False,
                              native_processes_planned=12, preprocess_processes_planned=1,
                              compile_processes_planned=0, control_aliases={'G': 'K'})))
        return 0
    support = bound_support(g)
    stage = dict(schema='gamma.enwiki9.native-xml-word-stage.v1', candidate_id=ID,
                 experiment=g.reference, objective_credit_bytes=0, complete_package_bytes=None,
                 full_corpus_score_bytes=None, larger_gate_authorized=False,
                 guard_authority='canonical outer guard; final closure pending')
    try:
        stage.update(execute(g, support), status='passed')
        g.verify()
    except Exception as error:
        stage.update(status='execution_failed', failure_class=getattr(error, 'category', 'invariant_or_evidence_failure'),
                     error=type(error).__name__ + ': ' + str(error))
    try:
        stage['terminal_cleanup'] = cleanup(g, support, 'terminal')
        g.closure()
        g.verify()
        stage['child_closure_ok'] = True
    except Exception as error:
        stage.update(status='execution_failed', cleanup_error=str(error), child_closure_ok=False)
    stage['commands'] = g.commands
    transient = g.work / 'native/ppm.temp'
    stage['artifact_index_exclusions'] = [dict(path=str(transient.relative_to(ROOT)),
                                              reason='PPM transient; metadata cleanup only, never hashed')]
    errors, artifacts = [], []
    for path in sorted(g.result.rglob('*')):
        if path == transient or path.name in ('stage-decision.json', 'artifacts.json'):
            continue
        try:
            require(not path.is_symlink(), 'aliased artifact')
            if path.is_file():
                artifacts.append(g.artifact(path))
        except Exception as error:
            errors.append(dict(path=str(path), error=str(error)))
    if errors:
        stage.update(status='execution_failed', artifact_index_errors=errors)
    stage['artifact_index_complete'] = not errors
    g.write('artifacts.json', dict(files=artifacts, errors=errors))
    stage['artifacts'] = g.artifact(g.result / 'artifacts.json')
    g.write('stage-decision.json', stage)
    print(json.dumps(stage))
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
