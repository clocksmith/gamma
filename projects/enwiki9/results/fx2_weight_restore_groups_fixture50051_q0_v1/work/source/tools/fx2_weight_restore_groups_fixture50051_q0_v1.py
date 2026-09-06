#!/usr/bin/env python3
"""Independent group restorations into the failed even7 model; diagnostic only."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ID = 'fx2_weight_restore_groups_fixture50051_q0_v1'
BASE = 'tools/fx2_weight_even7_fixture50051_q0_v1.py'
SAFE = 'tools/fx2_weight_native_transfer250k_q0_v1.py'
PROBE = 'tools/fx2_weight_restore_group_probe_v1.cpp'
UNIT = 'operations/evidence/20260906_fx2_group_restoration_unit.json'
PARENT_ID = 'fx2_weight_even7_fixture50051_q0_v1'
PARENT = 'results/' + PARENT_ID + '/'
AUDIT = 'operations/provenance/public_fx2_weight_even7_terminal_20260906.json'
REFLECTION = 'operations/adaptive/reflections/20260906T001115Z_fcb2f27fea.json'
ORIGINAL = PARENT + 'work/models/model/P.tfwc2'
QUANTIZED = PARENT + 'work/models/model/D.tfwc2'
ARMS = tuple('PQKEARUV')
CAPS = {'cpus': [2], 'memory_bytes': 9999998976, 'scratch_bytes': 16000000000,
        'swap_bytes': 0, 'wall_seconds': 1800}
PINNED = {
    BASE: 'defb7e7b1f9a4e9a149df7bc204bdb4d13f4281e19287703e3fae955dd7745d1',
    PROBE: '15db72ddf5f03a0dad75c2d7eb5fda10247fa59490a1ecead51557233fb4fc4d',
    UNIT: 'f11e014b4feee2aa1dbe70136f792da79849859ec860d9c0a774a7e43e6a8cb4',
    AUDIT: '1748b806702947e542a826fe4a8d8fceb6d77483353844381dfeeba315252b1e',
    REFLECTION: 'f260dff3f3cbeb07b7bcc54c43c9185e264bc78483516336b047e209541364d9',
}


def bound_module(name, source, data):
    module = types.ModuleType(name)
    module.__file__, module.__package__ = str(ROOT / source), 'lib' if source.startswith('lib/') else ''
    sys.modules[name] = module
    exec(compile(data, module.__file__, 'exec'), module.__dict__)
    return module


def load_helpers():
    if sys.argv[1:] not in ([], ['--validate-only']):
        raise ValueError('unexpected arguments')
    contract_path = 'operations/adaptive/experiments/' + ID + '.json'
    content = (ROOT / contract_path).read_bytes()
    if not sys.argv[1:] and json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) != {
            'path': contract_path, 'sha256': 'sha256:' + hashlib.sha256(content).hexdigest()}:
        raise ValueError('experiment changed before helper load')
    inputs = {row['path']: row for row in json.loads(content)['inputs']}
    buffers = {}
    for source in ('tools/' + ID + '.py', 'lib/fx2_native_gate_v1.py', 'lib/artifacts.py', BASE, SAFE):
        path = ROOT / source
        if path.resolve() != path:
            raise ValueError('aliased bootstrap source')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != inputs[source]['sha256'].removeprefix('sha256:'):
            raise ValueError('bootstrap source changed: ' + source)
        buffers[source] = data
    helper = bound_module('bound_group_native_gate', 'lib/fx2_native_gate_v1.py', buffers['lib/fx2_native_gate_v1.py'])
    globals().update({name: getattr(helper, name) for name in ('GateFailure', 'NativeGate', 'require', 'sha')})
    safe = bound_module('bound_group_transfer_safety', SAFE, buffers[SAFE])
    safe.require, safe.sha = require, sha
    base = bound_module('bound_group_even7_operations', BASE, buffers[BASE])
    base.require, base.sha = require, sha
    for name in ('bound_ref', 'compare_bytes', 'compare_trace', 'cleanup_native_transient'):
        setattr(base, name, getattr(safe, name))
    globals()['base'] = base


def group(name):
    if name in ('embedding.weight.q', 'prior_embedding.weight.q', 'unembedding.weight.q'):
        return 'E'
    match = re.fullmatch(r'blocks\.([0-9]+)\.(.+)', name)
    require(match is not None and str(int(match[1])) == match[1] and int(match[1]) < 12, 'unknown tensor group')
    block, field = int(match[1]), match[2]
    if field in ('mlp.up.weight.q', 'mlp.down.weight.q'):
        return 'U' if field == 'mlp.up.weight.q' else 'V'
    common = {f'attention.{site}_projection.weight.q' for site in ('query', 'key', 'value', 'output')}
    gates = {f'attention.{gate}_gate_projection.{site}.weight.q' for gate in ('forget', 'output') for site in ('up', 'down')}
    require(field in common or (block % 4 != 3 and field in gates), 'unknown attention tensor group')
    return 'A' if block % 4 == 3 else 'R'


def validate_inputs(gate):
    for source, digest in PINNED.items():
        base.bound_ref(gate, {'path': source, 'sha256': digest})
    audit, reflection = json.loads(gate.buffers[AUDIT]), json.loads(gate.buffers[REFLECTION])
    require(audit['candidate_id'] == PARENT_ID and audit['validity'] == 'valid' and
            reflection['candidateId'] == PARENT_ID and reflection['validity']['valid'] is True,
            'even7 diagnostic ancestry is invalid')
    require(reflection['decision']['verdict'] == 'hold' and reflection['decision']['promotionPredicatesPass'] is False,
            'unexpected even7 reflection decision')
    require(gate.contract['parent'] == {'candidateId': PARENT_ID, 'revision': audit['candidate_revision']} and
            gate.contract['objective'] == reflection['objective'], 'scientific parent or active objective differs')
    require(any(row['path'] == AUDIT and row['sha256'].removeprefix('sha256:') == PINNED[AUDIT]
                for row in reflection['evidence']), 'reflection does not bind even7 audit')
    # The retained helper validates its original native cache antecedent, not
    # this candidate's scientific parent. Give it a separate cache-validation
    # view; the actual contract above and NativeGate authority remain unchanged.
    cache_view = copy.copy(gate)
    cache_view.contract = {**gate.contract, 'parent': {'candidateId': base.PARENT_ID,
                           'revision': json.loads(gate.buffers[base.NATIVE_AUDIT])['candidate_revision']}}
    base.validate_inputs(cache_view)
    for name in ('cached', 'parent_packages', 'parent_archive', 'raw', 'storage', 'vocabulary', 'metadata',
                 'histograms', 'fixture_manifest', 'negatives'):
        setattr(gate, name, getattr(cache_view, name))
    indexed = {row['path']: row for row in audit['artifacts']}
    required = (ORIGINAL, QUANTIZED, PARENT + 'P/archive.bin', PARENT + 'D/archive.bin',
                PARENT + 'work/native/P-encode.trace', PARENT + 'work/native/D-encode.trace')
    for path in required:
        base.bound_ref(gate, indexed[path])
    require(gate.buffers[ORIGINAL] == gate.buffers[base.CACHED + 'models/6m-q4-fp32.tfwc2'] and
            len(gate.buffers[QUANTIZED]) == 2066802 and len(gate.buffers[PARENT + 'D/archive.bin']) == 4430,
            'original/even7 anchors differ')
    require(audit['scientific_measurements']['infrastructure_pass'] and audit['resources']['cleanup_complete'] and
            not any(audit['resources']['guard_flags'].values()), 'even7 terminal closure is invalid')
    unit = json.loads(gate.buffers[UNIT])
    require(unit['passed'] and not unit['model_accessed'] and not unit['corpus_launched'], 'group unit antecedent differs')
    for ref in unit['source_bindings']:
        base.bound_ref(gate, ref)
    require(re.findall(rb'^\s*#\s*include\s*"([^"]+)"', gate.buffers[PROBE], re.M) ==
            [b'fx2_weight_even7_probe_v1.cpp'], 'group probe include closure differs')
    gate.groups = {key: {'tensors': 0, 'events': 0, 'changed': 0} for key in 'EARUV'}
    for index, counts in gate.histograms.items():
        selected = gate.groups[group(gate.metadata['tensors'][index]['name'])]
        selected['tensors'] += 1
        selected['events'] += sum(counts)
        selected['changed'] += sum(value for symbol, value in enumerate(counts) if base.MAPPING[symbol] != symbol-7)
    require({key: row['tensors'] for key, row in gate.groups.items()} == {'E': 3, 'A': 12, 'R': 72, 'U': 12, 'V': 12} and
            sum(row['events'] for row in gate.groups.values()) == 5868864 and
            sum(row['changed'] for row in gate.groups.values()) == 3119371, 'group partition differs')


def models(gate):
    gate.probe = gate.work / 'restore-groups-probe'
    gate.run('compile-mutator', ['/usr/bin/g++', *base.FLAGS, str(gate.work / 'source' / PROBE), '-o', str(gate.probe)], 120)
    gate.binaries[str(gate.probe)] = sha(gate.probe)
    gate.run('synthetic-self-test', [str(gate.probe), '--self-test'], 30)
    unit = json.loads((gate.result / 'synthetic-self-test.stdout').read_bytes())
    require(unit['passed'] and unit['arms'] == 8 and unit['groups'] == 5 and unit['signed_values_per_group'] == 15 and
            unit['exceptional_raw_bit_patterns'] == 6 and unit['unknown_group_rejections'] == 4 and not unit['model_accessed'],
            'fresh synthetic unit failed')
    gate.write('synthetic.json', unit)
    original, quantized = gate.work / 'original.tfwc2', gate.work / 'even7.tfwc2'
    gate.copy(ORIGINAL, original); gate.copy(QUANTIZED, quantized)
    for path in (original, quantized):
        path.chmod(0o444); gate.retained[path] = sha(path)
    gate.required.update((gate.probe, original, quantized))
    outputs, comparisons = {}, {}
    directory = gate.work / 'models'; directory.mkdir()
    for arm in ARMS:
        expected = {'tensors': 111, 'events': 5868864, 'changed': 3119371} if arm == 'P' else gate.groups.get(arm, {'tensors': 0, 'events': 0, 'changed': 0})
        rows = []
        for suffix in ('', '.repeat'):
            output = directory / (arm + suffix + '.tfwc2')
            phase = 'model-' + arm + ('-repeat' if suffix else '')
            gate.run(phase, [str(gate.probe), arm, str(original), str(quantized), str(output)], 30)
            row = json.loads((gate.result / (phase + '.stdout')).read_bytes())
            require(row['schema'] == 'gamma.fx2-group-restoration.v1' and row['arm'] == arm and
                    all(row[key] is True for key in ('direct_parameter_comparison', 'canonical_repeat', 'fresh_repeat', 'non_int4_bits_unchanged')),
                    'model restoration proof failed')
            require(row['model_bytes'] == output.stat().st_size and row['restored_tensors'] == expected['tensors'] and
                    row['restored_events'] == expected['events'] and row['restored_changed_events'] == expected['changed'] and
                    row['remaining_changed_events'] == 3119371-expected['changed'] and
                    row['bookkeeping_tensors'] == (111 if arm == 'K' else 0), 'group activation/counts differ')
            require(not Path(str(output) + '.partial').exists(), 'model publication incomplete')
            if arm in ('P', 'Q', 'K'):
                base.compare_bytes(gate, output, gate.buffers[ORIGINAL if arm == 'P' else QUANTIZED], phase + '-anchor')
            output.chmod(0o444); gate.retained[output] = sha(output)
            gate.required.update((output, gate.result / (phase + '.stdout'), gate.result / (phase + '.execution.json')))
            rows.append(row)
            if not suffix:
                outputs[arm] = output
            else:
                base.compare_bytes(gate, output, outputs[arm].read_bytes(), phase)
        require(rows[0] == rows[1], 'fresh model receipts differ')
        comparisons[arm] = {'model': gate.artifact(outputs[arm]), **rows[0]}
    gate.write('model-comparisons.json', {'groups': gate.groups, 'arms': comparisons,
                'each_group_starts_from_same_even7': True, 'cumulative_restoration': False,
                'inference_probability_identity_inferred_from_tensor_hash': False})
    return outputs, comparisons


def packages(gate, output_models):
    baseline = gate.parent_packages['P']
    model_index = max(i for i, row in enumerate(baseline['counted_files']) if row['path'] == base.CACHED + 'models/6m-q4-fp32.tfwc2')
    output, economics = {}, {}
    for arm in ARMS:
        files = [gate.artifact(gate.native / row['path'].removeprefix(base.CACHED)) for row in baseline['counted_files']]
        files[model_index] = gate.artifact(output_models[arm])
        sources = [] if arm == 'P' else [base.PROBE, base.HEADER] + ([PROBE] if arm in 'EARUV' else [])
        source_refs = [gate.artifact(gate.work / 'source' / path) for path in sources]
        recipe = ''
        if arm != 'P':
            recipe = base.PROBE_BUILD_OPTIONS + 'probe D original.tfwc2 even7.tfwc2\n'
        if arm in 'EARUV':
            recipe += 'g++ ' + ' '.join(base.FLAGS) + ' ' + PROBE + ' -o restore-groups\n'
            recipe += 'restore-groups ' + arm + ' original.tfwc2 even7.tfwc2 restored.tfwc2\n'
        options = base.OPTIONS + recipe
        files += source_refs
        package = {'counted_files': files, 'option_text': options,
                   'counted_bytes': sum(row['bytes'] for row in files) + len(options.encode()),
                   'dependency_closure_complete': False, 'source_runtime_overlap_counted_twice': True,
                   'diagnostic_original_model_in_source_inventory': True, 'unresolved': baseline['unresolved'],
                   'meaning': 'Inherited mixed source/runtime diagnostic inventory; ship the restored runtime model, retain original source asset and explicit two-stage model-generation recipe. No complete submission accounting.'}
        gate.write(arm + '-package.json', package); output[arm] = package
        size, added = output_models[arm].stat().st_size, sum(row['bytes'] for row in source_refs) + len(recipe.encode())
        economics[arm] = {'model_bytes': size, 'added_mutator_source_and_options_bytes': added,
                         'native_binary_delta_bytes': 0, 'per_copy_model_delta_vs_original': size-2930652,
                         'per_copy_model_delta_vs_selected_marginal': size-2908329,
                         'two_copy_component_delta_vs_selected_marginal': 2*(size-2908329)+added,
                         'two_copy_component_delta_vs_original': 2*(size-2930652)+added,
                         'diagnostic_inventory_bytes': package['counted_bytes']}
    for arm, row in economics.items():
        row['model_byte_increase_vs_Q'] = row['model_bytes']-economics['Q']['model_bytes']
        row['two_copy_component_delta_vs_Q'] = row['two_copy_component_delta_vs_selected_marginal']-economics['Q']['two_copy_component_delta_vs_selected_marginal']
    gate.write('package-economics.json', {'arms': economics, 'complete_package_bytes': None,
               'full_corpus_score_bytes': None, 'objective_credit_bytes': 0,
               'model_generation_inputs_are_not_extra_runtime_dependencies': True,
               'development_binary': gate.artifact(gate.probe), 'development_binary_counted_as_runtime': False})
    return output, economics


def probability_diagnosis(gate):
    count, mask = base.MODELED_BYTES*8, (1 << 32)-1
    anchors = {arm: (gate.native / (arm + '-encode.trace')).read_bytes() for arm in ('P', 'Q')}
    output = {}
    for arm in ARMS:
        path = gate.native / (arm + '-encode.trace')
        data = path.read_bytes()
        require(len(data) == count*28, 'diagnostic trace size differs')
        first, changed = dict.fromkeys(anchors), dict.fromkeys(anchors, 0)
        thirds, before = [[], [], []], (0, mask)
        for index, row in enumerate(struct.iter_unpack('<7I', data)):
            bits, q, low, high, after_low, after_high, truth = row
            p = struct.unpack('<f', struct.pack('<I', bits))[0]
            require(math.isfinite(p) and 0 <= p <= 1 and 1 <= q <= 65535 and (low, high) == before and low <= high,
                    'invalid probability or coder continuity')
            require(truth == ((gate.storage[10 + index//8] >> (7-index%8)) & 1), 'trace truth differs from stored WRT body')
            width = high-low+1; split = ((width-1)*q)//65536
            selected = split+1 if truth else width-1-split
            require(selected > 0, 'zero arithmetic interval')
            thirds[min(2, 3*index//count)].append(math.log2(width)-math.log2(selected))
            a, b = (low, low+split) if truth else (low+split+1, high)
            while ((a ^ b) & 0xff000000) == 0:
                a, b = (a << 8) & mask, ((b << 8) + 255) & mask
            require((a, b) == (after_low, after_high), 'recorded arithmetic transition differs')
            before = (a, b)
            for parent, reference in anchors.items():
                if data[index*28:index*28+8] != reference[index*28:index*28+8]:
                    changed[parent] += 1
                    if first[parent] is None:
                        first[parent] = index
        totals = [math.fsum(values) for values in thirds]
        output[arm] = {'trace': gate.artifact(path), 'effective_interval_bits': math.fsum(totals),
                       'chronological_thirds_bits': totals, 'first_probability_difference_bit': first,
                       'changed_probability_records': changed, 'truth_and_coder_transitions_verified': True}
    for row in output.values():
        for parent in ('P', 'Q'):
            row['delta_vs_' + parent + '_bits'] = row['effective_interval_bits']-output[parent]['effective_interval_bits']
    gate.write('probability-loss-diagnosis.json', {'arms': output, 'record_bytes': 28, 'records_per_arm': count,
               'arithmetic': 'binary64 log2 and fsum; diagnostic effective interval loss, not an archive size',
               'definition': 'log2(high-low+1) minus log2(bit1 ? floor((high-low)*q/65536)+1 : high-low-floor((high-low)*q/65536))',
               'scope': 'examined public development fixture; interactions are nonadditive; no successor selected',
               'objective_credit_bytes': 0})
    return output


def execute(gate):
    driver = bound_module('bound_group_driver', 'lib/driver.py', gate.buffers['lib/driver.py'])
    gate.retain_sources(); gate.native = gate.work / 'native'
    for source, ref in gate.cached.items():
        target = gate.native / source.removeprefix(base.CACHED)
        gate.copy(source, target); target.chmod(0o555 if source == base.CACHED + 'cmix' else 0o444)
        gate.retained[target] = ref['sha256']
    gate.binaries[str(gate.native / 'cmix')] = base.RUNTIME['cmix'][1]
    output_models, comparisons = models(gate)
    inventories, economics = packages(gate, output_models)
    base.verify_runtime(gate)
    gate.run('fixture-preprocess', [str(gate.native / 'cmix'), '-s', 'dictionary/english.dic', 'prof_input/input', 'fixture.stored'], 30, work=gate.native)
    base.verify_runtime(gate)
    base.compare_bytes(gate, gate.native / 'fixture.stored', gate.storage, 'fixture-storage')
    gate.required.add(gate.native / 'fixture.stored')
    native, traces = {}, []
    for arm in ARMS:
        output, package = gate.result / arm, inventories[arm]
        result = driver.run(ID, gate.native / 'prof_input/input', base.RAW_BYTES, True, run_purpose='diagnostic',
                            run_scope_label=arm + '-group-restoration-public-fixture', run_context='Each single group restored independently into the same failed even7 model',
                            run_source='canonical-tool', module=base.Codec(gate, arm, output_models[arm]), artifact_dir=output,
                            package_inventory=([(row['path'], row['bytes']) for row in package['counted_files']] +
                                               [('required-option-text', len(package['option_text'].encode()))], package))
        require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'], 'native exact inverse/repeat failed')
        archive = (output / 'archive.bin').read_bytes()
        base.archive_header(gate, archive)
        base.compare_bytes(gate, output / 'restored.bin', gate.raw, arm + '-raw-inverse')
        base.compare_bytes(gate, output / 'repeat.bin', archive, arm + '-archive-repeat')
        if arm in ('P', 'Q', 'K'):
            old = 'P' if arm == 'P' else 'D'
            base.compare_bytes(gate, output / 'archive.bin', gate.buffers[PARENT + old + '/archive.bin'], arm + '-anchor-archive')
            base.compare_bytes(gate, gate.native / (arm + '-encode.trace'), gate.buffers[PARENT + 'work/native/' + old + '-encode.trace'], arm + '-anchor-trace')
        reference = gate.native / (('Q' if arm == 'K' else arm) + '-encode.trace')
        for phase in base.PHASES:
            traces.append(base.compare_trace(gate, reference, gate.native / (arm + '-' + phase + '.trace'), base.MODELED_BYTES*8*28))
        native[arm] = {'archive_bytes': len(archive), 'archive_delta_vs_P': len(archive)-3223,
                       'archive_recovered_bytes_vs_Q': 4430-len(archive), 'exact_raw_inverse': True,
                       'same_arm_archive_and_coder_repeat': True, 'model': comparisons[arm], 'package_components': economics[arm]}
    require(len(gate.commands) == 43 and all(row['returncode'] == 0 for row in gate.commands), 'closed process population differs')
    diagnosis = probability_diagnosis(gate)
    costs = {arm: [row for row in gate.commands if row['phase'] in {arm + '-' + phase for phase in base.PHASES}] for arm in ARMS}
    for arm in ARMS:
        require(len(costs[arm]) == 3, 'native phase costs missing')
        native[arm]['probability_diagnosis'] = diagnosis[arm]
    gate.write('coder-records.json', {'comparisons': traces, 'Q_K_archive_probability_and_coder_identity': True,
                                    'all_arms_match_own_three_processes': True})
    gate.write('native-costs.json', {'arms': costs, 'timing_scope': 'shared-host process diagnostics including initialization and trace I/O',
                                   'kernel_only_cpu_seconds': None, 'missing_diagnostics': ['immutable binary has no kernel-only timer']})
    gate.write('restoration-table.json', {'arms': native, 'scope_raw_bytes': base.RAW_BYTES, 'scope_modeled_bytes': base.MODELED_BYTES,
                                        'interactions_additive': False, 'successor_selected': False, 'confirmation_data': False})
    return {'infrastructure_pass': True, 'synthetic_pass': True, 'model_restoration_pass': True,
            'native_binary_reused_exactly': True, 'native_binary': gate.artifact(gate.native / 'cmix'),
            'planned_processes': 43, 'native_phases': 24, 'mutator_compiles': 1, 'native_compiles': 0,
            'scope_bytes': base.RAW_BYTES, 'modeled_bytes': base.MODELED_BYTES, 'arms': native,
            'P_anchor_bytes': 3223, 'Q_K_anchor_bytes': 4430, 'Q_K_identity': True,
            'roundtrip_ok': True, 'deterministic_ok': True, 'successor_selected': False,
            'interactions_additive': False, 'same_development_population_requires_fresh_confirmation': True}


def main():
    load_helpers()
    validate = bool(sys.argv[1:])
    gate = NativeGate(ROOT, ID, CAPS, validate)
    validate_inputs(gate)
    if validate:
        print(json.dumps({'status': 'preflight_pass', 'inputs': len(gate.inputs), 'cached_native_files': len(gate.cached),
                          'arms': list(ARMS), 'groups': gate.groups, 'planned_processes': 43, 'native_compiles': 0, 'codec_executed': False}))
        return 0
    gate.required = {gate.result / name for name in ('synthetic.json', 'model-comparisons.json', 'package-economics.json',
                     'coder-records.json', 'native-costs.json', 'restoration-table.json', 'probability-loss-diagnosis.json')}
    for arm in ARMS:
        gate.required.add(gate.result / (arm + '-package.json'))
        gate.required.update(gate.result / arm / name for name in ('result.json', 'archive.bin', 'repeat.bin', 'restored.bin'))
        gate.required.update(gate.work / 'native' / (arm + '-' + phase + '.trace') for phase in base.PHASES)
    stage = {'schema': 'gamma.enwiki9.fx2-weight-restore-groups-fixture-stage.v1', 'candidate_id': ID,
             'experiment': gate.reference, 'objective': gate.contract['objective'], 'status': 'running',
             'infrastructure_pass': False, 'objective_credit_bytes': 0, 'full_corpus_score_bytes': None,
             'larger_gate_authorized': False, 'successor_selected': False,
             'continuous_guard_decision': 'pending canonical outer guard closure', 'dependency_closure_complete': False,
             'license_audit_complete': False, 'isolated_resource_qualification_complete': False,
             'full_corpus_reconstruction_proven': False, 'scope': 'single-group restoration diagnostic on examined public 50051-byte fixture'}
    try:
        stage.update(execute(gate), status='passed')
    except Exception as error:
        stage.update(status='execution_failed', infrastructure_pass=False,
                     failure_class=error.category if isinstance(error, GateFailure) else 'invariant_or_missing_evidence',
                     error=type(error).__name__ + ': ' + str(error))
    stage['child_closure_ok'] = False
    try:
        gate.closure(); stage['child_closure_ok'] = True
    except Exception as error:
        stage.update(status='execution_failed', infrastructure_pass=False, closure_error=str(error))
    cleanup = base.cleanup_native_transient(gate, stage['child_closure_ok'])
    if not cleanup['cleanup_complete'] or (stage['status'] == 'passed' and not cleanup['no_residual_before_cleanup']):
        stage.update(status='execution_failed', infrastructure_pass=False, transient_cleanup_error='owned PPM cleanup or process closure failed')
    gate.write('transient-cleanup.json', cleanup)
    stage['transient_cleanup'] = gate.artifact(gate.result / 'transient-cleanup.json')
    stage['artifact_index_exclusions'] = [{'path': cleanup['path'], 'role': cleanup['role'], 'status': cleanup['status'],
                                          'residual_present': cleanup['residual_present'], 'reason': 'metadata-only owned PPM transient cleanup'}]
    try:
        gate.closure(); gate.verify()
    except Exception as error:
        stage.update(status='execution_failed', infrastructure_pass=False, final_verification_error=str(error))
    stage['commands'] = gate.commands
    for command in gate.commands:
        gate.required.update(gate.result / (command['phase'] + suffix) for suffix in ('.stdout', '.stderr', '.execution.json'))
    gate.write('stage-decision.json', {**stage, 'status': 'publishing' if stage['status'] == 'passed' else stage['status'],
                                       'infrastructure_pass': False, 'artifact_index_status': 'pending'})
    try:
        artifacts, diagnostics = base.index_artifacts(gate, gate.work / 'native/ppm.temp')
        if not diagnostics['complete']:
            stage.update(status='execution_failed', infrastructure_pass=False, artifact_index_errors=diagnostics['errors'])
        gate.write('artifact-index-diagnostics.json', diagnostics)
        stage['artifact_index_diagnostics'] = gate.artifact(gate.result / 'artifact-index-diagnostics.json')
        gate.write('artifacts.json', artifacts)
        stage.update(artifacts=gate.artifact(gate.result / 'artifacts.json'), artifact_index_status='complete' if diagnostics['complete'] else 'incomplete')
    except Exception as error:
        stage.update(status='execution_failed', infrastructure_pass=False, artifact_index_status='failed', artifact_index_error=str(error))
    gate.write('stage-decision.json', stage)
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
