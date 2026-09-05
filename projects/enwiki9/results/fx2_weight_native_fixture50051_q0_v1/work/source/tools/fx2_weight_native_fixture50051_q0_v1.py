#!/usr/bin/env python3
"""Integrate fixed weight marginals; gate package cost before exact native replay."""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ID = 'fx2_weight_native_fixture50051_q0_v1'
UPSTREAM = 'external/fx2-cmix-transformer-v1/'
PARENT = 'results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/'
MARGINAL = 'results/fx2_weight_marginal_roundtrip_q0_v1/work/'
MODEL = UPSTREAM + 'models/6m-q4-fp32.tfwc2'
SELECTED = MARGINAL + 'model.D'
NATIVE_ADAPTER = 'operations/provenance/public_fx2_weight_marginal_native_adapter_v1.json'
TRACE_ADAPTER = 'operations/provenance/public_fx2_argmax_native_adapter_v1.json'
CAPS = {'cpus': [2], 'memory_bytes': 9999998976, 'scratch_bytes': 16000000000, 'swap_bytes': 0, 'wall_seconds': 900}
FAST = '-DSEED=923 -DUPDATE_LIMIT=3000 -m64 -Wall -std=c++17 -include cstdint -fno-fast-math -fno-math-errno -fno-exceptions -fno-threadsafe-statics -march=x86-64-v3 -mtune=generic -mrecip=none -fdata-sections -ffunction-sections'
FLAGS = ['-std=c++17', '-O2', '-Wall', '-Wextra', '-fno-fast-math', '-ffp-contract=off', '-fno-math-errno', '-march=x86-64-v3', '-mtune=generic', '-mrecip=none']
ARMS = ('P', 'K', 'D')
MODELED = 32478
POPULATIONS = {'zero_tensors', 'uniform_marginal', 'skewed_marginal', 'heterogeneous_tensors', 'empty_and_scalar', 'all_tags_and_rows', 'range_adaptation_stress', 'maximum_native_dimensions'}


def load_helpers():
    """Execute the exact bound helper source, bypassing pre-existing bytecode."""
    contract_path = 'operations/adaptive/experiments/' + ID + '.json'
    content = (ROOT / contract_path).read_bytes()
    if sys.argv[1:] != ['--validate-only']:
        reference = json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON'])
        if reference['path'] != contract_path or hashlib.sha256(content).hexdigest() != reference['sha256'].removeprefix('sha256:'):
            raise ValueError('experiment changed before loading helper')
    contract = json.loads(content)
    inputs = {row['path']: row for row in contract['inputs']}
    buffers = {}
    for source in ('tools/' + ID + '.py', 'lib/fx2_native_gate_v1.py', 'lib/artifacts.py'):
        path = ROOT / source
        if path.resolve() != path:
            raise ValueError('aliased bootstrap source')
        buffers[source] = path.read_bytes()
        if hashlib.sha256(buffers[source]).hexdigest() != inputs[source]['sha256'].removeprefix('sha256:'):
            raise ValueError('bootstrap source changed')
    namespace = {}
    exec(compile(buffers['lib/fx2_native_gate_v1.py'], str(ROOT / 'lib/fx2_native_gate_v1.py'), 'exec'), namespace)
    globals().update({name: namespace[name] for name in ('GateFailure', 'NativeGate', 'read', 'require', 'sha')})


def validate_consumed_inputs(gate):
    audit = json.loads(gate.buffers['operations/provenance/public_fx2_cmix_transformer_v1.json'])
    paths = [row['path'] for row in audit['build_source_files']]
    require(len(paths) == len(set(paths)) == 131, 'upstream build closure differs')
    for row in audit['build_source_files']:
        source = UPSTREAM + row['path']
        require(len(gate.buffers[source]) == row['bytes'] and gate.inputs[source]['sha256'].removeprefix('sha256:') == row['sha256'], 'upstream source audit differs')
        require(PARENT + 'work/' + row['path'] in gate.buffers, 'missing source accounting baseline')
    manifest = json.loads(gate.buffers[MARGINAL + 'fixtures/manifest.json'])
    require(len(manifest['valid']) == 8 and {r['id'] for r in manifest['valid']} == POPULATIONS, 'synthetic populations differ')
    negatives = [r for r in manifest['rejection'] if r['mode'] == 'restore']
    require(len(negatives) == len({r['id'] for r in negatives}) == 20, 'marginal negative controls differ')
    refs = [r[k] for r in manifest['valid'] for k in ('parent', 'raw_reference', 'expected_D', 'expected_G')] + [r['input'] for r in negatives]
    for ref in refs:
        require(Path(ref['path']).name == ref['path'], 'fixture path escapes population')
        path = MARGINAL + 'fixtures/' + ref['path']
        require(path in gate.buffers and len(gate.buffers[path]) == ref['bytes'] and gate.inputs[path]['sha256'].removeprefix('sha256:') == ref['sha256'], 'fixture is missing or not bound to manifest')
    require(len(gate.buffers[MODEL]) == 2930652 and hashlib.sha256(gate.buffers[MODEL]).hexdigest() == '7f4db6c8c843a7e6264b6a48ed4805e9e431f543df7a9a0ecb37a35a5e4b8860', 'original trained model differs')
    require(len(gate.buffers[SELECTED]) == 2908329 and hashlib.sha256(gate.buffers[SELECTED]).hexdigest() == '5cae4299a64af88b88a637f3c14e9ee54a5fd98c559e391f35dfa7d832b00e4a', 'selected D model differs')


def activation(gate, phase, arms):
    lines = (gate.result / (phase + '.stderr')).read_bytes().splitlines()
    found = [line for line in lines if line.startswith(b'Gamma weight loader selected=')]
    expected = []
    for arm in arms:
        expected.append(('Gamma weight loader selected=' + arm + ' tensors=434 histogram_tensors=' + ('0' if arm == 'P' else '111') + ' histogram_symbols=' + ('0' if arm == 'P' else '5868864') + ' side_information_bytes=' + ('7169' if arm == 'D' else '0') + ' canonical=' + ('1' if arm == 'D' else '0')).encode())
    require(found == expected, 'loader activation differs in ' + phase)


class Codec:
    def __init__(self, gate, native, arm):
        self.gate, self.native, self.arm, self.count = gate, native, arm, 0
        self.model = 'models/model.D' if arm == 'D' else 'models/6m-q4-fp32.tfwc2'

    def invoke(self, name, arguments):
        env = {'GAMMA_FX2_CODER_TRACE': str(self.native / (name + '.trace'))}
        if self.arm != 'P':
            env['GAMMA_FX2_WEIGHT_BOOKKEEPING'] = '1'
        self.gate.run(name, [str(self.native / 'cmix'), *arguments, '--transformer', self.model], 120, env, work=self.native)
        activation(self.gate, name, [self.arm])

    def compress(self, raw):
        name = self.arm + ('-encode' if self.count == 0 else '-reencode')
        self.count += 1
        with (self.native / (name + '.raw')).open('xb') as handle:
            handle.write(raw)
        self.invoke(name, ['-c', 'dictionary/english.dic', name + '.raw', name + '.cmix'])
        return (self.native / (name + '.cmix')).read_bytes()

    def decompress(self, archive):
        name = self.arm + '-decode'
        with (self.native / (name + '.cmix')).open('xb') as handle:
            handle.write(archive)
        self.invoke(name, ['-d', 'dictionary/english.dic', name + '.cmix', name + '.raw'])
        return (self.native / (name + '.raw')).read_bytes()


def execute(gate):
    from lib import driver
    gate.retain_sources()
    audit = json.loads(gate.buffers['operations/provenance/public_fx2_cmix_transformer_v1.json'])
    native = gate.work / 'native'
    for row in audit['build_source_files']:
        gate.copy(UPSTREAM + row['path'], native / row['path'])
    gate.adapter('operations/provenance/public_fx2_static_vocab_adapter_v1.json', native)
    gate.adapter(NATIVE_ADAPTER, native)
    gate.adapter(TRACE_ADAPTER, native, {'src/coder/encoder.cpp', 'src/coder/decoder.cpp'})
    gate.copy('tools/fx2_coder_trace_v1.hpp', native / 'src/coder/gamma-coder-trace.h')
    gate.copy(SELECTED, native / 'models/model.D')
    # Both reference assets remain diagnostic inputs; deployment inventories
    # below include exactly the arm's required model.
    require(sha(native / 'src/models/byte-model.cpp') == sha(ROOT / (UPSTREAM + 'src/models/byte-model.cpp')), 'unrequested argmax mutation')
    for name in ('fx2_weight_native_compare_v1.cpp',):
        gate.copy('tools/' + name, native / 'cpp_infer/src' / name)
    common = [str(native / 'cpp_infer/src' / p) for p in ('weights_io.cpp', 'weights_io_compressed.cpp')]
    for name, source in [('compare', 'fx2_weight_native_compare_v1.cpp'), ('raw-check', 'test_weights_compressed.cpp')]:
        binary = gate.work / name
        gate.run('compile-' + name, ['/usr/bin/g++', *FLAGS, str(native / 'cpp_infer/src' / source), *common, '-o', str(binary), '-lm'], 120)
        gate.binaries[str(binary)] = sha(binary)
    manifest = json.loads(gate.buffers[MARGINAL + 'fixtures/manifest.json'])
    checks = []
    for row in manifest['valid']:
        for arm, key in [('P', 'parent'), ('K', 'parent'), ('D', 'expected_D'), ('G', 'expected_G')]:
            name = 'synthetic-' + row['id'] + '-' + arm
            gate.run(name, [str(gate.work / 'raw-check'), str(ROOT / (MARGINAL + 'fixtures/' + row['raw_reference']['path'])), str(ROOT / (MARGINAL + 'fixtures/' + row[key]['path']))], 15, {'GAMMA_FX2_WEIGHT_BOOKKEEPING': '1'} if arm != 'P' else {})
            output = (gate.result / (name + '.stdout')).read_text().strip()
            expected = f"OK: {row['tensor_count']} tensors, {row['tensor_payload_bytes'] + row['regenerated_rope_bytes']} payload bytes bit-identical"
            require(output == expected, 'synthetic tensor equality evidence differs')
            checks.append({'population': row['id'], 'arm': arm, 'exact': True})
    rejected = []
    raw_reference = ROOT / (MARGINAL + 'fixtures/' + next(row for row in manifest['valid'] if row['id'] == 'heterogeneous_tensors')['raw_reference']['path'])
    for row in manifest['rejection']:
        if row['mode'] != 'restore':
            continue  # Existing P parser semantics are preserved, not hardened here.
        name = 'reject-' + row['id']
        gate.run(name, [str(gate.work / 'raw-check'), str(raw_reference), str(ROOT / (MARGINAL + 'fixtures/' + row['input']['path']))], 15, accepted=(1,))
        require(b'weights_io_compressed:' in (gate.result / (name + '.stderr')).read_bytes(), 'negative did not fail in loader')
        rejected.append(row['id'])
    gate.write('synthetic.json', {'exact_comparisons': checks, 'loader_rejections': rejected})
    comparisons = []
    for arm in ARMS:
        target = native / ('models/model.D' if arm == 'D' else 'models/6m-q4-fp32.tfwc2')
        name = 'model-' + arm
        gate.run(name, [str(gate.work / 'compare'), str(native / 'models/6m-q4-fp32.tfwc2'), str(target)], 30, {'GAMMA_FX2_WEIGHT_BOOKKEEPING': '1'} if arm != 'P' else {})
        activation(gate, name, ['P', arm])
        comparison = read(gate.result / (name + '.stdout'))
        require(comparison['tensor_count'] == 434 and comparison['payload_bytes'] == 39588806 and comparison['exact_byte_comparison'] and comparison['reference_digest_hex'] == comparison['target_digest_hex'], 'complete tensor comparison evidence differs')
        comparisons.append({'arm': arm, 'result': gate.artifact(gate.result / (name + '.stdout'))})
    gate.write('tensor-comparisons.json', {'all_exact': True, 'comparisons': comparisons})
    gate.run('compile-native', ['/usr/bin/make', '-j1', 'cmix', 'CC=/usr/bin/g++', 'CPPFLAGS_PART-THAT-SHOULD-BE-FAST=' + FAST + ' -O3', 'CPPFLAGS_PART-THAT-CAN-BE-SLOW=' + FAST + ' -Os'], 180, work=native)
    binary = gate.artifact(native / 'cmix')
    gate.binaries[str(native / 'cmix')] = binary['sha256']
    gate.run('disassemble', ['/usr/bin/objdump', '-d', '--insn-width=16', 'cmix'], 30, work=native)
    require(re.search(r'\b(?:v?(?:rcp|rsqrt)(?:14|28)?(?:ss|ps))\b|%zmm|%k[0-7]|\{vex\}|\t62 [0-9a-f][0-9a-f] ', (gate.result / 'disassemble.stdout').read_text()) is None, 'forbidden reciprocal or AVX512 instruction')
    gate.run('dynamic-dependencies', ['/usr/bin/objdump', '-p', 'cmix'], 15, work=native)
    gate.run('parent-dynamic-dependencies', ['/usr/bin/objdump', '-p', str(ROOT / (PARENT + 'work/cmix'))], 15, work=native)
    needed = lambda phase: re.findall(r'^\s+NEEDED\s+(\S+)', (gate.result / (phase + '.stdout')).read_text(), re.M)
    require(needed('dynamic-dependencies') == needed('parent-dynamic-dependencies'), 'new dynamic dependency requires a new accounting gate')
    sources = [gate.artifact(native / row['path']) for row in audit['build_source_files']]
    sources += [gate.artifact(native / 'src/coder/gamma-coder-trace.h')]
    parent_binary = gate.artifact(ROOT / (PARENT + 'work/cmix'))
    model_delta = len(gate.buffers[SELECTED]) - len(gate.buffers[MODEL])
    source_delta = sum(row['bytes'] for row in sources) - sum(len(gate.buffers[PARENT + 'work/' + row['path']]) for row in audit['build_source_files'])
    binary_delta = binary['bytes'] - parent_binary['bytes']
    # Use the same deployment argument spelling "model" for each alternative.
    # The gate's arm-selection and trace environments are diagnostics only.
    options = '-c dictionary input archive --transformer model\n-d dictionary archive output --transformer model\n'
    economics = {'model_delta_per_copy': model_delta, 'binary_delta_per_copy': binary_delta, 'raw_source_delta': source_delta, 'runtime_pair_delta': 2 * (binary_delta + model_delta), 'source_compressor_plus_decoder_delta': source_delta + binary_delta + 2 * model_delta, 'option_text': options, 'option_delta_bytes': 0, 'parent_binary': parent_binary, 'native_binary': binary, 'needed_libraries_identical': True, 'dependency_closure_complete': False, 'full_corpus_score_bytes': None, 'meaning': 'Incremental raw counted components against pinned source-built parent. Runtime pair and source-compressor alternatives are separate; neither is an awarded score. Both count two required model copies. Existing source/runtime and licensing gaps remain open.'}
    economics['pre_corpus_economic_gate_pass'] = max(economics['runtime_pair_delta'], economics['source_compressor_plus_decoder_delta']) < 0
    gate.write('package-economics.json', economics)
    if not economics['pre_corpus_economic_gate_pass']:
        raise GateFailure('economic_budget_stop', 'native program/source overhead exhausts the two-copy model saving')
    arm_results = {}
    parent_archive = gate.buffers[PARENT + 'work/fixture.cmix']
    for arm in ARMS:
        model = native / ('models/model.D' if arm == 'D' else 'models/6m-q4-fp32.tfwc2')
        files = sources + [binary, gate.artifact(model), gate.artifact(native / 'dictionary/english.dic')]
        package = {'counted_files': files, 'option_text': options, 'counted_bytes': sum(row['bytes'] for row in files) + len(options.encode()), 'dependency_closure_complete': False, 'diagnostic_parent_asset_in_source_inventory': True, 'source_runtime_overlap_counted_twice': True, 'unresolved': read(ROOT / (PARENT + 'package.json'))['unresolved']}
        require(package['counted_bytes'] <= 10000000, 'raw source/runtime inventory ceiling exceeded')
        gate.write(arm + '-package.json', package)
        result = driver.run(ID, native / 'prof_input/input', 50051, True, run_purpose='diagnostic', run_scope_label=arm + '-public-fixture', run_context='Native fixed weight marginals; original argmax; exact loaded tensors and coder records', run_source='canonical-tool', module=Codec(gate, native, arm), artifact_dir=gate.result / arm, package_inventory=([(row['path'], row['bytes']) for row in files] + [('required-option-text', len(options.encode()))], package))
        require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'], 'native inversion or repeat failed')
        require((gate.result / arm / 'archive.bin').read_bytes() == parent_archive, 'native archive differs from original parent')
        for phase in ('encode', 'decode', 'reencode'):
            gate.compare_trace(native / 'P-encode.trace', native / (arm + '-' + phase + '.trace'), MODELED * 8 * 28)
        arm_results[arm] = {'result': gate.artifact(gate.result / arm / 'result.json'), 'exact_parent_archive': True, 'exact_inverse': True, 'exact_repeat': True}
    traces = [gate.compare_trace(native / 'P-encode.trace', native / (arm + '-' + phase + '.trace'), MODELED * 8 * 28) for arm in ARMS for phase in ('encode', 'decode', 'reencode')]
    gate.write('coder-records.json', {'record_bytes': 28, 'records_per_phase': MODELED * 8, 'all_exact': True, 'comparisons': traces})
    return {'native_binary': binary, 'arms': arm_results, 'tensor_comparison_pass': True, 'pre_corpus_economic_gate_pass': True, 'coder_records_identical': True, 'all_archives_match_original_parent': True, 'archive_saved_bytes': 0, 'package_economics': economics}


def main():
    load_helpers()
    require(sys.argv[1:] in ([], ['--validate-only']), 'unexpected arguments')
    validate = bool(sys.argv[1:])
    gate = NativeGate(ROOT, ID, CAPS, validate)
    validate_consumed_inputs(gate)
    if validate:
        print(json.dumps({'status': 'preflight_pass', 'inputs': len(gate.inputs), 'codec_executed': False}))
        return 0
    stage = {'schema': 'gamma.enwiki9.fx2-weight-native-stage.v1', 'candidate_id': ID, 'experiment': gate.reference, 'objective_credit_bytes': 0, 'full_corpus_score_bytes': None, 'larger_gate_authorized': False, 'continuous_guard_decision': 'pending canonical outer guard closure'}
    try:
        stage.update(execute(gate), status='passed')
    except Exception as error:
        category = error.category if isinstance(error, GateFailure) else 'missing_or_unreadable_evidence' if isinstance(error, (OSError, KeyError, json.JSONDecodeError)) else 'invariant_failed'
        stage.update(status='budget_stopped' if category == 'economic_budget_stop' else 'execution_failed', failure_class=category, error=type(error).__name__ + ': ' + str(error))
    try:
        gate.closure()
        gate.verify()
        stage['child_closure_ok'] = True
    except Exception as error:
        stage.update(status='execution_failed', closure_error=str(error))
    stage['commands'] = gate.commands
    gate.write('artifacts.json', [gate.artifact(path) for path in sorted(gate.result.rglob('*')) if path.is_file()])
    stage['artifacts'] = gate.artifact(gate.result / 'artifacts.json')
    gate.write('stage-decision.json', stage)
    return 0 if stage['status'] in ('passed', 'budget_stopped') else 1


if __name__ == '__main__':
    raise SystemExit(main())
