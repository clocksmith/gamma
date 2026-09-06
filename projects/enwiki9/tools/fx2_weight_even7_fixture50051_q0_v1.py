#!/usr/bin/env python3
"""Prospective fixed even7 model mutation and exact native fixture comparison."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ID = 'fx2_weight_even7_fixture50051_q0_v1'
PARENT_ID = 'fx2_weight_native_fixture50051_q0_v1'
PARENT = 'results/' + PARENT_ID + '/'
CACHED = PARENT + 'work/native/'
STATIC = 'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
MARGINAL = 'results/fx2_weight_marginal_roundtrip_q0_v1/'
FIXTURES = MARGINAL + 'work/fixtures/'
PROBE = 'tools/fx2_weight_even7_probe_v1.cpp'
HEADER = 'lib/fx2_weight_format_v1.hpp'
SAFE_SOURCE = 'tools/fx2_weight_native_transfer250k_q0_v1.py'
NATIVE_AUDIT = 'operations/provenance/public_fx2_weight_native_terminal_20260905.json'
NATIVE_REFLECTION = 'operations/adaptive/reflections/20260905T230139Z_d8475c03dc.json'
VOCABULARY = 'operations/provenance/public_fx2_authenticated_vocabulary_20260905.json'
MODEL_METADATA = MARGINAL + 'model-P.stdout'
MARGINAL_MODEL = MARGINAL + 'work/model.D'
CAPS = {'cpus': [2], 'memory_bytes': 9999998976, 'scratch_bytes': 16000000000,
        'swap_bytes': 0, 'wall_seconds': 900}
ARMS = ('P', 'K', 'D', 'C')
PHASES = ('encode', 'decode', 'reencode')
MAPPING = (-6, -6, -4, -4, -4, -2, 0, 0, 0, 2, 4, 4, 4, 6, 6)
RAW_BYTES, MODELED_BYTES = 50051, 32478
ORIGINAL_MODEL_BYTES, MARGINAL_MODEL_BYTES = 2930652, 2908329
FLAGS = ('-std=c++17', '-O2', '-Wall', '-Wextra', '-fno-fast-math', '-ffp-contract=off',
         '-fno-math-errno', '-march=x86-64-v3', '-mtune=generic', '-mrecip=none')
OPTIONS = '-c dictionary input archive --transformer model\n-d dictionary archive output --transformer model\n'
PROBE_BUILD_OPTIONS = 'g++ ' + ' '.join(FLAGS) + ' tools/fx2_weight_even7_probe_v1.cpp -o probe\n'
FIXTURE_IDS = {'zero_tensors', 'uniform_marginal', 'skewed_marginal', 'heterogeneous_tensors',
               'empty_and_scalar', 'all_tags_and_rows', 'range_adaptation_stress', 'maximum_native_dimensions'}
NEGATIVE_IDS = {'duplicate_names', 'unknown_dtype', 'too_many_dimensions', 'unknown_encoding',
                'int4_wrong_dtype', 'bf16_wrong_dtype', 'plane_wrong_dtype', 'int4_outside_public_writer_domain',
                'rope_missing_frequency', 'rope_wrong_dtype', 'rope_wrong_frequency_shape', 'rope_nonvector_frequency',
                'extent_exceeds_bound', 'parent_bad_magic', 'parent_nonzero_cache', 'parent_truncated_header',
                'parent_truncated_stream', 'parent_missing_flush', 'parent_trailing_byte', 'parent_tensor_limit'}
PINNED = {
    NATIVE_AUDIT: '9370d51f64049b536a909f79115ffe6bbd91dea2ff5157eb18ea24cadd74ef1e',
    NATIVE_REFLECTION: '9bcc8540bf9fb03a4b89d44c0a6b9c7f07f85f587a7af0848f830a0a0ad41cda',
    SAFE_SOURCE: '474b7d6e2bb3f89817d440c7a1c4e6902437d4e0ae0c78105da7b049da83ee0f',
    PROBE: 'c34cdc271c8337ab4849fdb1fc41d44efe302897892872da2a8acbcd93deded5',
    HEADER: 'aa615fc92b456bada499602888c2bf38ea8a98918694ce2cfd9691d384b2fa30',
    MARGINAL_MODEL: '5cae4299a64af88b88a637f3c14e9ee54a5fd98c559e391f35dfa7d832b00e4a',
}
RUNTIME = {
    'cmix': (496136, 'c848acc756c8ced70422dfc4c8da03ac936417754b877eb8addf0143ce2ba100'),
    'dictionary/english.dic': (411996, '4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a'),
    'models/6m-q4-fp32.tfwc2': (ORIGINAL_MODEL_BYTES, '7f4db6c8c843a7e6264b6a48ed4805e9e431f543df7a9a0ecb37a35a5e4b8860'),
}
METADATA_FIELDS = ('name', 'dtype', 'encoding', 'elements', 'represented_bytes', 'stored_payload_bytes', 'row_width', 'shape')


def load_helpers():
    """Execute exact bound source buffers; do not import pre-existing bytecode."""
    if sys.argv[1:] not in ([], ['--validate-only']):
        raise ValueError('unexpected arguments')
    contract_path = 'operations/adaptive/experiments/' + ID + '.json'
    content = (ROOT / contract_path).read_bytes()
    if not sys.argv[1:]:
        reference = json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON'])
        if reference != {'path': contract_path, 'sha256': 'sha256:' + hashlib.sha256(content).hexdigest()}:
            raise ValueError('experiment binding changed before helper load')
    inputs = {row['path']: row for row in json.loads(content)['inputs']}
    buffers = {}
    for source in ('tools/' + ID + '.py', 'lib/fx2_native_gate_v1.py', 'lib/artifacts.py', SAFE_SOURCE):
        path = ROOT / source
        if path.resolve() != path:
            raise ValueError('aliased bootstrap source')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != inputs[source]['sha256'].removeprefix('sha256:'):
            raise ValueError('bootstrap source changed: ' + source)
        buffers[source] = data
    namespace = {}
    exec(compile(buffers['lib/fx2_native_gate_v1.py'], str(ROOT / 'lib/fx2_native_gate_v1.py'), 'exec'), namespace)
    globals().update({name: namespace[name] for name in ('GateFailure', 'NativeGate', 'require', 'sha')})
    safe = types.ModuleType('bound_fx2_transfer_safety')
    safe.__file__ = str(ROOT / SAFE_SOURCE)
    exec(compile(buffers[SAFE_SOURCE], safe.__file__, 'exec'), safe.__dict__)
    safe.require, safe.sha = require, sha
    # Only candidate-independent comparison/cleanup operations are reused.
    globals().update({name: getattr(safe, name) for name in
                      ('bound_ref', 'compare_bytes', 'compare_trace', 'cleanup_native_transient')})


def histogram_header(data):
    """Read only the independently retained fixed-marginal side information."""
    require(data[:8] == b'GFX2MAR1' and len(data) >= 77 and data[12] == 1, 'histogram authority format differs')
    tensor_count, count = struct.unpack_from('<I', data, 8)[0], struct.unpack_from('<I', data, 13)[0]
    require(count <= tensor_count and len(data) >= 77 + 64 * count + 5, 'histogram authority is truncated')
    global_counts = list(struct.unpack_from('<15I', data, 17))
    local, summed = {}, [0] * 15
    for number in range(count):
        record = struct.unpack_from('<16I', data, 77 + 64 * number)
        index, counts = record[0], list(record[1:])
        require(index < tensor_count and index not in local and (not local or index > max(local)), 'histogram indices differ')
        local[index] = counts
        summed = [a + b for a, b in zip(summed, counts)]
    require(summed == global_counts, 'histogram aggregate differs')
    return tensor_count, local, global_counts


def validate_inputs(gate):
    for source, digest in PINNED.items():
        bound_ref(gate, {'path': source, 'sha256': digest})
    for source in ('lib/driver.py', 'tools/research_contracts.py', 'tools/enwiki9_python_source_closure.py',
                   'lib/fx2_native_gate_v1.py', 'lib/artifacts.py', MODEL_METADATA, VOCABULARY, FIXTURES + 'manifest.json'):
        bound_ref(gate, gate.inputs[source])
    audit = json.loads(gate.buffers[NATIVE_AUDIT])
    reflection = json.loads(gate.buffers[NATIVE_REFLECTION])
    require(audit['candidate_id'] == PARENT_ID and audit['validity'] == 'valid', 'cached native audit is not valid')
    require(reflection['candidateId'] == PARENT_ID and reflection['validity']['valid'] is True and
            reflection['decision']['promotionPredicatesPass'] is True, 'native parent reflection is not selectable')
    require(any(row['path'] == NATIVE_AUDIT and row['sha256'].removeprefix('sha256:') == PINNED[NATIVE_AUDIT]
                for row in reflection['evidence']), 'native reflection does not bind audit')
    require(gate.contract['parent'] == {'candidateId': PARENT_ID, 'revision': audit['candidate_revision']} and
            gate.contract['objective'] == reflection['objective'], 'semantic parent or objective differs')
    require(audit['source_bindings']['all_inputs_match'] and audit['resources']['cleanup_complete'] and
            audit['resources']['closed_process_list_empty'] and not any(audit['resources']['guard_flags'].values()),
            'cached native source or closed guard is invalid')
    require(all(audit['scientific_measurements'][key] is True for key in
                ('tensor_comparison_pass', 'coder_records_identical', 'all_archives_match_original_parent')),
            'cached native equivalence antecedent failed')
    indexed = {row['path']: row for row in audit['artifacts']}
    require(len(indexed) == len(audit['artifacts']), 'duplicate native artifact reference')
    gate.cached, gate.parent_packages = {}, {}
    for arm in ('P', 'K', 'D'):
        path = PARENT + arm + '-package.json'
        package = json.loads(bound_ref(gate, indexed[path]))
        require(len(package['counted_files']) == 135 and package['source_runtime_overlap_counted_twice'] is True and
                package['dependency_closure_complete'] is False, 'cached package scope differs')
        require(package['option_text'] == OPTIONS and package['counted_bytes'] ==
                sum(row['bytes'] for row in package['counted_files']) + len(OPTIONS.encode()), 'cached package arithmetic differs')
        for row in package['counted_files']:
            require(row['path'].startswith(CACHED) and indexed[row['path']] == row, 'package member lacks native audit authority')
            bound_ref(gate, row)
            require(row['path'] not in gate.cached or gate.cached[row['path']] == row, 'conflicting cached member')
            gate.cached[row['path']] = row
        gate.parent_packages[arm] = package
    require(len(gate.cached) == 134 and gate.parent_packages['P'] == gate.parent_packages['K'], 'cached package closure differs')
    for relative, (size, digest) in RUNTIME.items():
        bound_ref(gate, {'path': CACHED + relative, 'bytes': size, 'sha256': digest})
    gate.parent_archive = bound_ref(gate, audit['arms']['P']['archive'])
    require(len(gate.parent_archive) == 3223 and hashlib.sha256(gate.parent_archive).hexdigest() ==
            'cc94af1a3af764b9c3906f1a30397ed987e71df19b02dca81c50b62146b27805', 'parent archive differs')
    gate.raw = bound_ref(gate, gate.cached[CACHED + 'prof_input/input'])
    require(len(gate.raw) == RAW_BYTES and hashlib.sha256(gate.raw).hexdigest() ==
            '890b3e1210a24a249768d86bd5a79a1775ce19b2d56984ce3069ee26359ef2e6', 'public fixture differs')
    gate.storage = bound_ref(gate, {'path': STATIC + 'work/fixture.stored', 'bytes': 32488,
                                  'sha256': 'be65dc4d4afc30647dcaab0f7e6191e50295c7c2a626fdeedbfa5a684a1eaf9d'})
    gate.vocabulary = json.loads(gate.buffers[VOCABULARY])
    require(gate.vocabulary['embedded_weights']['sha256'] == RUNTIME['models/6m-q4-fp32.tfwc2'][1] and
            gate.vocabulary['vocabulary_size'] == 205, 'vocabulary/model association differs')
    require(gate.storage[:10] == bytes.fromhex('8000000000070000c383') and
            len(gate.storage) == MODELED_BYTES + 10 and
            set(gate.storage[10:]) <= set(gate.vocabulary['vocabulary_bytes']), 'stored fixture framing or alphabet differs')
    archive_header(gate, gate.parent_archive)
    gate.metadata = json.loads(gate.buffers[MODEL_METADATA])
    count, gate.histograms, aggregate = histogram_header(gate.buffers[MARGINAL_MODEL])
    require(count == len(gate.metadata['tensors']) == 434 and len(gate.histograms) == 111 and
            sum(aggregate) == 5868864 and len(gate.buffers[MARGINAL_MODEL]) == MARGINAL_MODEL_BYTES,
            'measured full-model histogram authority differs')
    gate.fixture_manifest = json.loads(gate.buffers[FIXTURES + 'manifest.json'])
    require(gate.fixture_manifest['schema'] == 'gamma.fx2-weight-marginal-synthetic-fixtures.v1' and
            len(gate.fixture_manifest['valid']) == 8 and {row['id'] for row in gate.fixture_manifest['valid']} == FIXTURE_IDS,
            'synthetic population differs')
    gate.negatives = [row for row in gate.fixture_manifest['rejection'] if row['mode'] == 'P']
    require(len(gate.negatives) == 20 and {row['id'] for row in gate.negatives} == NEGATIVE_IDS, 'malformed parent population differs')
    refs = [row[key] for row in gate.fixture_manifest['valid'] for key in ('parent', 'raw_reference')]
    refs += [row['input'] for row in gate.negatives]
    for row in refs:
        require(Path(row['path']).name == row['path'], 'fixture path escapes population')
        bound_ref(gate, {**row, 'path': FIXTURES + row['path']})
    include = re.findall(rb'^\s*#\s*include\s*"([^"]+)"', gate.buffers[PROBE], re.M)
    require(include == [b'../lib/fx2_weight_format_v1.hpp'] and
            not re.findall(rb'^\s*#\s*include\s*"', gate.buffers[HEADER], re.M), 'mutator quoted include closure differs')


def archive_header(gate, data):
    require(len(data) >= 51 and data[:9] == bytes.fromhex('47465631070000c383'), 'native archive literal header differs')
    require(int.from_bytes(data[9:14], 'big') == (1 << 39) + MODELED_BYTES and
            data[14:46].hex() == gate.vocabulary['vocabulary_bitmap_hex'], 'native archive modeled coordinates or map differ')


def raw_tensors(data):
    """Independent parser for the retained small raw synthetic references."""
    position = 0
    def take(size):
        nonlocal position
        require(size >= 0 and position + size <= len(data), 'raw reference is truncated')
        result = data[position:position + size]
        position += size
        return result
    def u32():
        return int.from_bytes(take(4), 'little')
    require(take(8) == b'FX2TFW01', 'raw fixture magic differs')
    rows = []
    for _ in range(u32()):
        name = take(u32()).decode()
        dtype, dimensions = take(1)[0], u32()
        require(dtype in (0, 1, 2, 3) and dimensions <= 8, 'raw fixture metadata differs')
        shape = [u32() for _ in range(dimensions)]
        elements = math.prod(shape)
        payload = take(elements * (1, 2, 4, 4)[dtype])
        rows.append({'name': name, 'dtype': dtype, 'shape': shape, 'elements': elements, 'payload': payload})
    require(position == len(data), 'raw reference has trailing data')
    return rows


def fnv(data):
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & ((1 << 64) - 1)
    return f'{value:016x}'


def mapped_histogram(counts):
    require(len(counts) == 15 and all(type(value) is int and value >= 0 for value in counts), 'invalid histogram')
    output = [0] * 15
    for symbol, count in enumerate(counts):
        output[MAPPING[symbol] + 7] += count
    return output


def verify_probe(row, arm, source, output, expected_metadata=None, expected_histograms=None, raw_reference=None):
    require(row['schema'] == 'gamma.fx2-weight-even7-probe.v1' and row['mode'] == arm and
            row['input_format'] == row['output_format'] == 'FX2TFWC2', 'mutator schema or mode differs')
    require(all(row[key] is True for key in ('parent_stream_regeneration_ok', 'transformed_model_exact',
                'canonical_output_repeat_ok', 'fresh_transformation_repeat_ok', 'non_int4_events_and_metadata_unchanged')),
            'mutator direct comparison failed')
    require(row['original_model_inversion_claimed'] is (arm in ('P', 'K')) and
            row['rope_materialized'] is False and row['objective_credit_bytes'] == 0, 'mutator scope differs')
    require(row['input_bytes'] == source.stat().st_size and row['output_bytes'] == output.stat().st_size and
            output.read_bytes()[:8] == b'FX2TFWC2', 'mutator output size or format differs')
    tensors = row['tensors']
    require(row['tensor_count'] == len(tensors), 'mutator tensor count differs')
    if expected_metadata is not None:
        require(len(tensors) == len(expected_metadata), 'metadata reference count differs')
    if raw_reference is not None:
        require(len(tensors) == len(raw_reference), 'raw reference count differs')
    symbols = mapping_changes = changed = shifted = payload_bytes = rope_bytes = int4_count = 0
    for index, tensor in enumerate(tensors):
        require(tensor['index'] == index, 'tensor order differs')
        if expected_metadata is not None:
            require(all(tensor[key] == expected_metadata[index][key] for key in METADATA_FIELDS), 'measured tensor metadata differs')
        encoding = tensor['encoding']
        payload_bytes += tensor['stored_payload_bytes']
        rope_bytes += tensor['represented_bytes'] if encoding in (4, 5) else 0
        if raw_reference is not None:
            raw = raw_reference[index]
            require(all(tensor[key] == raw[key] for key in ('name', 'dtype', 'shape', 'elements')), 'raw synthetic metadata differs')
            original = raw['payload']
            if encoding == 1:
                original = bytes((value if value < 128 else value - 256) + 7 for value in original)
            elif encoding == 2:
                original = b''.join(original[k:k + 2][::-1] for k in range(0, len(original), 2))
            elif encoding in (4, 5):
                original = b''
            expected = original
            if encoding == 1 and arm in ('D', 'C'):
                expected = bytes(MAPPING[value] + 7 for value in original)
                width = tensor['row_width']
                if arm == 'C' and expected and width > 1:
                    expected = b''.join(expected[k + 1:k + width] + expected[k:k + 1] for k in range(0, len(expected), width))
            require(tensor['stored_payload_bytes'] == len(original) and tensor['input_payload_digest'] == fnv(original) and
                    tensor['output_payload_digest'] == fnv(expected), 'independent synthetic payload mapping differs')
            require(tensor['changed_payload_events'] == sum(a != b for a, b in zip(original, expected)), 'synthetic changed-event count differs')
            if encoding == 1:
                require(tensor['input_histogram'] == [original.count(value) for value in range(15)], 'synthetic input histogram differs')
                require(tensor['signed_integer_weight_error_sum'] == sum(b - a for a, b in zip(original, expected)) and
                        tensor['squared_integer_weight_error_sum'] == sum((b - a) ** 2 for a, b in zip(original, expected)),
                        'independent synthetic integer error differs')
        if encoding == 1:
            int4_count += 1
            counts = tensor['input_histogram']
            if expected_histograms is not None:
                require(counts == expected_histograms[index], 'measured tensor histogram differs')
            expected_counts = mapped_histogram(counts) if arm in ('D', 'C') else counts
            require(sum(counts) == tensor['elements'] and tensor['output_histogram'] == expected_counts, 'mapped histogram differs')
            symbols += sum(counts)
            local_mapping_changes = sum(count for k, count in enumerate(counts) if MAPPING[k] != k - 7) if arm in ('D', 'C') else 0
            mapping_changes += local_mapping_changes
            if arm == 'D':
                require(tensor['changed_payload_events'] == local_mapping_changes and
                        tensor['signed_integer_weight_error_sum'] == sum((MAPPING[k] - (k - 7)) * count for k, count in enumerate(counts)) and
                        tensor['squared_integer_weight_error_sum'] == sum((MAPPING[k] - (k - 7)) ** 2 * count for k, count in enumerate(counts)),
                        'independent D mapping counts or integer error differ')
        else:
            require(tensor['input_payload_digest'] == tensor['output_payload_digest'] and tensor['changed_payload_events'] == 0,
                    'non-INT4 payload changed')
        changed += tensor['changed_payload_events']
    require(row['tensor_payload_bytes'] == payload_bytes and row['regenerated_rope_bytes'] == rope_bytes and
            row['int4_tensor_count'] == int4_count and row['int4_symbols'] == symbols and
            row['bookkeeping_int4_tensors'] == (0 if arm == 'P' else int4_count) and
            row['mapping_changed_symbols'] == mapping_changes and row['changed_symbols_vs_parent'] == changed,
            'mutator aggregate counts differ')
    if arm in ('P', 'K'):
        require(changed == 0 and source.read_bytes() == output.read_bytes() and
                row['input_tensor_events_digest'] == row['output_tensor_events_digest'], 'P/K identity differs')
    if arm != 'C':
        require(row['shift_changed_symbols_vs_D'] == 0, 'unexpected row rotation')


def run_mutator(gate, label, arm, source, output, **verification):
    gate.run(label, [str(gate.probe), arm, str(source), str(output)], 30)
    require(output.is_file() and not Path(str(output) + '.partial').exists(), 'mutator output publication incomplete')
    row = json.loads((gate.result / (label + '.stdout')).read_text())
    verify_probe(row, arm, source, output, **verification)
    gate.required.update((output, gate.result / (label + '.stdout'), gate.result / (label + '.execution.json')))
    return row


def mutate_population(gate, label, source, **verification):
    directory = gate.work / 'models' / label
    directory.mkdir(parents=True)
    rows, paths = {}, {}
    for arm in ARMS:
        output, repeated = directory / (arm + '.tfwc2'), directory / (arm + '.repeat.tfwc2')
        row = run_mutator(gate, label + '-' + arm, arm, source, output, **verification)
        repeat = run_mutator(gate, label + '-' + arm + '-repeat', arm, source, repeated, **verification)
        require(output.read_bytes() == repeated.read_bytes() and row == repeat, 'fresh-process mutator repeat differs')
        paths[arm], rows[arm] = output, row
    require(paths['P'].read_bytes() == paths['K'].read_bytes(), 'mutator bookkeeping identity differs')
    require([t.get('output_histogram') for t in rows['D']['tensors']] ==
            [t.get('output_histogram') for t in rows['C']['tensors']], 'row-rotation histogram control differs')
    return rows, paths


def synthetic_gate(gate):
    gate.probe = gate.work / 'even7-probe'
    gate.run('compile-mutator', ['/usr/bin/g++', *FLAGS, str(gate.work / 'source' / PROBE), '-o', str(gate.probe)], 120)
    gate.binaries[str(gate.probe)] = sha(gate.probe)
    gate.run('mutator-self-test', [str(gate.probe), '--self-test'], 30)
    self_test = json.loads((gate.result / 'mutator-self-test.stdout').read_text())
    require(self_test['status'] == 'passed' and self_test['mapping_values'] == 15 and
            self_test['signed_ties_and_idempotence'] is True and self_test['model_accessed'] is False, 'mutator self-test differs')
    checks = []
    for fixture in gate.fixture_manifest['valid']:
        source = gate.work / 'fixtures' / fixture['parent']['path']
        gate.copy(FIXTURES + fixture['parent']['path'], source)
        raw = raw_tensors(gate.buffers[FIXTURES + fixture['raw_reference']['path']])
        rows, outputs = mutate_population(gate, 'synthetic-' + fixture['id'], source, raw_reference=raw)
        require(all(row['tensor_count'] == fixture['tensor_count'] and row['tensor_payload_bytes'] == fixture['tensor_payload_bytes'] and
                    row['regenerated_rope_bytes'] == fixture['regenerated_rope_bytes'] for row in rows.values()), 'synthetic totals differ')
        checks.append({'id': fixture['id'], 'independent_raw_reference_checks': True,
                       'outputs': {arm: gate.artifact(path) for arm, path in outputs.items()}})
    rejected = []
    for fixture in gate.negatives:
        source = gate.work / 'fixtures' / fixture['input']['path']
        gate.copy(FIXTURES + fixture['input']['path'], source)
        output = gate.work / 'fixtures' / (fixture['id'] + '.unexpected.tfwc2')
        label = 'reject-' + fixture['id']
        gate.run(label, [str(gate.probe), 'P', str(source), str(output)], 30, accepted=(1,))
        require(not output.exists() and not Path(str(output) + '.partial').exists() and
                b'fx2_weight_even7_probe_v1:' in (gate.result / (label + '.stderr')).read_bytes(), 'malformed parent rejection differs')
        rejected.append(fixture['id'])
    gate.write('synthetic.json', {'populations': checks, 'malformed_parent_rejections': rejected,
                                'mapping': list(MAPPING), 'fresh_repeats': True, 'objective_credit_bytes': 0})
    gate.required.add(gate.result / 'synthetic.json')


def verify_runtime(gate, model=None):
    for relative, (size, digest) in RUNTIME.items():
        path = gate.native / relative
        require(path.resolve() == path and path.stat().st_size == size and sha(path) == digest, 'cached runtime changed: ' + relative)
    if model is not None:
        require(model.resolve() == model and sha(model) == gate.retained[model], 'selected mutated model changed')
    require(not (gate.native / 'ppm.temp').exists(), 'successful native phase left PPM scratch')


class Codec:
    def __init__(self, gate, arm, model):
        self.gate, self.arm, self.model, self.calls = gate, arm, model, 0

    def invoke(self, phase, arguments):
        gate, name = self.gate, self.arm + '-' + phase
        verify_runtime(gate, self.model)
        env = {'GAMMA_FX2_CODER_TRACE': str(gate.native / (name + '.trace'))}
        if self.arm == 'K':
            env['GAMMA_FX2_WEIGHT_BOOKKEEPING'] = '1'
        gate.run(name, [str(gate.native / 'cmix'), *arguments, '--transformer', str(self.model)], 120, env, work=gate.native)
        verify_runtime(gate, self.model)
        marker = ('Gamma weight loader selected=' + ('K' if self.arm == 'K' else 'P') +
                  ' tensors=434 histogram_tensors=' + ('111' if self.arm == 'K' else '0') +
                  ' histogram_symbols=' + ('5868864' if self.arm == 'K' else '0') + ' side_information_bytes=0 canonical=0').encode()
        markers = [line for line in (gate.result / (name + '.stderr')).read_bytes().splitlines()
                   if line.startswith(b'Gamma weight loader selected=')]
        require(markers == [marker], 'native format-path activation differs: ' + name)
        gate.required.update((gate.native / (name + '.trace'), gate.result / (name + '.stderr'), gate.result / (name + '.execution.json')))

    def compress(self, raw):
        require(raw == self.gate.raw and self.calls < 2, 'unexpected encoder population or call')
        phase = 'encode' if self.calls == 0 else 'reencode'
        self.calls += 1
        name = self.arm + '-' + phase
        with (self.gate.native / (name + '.raw')).open('xb') as handle:
            handle.write(raw)
        self.invoke(phase, ['-c', 'dictionary/english.dic', name + '.raw', name + '.cmix'])
        return (self.gate.native / (name + '.cmix')).read_bytes()

    def decompress(self, archive):
        name = self.arm + '-decode'
        with (self.gate.native / (name + '.cmix')).open('xb') as handle:
            handle.write(archive)
        self.invoke('decode', ['-d', 'dictionary/english.dic', name + '.cmix', name + '.raw'])
        return (self.gate.native / (name + '.raw')).read_bytes()


def packages(gate, models):
    baseline = gate.parent_packages['P']
    runtime_index = max(index for index, row in enumerate(baseline['counted_files'])
                        if row['path'] == CACHED + 'models/6m-q4-fp32.tfwc2')
    source_members = [gate.artifact(gate.work / 'source' / source) for source in (PROBE, HEADER)]
    model_costs, output = {}, {}
    for arm in ARMS:
        files = [gate.artifact(gate.native / row['path'].removeprefix(CACHED)) for row in baseline['counted_files']]
        files[runtime_index] = gate.artifact(models[arm])
        converter_options = (PROBE_BUILD_OPTIONS + arm + ' input.tfwc2 output.tfwc2\n') if arm in ('D', 'C') else ''
        added_source = sum(row['bytes'] for row in source_members) + len(converter_options.encode()) if arm in ('D', 'C') else 0
        if arm in ('D', 'C'):
            files += source_members
        option_text = OPTIONS + converter_options
        package = {'counted_files': files, 'option_text': option_text,
                   'counted_bytes': sum(row['bytes'] for row in files) + len(option_text.encode()),
                   'dependency_closure_complete': False, 'source_runtime_overlap_counted_twice': True,
                   'diagnostic_original_model_in_source_inventory': True,
                   'meaning': 'Inherited raw source/runtime diagnostic inventory: retain original source asset and substitute only the selected runtime model; add conservative mutator source/options for D/C. Not a submission package.',
                   'unresolved': baseline['unresolved']}
        gate.write(arm + '-package.json', package)
        gate.required.add(gate.result / (arm + '-package.json'))
        size = models[arm].stat().st_size
        model_costs[arm] = {'model': gate.artifact(models[arm]), 'model_bytes': size,
                            'per_copy_delta_vs_original': size - ORIGINAL_MODEL_BYTES,
                            'per_copy_delta_vs_selected_marginal': size - MARGINAL_MODEL_BYTES,
                            'two_copy_delta_vs_original': 2 * (size - ORIGINAL_MODEL_BYTES),
                            'two_copy_delta_vs_selected_marginal': 2 * (size - MARGINAL_MODEL_BYTES),
                            'conservative_added_mutator_source_and_options_bytes': added_source,
                            'conservative_two_copy_component_delta_vs_selected_marginal': 2 * (size - MARGINAL_MODEL_BYTES) + added_source,
                            'diagnostic_inventory_delta_vs_original_P': package['counted_bytes'] - baseline['counted_bytes'],
                            'component_economic_pass': 2 * (size - MARGINAL_MODEL_BYTES) + added_source < 0,
                            'native_binary_delta_bytes': 0}
        output[arm] = package
    economics = {'arms': model_costs, 'original_model_bytes': ORIGINAL_MODEL_BYTES,
                 'selected_marginal_model_bytes': MARGINAL_MODEL_BYTES,
                 'headline_baseline': 'validated smaller fixed-marginal model; prior 22323-byte saving is not credited again',
                 'full_corpus_score_bytes': None, 'objective_credit_bytes': 0,
                 'development_probe': gate.artifact(gate.probe), 'development_probe_is_runtime_dependency': False,
                 'mutator_sources': source_members, 'native_binary_unchanged': True,
                 'meaning': 'Two-copy model arithmetic and inherited mixed diagnostic inventories are separate alternatives; no summed forecast or complete-package claim.'}
    gate.write('package-economics.json', economics)
    gate.required.add(gate.result / 'package-economics.json')
    return output, economics


def execute(gate):
    from lib import driver
    gate.retain_sources()
    gate.native = gate.work / 'native'
    for source, ref in gate.cached.items():
        target = gate.native / source.removeprefix(CACHED)
        gate.copy(source, target)
        target.chmod(0o555 if source == CACHED + 'cmix' else 0o444)
        gate.retained[target] = ref['sha256']
    gate.binaries[str(gate.native / 'cmix')] = RUNTIME['cmix'][1]
    synthetic_gate(gate)
    source = gate.native / 'models/6m-q4-fp32.tfwc2'
    rows, models = mutate_population(gate, 'model', source, expected_metadata=gate.metadata['tensors'], expected_histograms=gate.histograms)
    require(rows['D']['mapping_changed_symbols'] == 3119371 and rows['C']['mapping_changed_symbols'] == 3119371 and
            rows['C']['shift_changed_symbols_vs_D'] > 0 and
            rows['D']['output_tensor_events_digest'] != rows['C']['output_tensor_events_digest'], 'full-model treatment or misalignment control is inactive')
    for path in models.values():
        path.chmod(0o444)
        gate.retained[path] = sha(path)
    gate.write('model-comparisons.json', {'outputs': {arm: gate.artifact(path) for arm, path in models.items()},
                                        'direct_event_comparison_pass': True, 'independent_metadata_histogram_map_checks': True,
                                        'mapping': list(MAPPING), 'control': 'left rotate every mapped last-dimension row by one',
                                        'original_model_inversion_claimed_for_D_C': False, 'objective_credit_bytes': 0})
    gate.required.add(gate.result / 'model-comparisons.json')
    inventories, economics = packages(gate, models)
    verify_runtime(gate)
    gate.run('fixture-preprocess', [str(gate.native / 'cmix'), '-s', 'dictionary/english.dic', 'prof_input/input', 'fixture.stored'], 30, work=gate.native)
    verify_runtime(gate)
    compare_bytes(gate, gate.native / 'fixture.stored', gate.storage, 'fixture-storage')
    gate.required.add(gate.native / 'fixture.stored')
    native, comparisons = {}, []
    for arm in ARMS:
        output = gate.result / arm
        package = inventories[arm]
        result = driver.run(ID, gate.native / 'prof_input/input', RAW_BYTES, True,
                            run_purpose='diagnostic', run_scope_label=arm + '-public-fixture',
                            run_context='Fixed even7 lossy model parameters; exact corpus inverse; C rotates mapped rows',
                            run_source='canonical-tool', module=Codec(gate, arm, models[arm]), artifact_dir=output,
                            package_inventory=([(row['path'], row['bytes']) for row in package['counted_files']] +
                                               [('required-option-text', len(package['option_text'].encode()))], package))
        require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'], 'native inverse or repeat failed')
        archive = (output / 'archive.bin').read_bytes()
        compare_bytes(gate, output / 'restored.bin', gate.raw, arm + '-raw-inverse')
        compare_bytes(gate, output / 'repeat.bin', archive, arm + '-archive-repeat')
        archive_header(gate, archive)
        if arm in ('P', 'K'):
            compare_bytes(gate, output / 'archive.bin', gate.parent_archive, arm + '-parent-archive')
        reference = gate.native / (('P' if arm in ('P', 'K') else arm) + '-encode.trace')
        for phase in PHASES:
            comparisons.append(compare_trace(gate, reference, gate.native / (arm + '-' + phase + '.trace'), MODELED_BYTES * 8 * 28))
        artifacts = {name: gate.artifact(output / name) for name in ('result.json', 'archive.bin', 'repeat.bin', 'restored.bin')}
        gate.required.update(output / name for name in artifacts)
        native[arm] = {'artifacts': artifacts, 'archive_bytes': len(archive), 'archive_delta_vs_parent': len(archive) - 3223,
                       'roundtrip_ok': True, 'deterministic_ok': True, 'within_arm_coder_records_identical': True,
                       'original_parent_archive_required': arm in ('P', 'K'),
                       'native_loader_selected': 'K' if arm == 'K' else 'P',
                       'fixture_component_tradeoff_delta_vs_selected_marginal':
                           economics['arms'][arm]['conservative_two_copy_component_delta_vs_selected_marginal'] + len(archive) - 3223}
    require(len(gate.commands) == 107, 'fixed process population differs')
    gate.write('coder-records.json', {'record_bytes': 28, 'records_per_phase': MODELED_BYTES * 8,
                                    'P_K_match': True, 'D_C_each_match_own_replay': True,
                                    'D_P_or_C_P_equality_required': False, 'comparisons': comparisons})
    costs = {}
    for arm in ARMS:
        phases = [row for row in gate.commands if row['phase'] in {arm + '-' + phase for phase in PHASES}]
        require(len(phases) == 3 and all(row['returncode'] == 0 for row in phases), 'native phase receipts incomplete')
        cpu = [None if row['user_cpu_seconds'] is None or row['system_cpu_seconds'] is None else
               row['user_cpu_seconds'] + row['system_cpu_seconds'] for row in phases]
        costs[arm] = {'native_process_elapsed_seconds': sum(row['elapsed_seconds'] for row in phases),
                      'native_process_cpu_seconds': None if any(value is None for value in cpu) else sum(cpu),
                      'kernel_only_cpu_seconds': None, 'missing_diagnostics': ['kernel-only timer unavailable in immutable cached binary'],
                      'timing_scope': 'three independent native processes, including initialization, codec and trace I/O',
                      'timing_authority': 'shared-host diagnostic'}
    gate.write('native-costs.json', costs)
    gate.required.update(gate.result / name for name in ('coder-records.json', 'native-costs.json'))
    # Exact signed ceiling division; this is a cold-fixture budget forecast.
    projected_archive_penalty = (native['D']['archive_delta_vs_parent'] * 1_000_000_000 + RAW_BYTES - 1) // RAW_BYTES
    planning_delta = economics['arms']['D']['conservative_two_copy_component_delta_vs_selected_marginal'] + projected_archive_penalty
    return {'infrastructure_pass': True, 'synthetic_pass': True, 'model_event_comparisons_pass': True,
            'native_binary': gate.artifact(gate.native / 'cmix'), 'native_binary_reused_exactly': True,
            'native_phases': 12, 'mutator_compiles': 1, 'native_compiles': 0,
            'scope_bytes': RAW_BYTES, 'modeled_bytes': MODELED_BYTES, 'arms': native,
            'P_K_parent_identity': True, 'roundtrip_ok': True, 'deterministic_ok': True,
            'component_economic_pass': economics['arms']['D']['component_economic_pass'],
            'D_archive_penalty_bytes': native['D']['archive_delta_vs_parent'],
            'C_archive_penalty_bytes': native['C']['archive_delta_vs_parent'],
            'D_beats_C_archive': native['D']['archive_bytes'] < native['C']['archive_bytes'],
            'planning_delta_vs_selected_marginal_bytes': planning_delta,
            'planning_net_positive': planning_delta < 0,
            'planning_projected_archive_penalty_bytes': projected_archive_penalty,
            'planning_scope': 'Cold public 50051-byte fixture archive penalty linearly scaled to 1000000000 bytes, plus measured two-copy component delta and conservative source overhead versus the selected marginal model; budget selection only, not full-score or transfer evidence or scientific futility.',
            'misalignment_archive_effect_observed': (gate.result / 'D/archive.bin').read_bytes() != (gate.result / 'C/archive.bin').read_bytes(),
            'package_economics': economics, 'kernel_costs': costs}


def index_artifacts(gate, transient):
    """Index this gate's evidence, retaining exact missing-file diagnostics."""
    errors, artifacts = [], []
    excluded = {gate.result / name for name in ('stage-decision.json', 'artifacts.json', 'artifact-index-diagnostics.json')}
    def onerror(error):
        errors.append({'path': str(error.filename or gate.result), 'operation': 'enumerate', 'error': str(error)})
    for directory, directories, files in os.walk(gate.result, onerror=onerror, followlinks=False):
        base = Path(directory)
        directories[:] = [name for name in directories if base / name != transient]
        for name in sorted(directories + files):
            path = base / name
            if path == transient or transient in path.parents or path in excluded:
                continue
            try:
                info = path.lstat()
                if stat.S_ISREG(info.st_mode):
                    artifacts.append(gate.artifact(path))
                elif not stat.S_ISDIR(info.st_mode):
                    raise ValueError('artifact is not a regular file or directory')
            except (OSError, ValueError) as error:
                errors.append({'path': str(path.relative_to(ROOT)), 'operation': 'fingerprint', 'error': str(error)})
    indexed = {row['path'] for row in artifacts}
    for path in sorted(gate.required):
        if str(path.relative_to(ROOT)) not in indexed:
            errors.append({'path': str(path.relative_to(ROOT)), 'operation': 'mandatory-evidence', 'error': 'missing successful fingerprint'})
    return sorted(artifacts, key=lambda row: row['path']), {'complete': not errors, 'errors': errors,
                    'indexed_files': len(artifacts), 'required_files': len(gate.required),
                    'index_metadata_excluded': [str(path.relative_to(ROOT)) for path in sorted(excluded)]}


def main():
    load_helpers()
    validate = bool(sys.argv[1:])
    gate = NativeGate(ROOT, ID, CAPS, validate)
    validate_inputs(gate)
    if validate:
        print(json.dumps({'status': 'preflight_pass', 'inputs': len(gate.inputs), 'cached_native_files': len(gate.cached),
                          'synthetic_populations': 8, 'malformed_parent_controls': 20, 'planned_processes': 107,
                          'native_compiles': 0, 'codec_executed': False}))
        return 0
    gate.required = {gate.result / name for name in ('synthetic.json', 'model-comparisons.json', 'package-economics.json',
                                                     'coder-records.json', 'native-costs.json')}
    for arm in ARMS:
        gate.required.add(gate.result / (arm + '-package.json'))
        gate.required.update(gate.result / arm / name for name in ('result.json', 'archive.bin', 'repeat.bin', 'restored.bin'))
        gate.required.update(gate.work / 'native' / (arm + '-' + phase + '.trace') for phase in PHASES)
    stage = {'schema': 'gamma.enwiki9.fx2-weight-even7-fixture-stage.v1', 'candidate_id': ID, 'experiment': gate.reference,
             'objective': gate.contract['objective'],
             'status': 'running', 'infrastructure_pass': False, 'objective_credit_bytes': 0, 'full_corpus_score_bytes': None,
             'larger_gate_authorized': False, 'continuous_guard_decision': 'pending canonical outer guard closure',
             'dependency_closure_complete': False, 'license_audit_complete': False,
             'isolated_resource_qualification_complete': False, 'full_corpus_reconstruction_proven': False,
             'scope': 'public 50051-byte fixture; changed model predictions; no original-weight inversion for D/C',
             'economic_rule_is_infrastructure_requirement': False}
    try:
        stage.update(execute(gate), status='passed')
    except Exception as error:
        category = error.category if isinstance(error, GateFailure) else 'missing_or_unreadable_evidence' if isinstance(error, (OSError, KeyError, json.JSONDecodeError)) else 'invariant_failed'
        stage.update(status='execution_failed', infrastructure_pass=False, failure_class=category, error=type(error).__name__ + ': ' + str(error))
    stage['child_closure_ok'] = False
    try:
        gate.closure()
        stage['child_closure_ok'] = True
    except Exception as error:
        stage.update(status='execution_failed', infrastructure_pass=False, closure_error=str(error))
    cleanup = cleanup_native_transient(gate, stage['child_closure_ok'])
    if not cleanup['cleanup_complete'] or (stage['status'] == 'passed' and not cleanup['no_residual_before_cleanup']):
        stage.update(status='execution_failed', infrastructure_pass=False, transient_cleanup_error='owned PPM cleanup or successful-process absence failed')
    gate.write('transient-cleanup.json', cleanup)
    stage['transient_cleanup'] = gate.artifact(gate.result / 'transient-cleanup.json')
    stage['artifact_index_exclusions'] = [{'path': cleanup['path'], 'role': cleanup['role'], 'status': cleanup['status'],
                                          'residual_present': cleanup['residual_present'], 'reason': 'metadata-only owned PPM transient cleanup'}]
    try:
        gate.closure()
        gate.verify()
    except Exception as error:
        stage.update(status='execution_failed', infrastructure_pass=False, final_verification_error=str(error))
    stage['commands'] = gate.commands
    gate.write('stage-decision.json', {**stage, 'status': 'publishing' if stage['status'] == 'passed' else stage['status'],
                                       'infrastructure_pass': False, 'artifact_index_status': 'pending'})
    try:
        artifacts, diagnostics = index_artifacts(gate, gate.work / 'native/ppm.temp')
        stage['artifact_index_status'] = 'complete' if diagnostics['complete'] else 'incomplete'
        if not diagnostics['complete']:
            stage.update(status='execution_failed', infrastructure_pass=False, artifact_index_errors=diagnostics['errors'])
        gate.write('artifact-index-diagnostics.json', diagnostics)
        stage['artifact_index_diagnostics'] = gate.artifact(gate.result / 'artifact-index-diagnostics.json')
        gate.write('artifacts.json', artifacts)
        stage['artifacts'] = gate.artifact(gate.result / 'artifacts.json')
    except Exception as error:
        stage.update(status='execution_failed', infrastructure_pass=False, artifact_index_status='failed', artifact_index_error=str(error))
    gate.write('stage-decision.json', stage)
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
