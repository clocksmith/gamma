#!/usr/bin/env python3
"""Bounded exact-residual model packing and restored native fixture identity."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ID = 'fx2_weight_exact_residual_model_q0_v1'
BASE = 'tools/fx2_weight_even7_fixture50051_q0_v1.py'
SAFE = 'tools/fx2_weight_native_transfer250k_q0_v1.py'
PROBE = 'tools/fx2_weight_exact_residual_probe_v1.cpp'
UNIT = 'operations/evidence/20260906_fx2_exact_residual_unit.json'
MARGINAL_AUDIT = 'operations/provenance/public_fx2_weight_marginal_terminal_20260905.json'
MARGINAL_REFLECTION = 'operations/adaptive/reflections/20260905T222955Z_5eb35a57d6.json'
ARMS = ('P', 'K', 'D')
CAPS = {'cpus': [2], 'memory_bytes': 9999998976, 'swap_bytes': 0,
        'scratch_bytes': 16000000000, 'wall_seconds': 900}
FLAGS = ('-std=c++17', '-O2', '-Wall', '-Wextra', '-fno-fast-math', '-ffp-contract=off')
PINNED = {
    BASE: 'defb7e7b1f9a4e9a149df7bc204bdb4d13f4281e19287703e3fae955dd7745d1',
    PROBE: '64ac452e0bf5acb0f1dee1487d509535104af5a0229d9b9457977be2d94d377f',
    UNIT: '421d808fe5f4f062454d30a22d737db8289942e721711d0762f7e1c449ba2822',
    MARGINAL_AUDIT: 'b879a20c6a4f621c27e5d0ef247cddeccc2cb59a5e6ce776684140eb4a5adf62',
    MARGINAL_REFLECTION: '20f44314b2ea61ccf6063d8a3cae2c8f1a42de80bd11277b6e408c99c04033e6',
}


def module_from_buffer(name, source, data):
    module = types.ModuleType(name)
    module.__file__, module.__package__ = str(ROOT / source), 'lib' if source.startswith('lib/') else ''
    sys.modules[name] = module
    exec(compile(data, module.__file__, 'exec'), module.__dict__)
    return module


def load_helpers():
    if sys.argv[1:] not in ([], ['--validate-only']):
        raise ValueError('unexpected arguments')
    path = 'operations/adaptive/experiments/' + ID + '.json'
    data = (ROOT / path).read_bytes()
    if not sys.argv[1:] and json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) != {
            'path': path, 'sha256': 'sha256:' + hashlib.sha256(data).hexdigest()}:
        raise ValueError('experiment changed before helper load')
    inputs = {row['path']: row for row in json.loads(data)['inputs']}
    buffers = {}
    for source in ('tools/' + ID + '.py', 'lib/fx2_native_gate_v1.py', 'lib/artifacts.py', BASE, SAFE):
        file = ROOT / source
        if file.resolve() != file:
            raise ValueError('aliased bootstrap source')
        buffers[source] = file.read_bytes()
        if hashlib.sha256(buffers[source]).hexdigest() != inputs[source]['sha256'].removeprefix('sha256:'):
            raise ValueError('bootstrap source changed: ' + source)
    helper = module_from_buffer('bound_exact_native_gate', 'lib/fx2_native_gate_v1.py', buffers['lib/fx2_native_gate_v1.py'])
    globals().update({name: getattr(helper, name) for name in ('NativeGate', 'GateFailure', 'require', 'sha')})
    safe = module_from_buffer('bound_exact_transfer_safety', SAFE, buffers[SAFE])
    safe.require, safe.sha = require, sha
    base = module_from_buffer('bound_exact_even7_operations', BASE, buffers[BASE])
    base.require, base.sha = require, sha
    for name in ('bound_ref', 'compare_bytes', 'compare_trace', 'cleanup_native_transient'):
        setattr(base, name, getattr(safe, name))
    globals()['base'] = base


def validate_inputs(gate):
    for source, digest in PINNED.items():
        base.bound_ref(gate, {'path': source, 'sha256': digest})
    # Scientific parent is the validated native marginal-loader fixture. Its
    # unchanged cache, public fixture, vocabulary and model identities are reused.
    base.validate_inputs(gate)
    reflection = json.loads(gate.buffers[MARGINAL_REFLECTION])
    require(reflection['candidateId'] == 'fx2_weight_marginal_roundtrip_q0_v1' and
            reflection['validity']['valid'] and reflection['decision']['promotionPredicatesPass'] and
            reflection['objective'] == gate.contract['objective'], 'marginal ancestry is invalid')
    require(any(row['path'] == MARGINAL_AUDIT and row['sha256'].removeprefix('sha256:') == PINNED[MARGINAL_AUDIT]
                for row in reflection['evidence']), 'marginal reflection does not bind audit')
    audit = json.loads(gate.buffers[base.NATIVE_AUDIT])
    native_index = {row['path']: row for row in audit['artifacts']}
    gate.anchor_trace = base.CACHED + 'P-encode.trace'
    base.bound_ref(gate, native_index[gate.anchor_trace])
    require(len(gate.buffers[gate.anchor_trace]) == base.MODELED_BYTES*8*28, 'native anchor trace is incomplete')
    unit = json.loads(gate.buffers[UNIT])
    require(unit['schema'] == 'gamma.enwiki9.fx2-exact-residual-unit.v1' and unit['test']['all_pass'] and
            unit['test']['count'] == 7 and unit['compile']['returncode'] == unit['test']['returncode'] == 0,
            'closed synthetic prerequisite failed')
    require(unit['measured_trained_model_bytes'] is None and unit['probability_stream_identity'] is None,
            'synthetic receipt scope differs')
    for ref in unit['source_bindings']:
        base.bound_ref(gate, ref)
    require({row['path'] for row in unit['source_bindings']} ==
            {PROBE, base.HEADER, 'tests/test_fx2_weight_exact_residual.py', 'tools/fx2_weight_marginal_fixtures_v1.py'},
            'synthetic source closure differs')
    require(tuple(unit['compile']['argv'][1:7]) == FLAGS and
            re.findall(rb'^\s*#\s*include\s*"([^"]+)"', gate.buffers[PROBE], re.M) == [b'../lib/fx2_weight_format_v1.hpp'],
            'compiler flags or local include closure differs')


def verify_probe(row, mode, source, output, metadata):
    require(row['schema'] == 'gamma.fx2-weight-exact-residual-probe.v1' and row['mode'] == mode,
            'exact-residual receipt identity differs')
    require(all(row[key] is True for key in ('original_stream_regeneration_ok', 'original_parameter_bits_exact',
                'inverse_ok', 'repeat_ok', 'BF16_and_raw_bits_unchanged')), 'exact parameter reconstruction failed')
    require(row['inference_executed'] is False and row['complete_package_bytes'] is None and
            row['full_corpus_score_bytes'] is None and row['objective_credit_bytes'] == 0, 'probe scope differs')
    require(row['input_bytes'] == source.stat().st_size and row['output_bytes'] == output.stat().st_size and
            row['original_stream_bytes'] == 2930652 and row['selected_marginal_bytes'] == 2908329,
            'model byte accounting differs')
    require(row['int4_tensor_count'] == 111 and row['tensor_payload_bytes'] == 6034374 and
            row['regenerated_rope_bytes'] == 33554432 and len(row['tensors']) == 434,
            'model parameter population differs')
    require([{key: tensor[key] for key in base.METADATA_FIELDS} for tensor in row['tensors']] ==
            [{key: tensor[key] for key in base.METADATA_FIELDS} for tensor in metadata], 'model metadata differs')
    require(row['bookkeeping_nonzero_residuals'] == (3119371 if mode in ('K', 'D') else 0) and
            row['header_bytes'] == (12 if mode == 'restore' else 7181), 'approximation/residual activation differs')
    require(row['side_information_bytes'] == row['header_bytes']-12 and
            row['delta_vs_selected_marginal_bytes'] == output.stat().st_size-2908329, 'side information accounting differs')


def pack_models(gate):
    gate.probe = gate.work / 'exact-residual-probe'
    gate.run('compile-probe', ['/usr/bin/g++', *FLAGS, str(gate.work / 'source' / PROBE), '-o', str(gate.probe)], 120)
    gate.binaries[str(gate.probe)] = sha(gate.probe)
    gate.required.add(gate.probe)
    gate.run('probe-self-test', [str(gate.probe), '--self-test'], 30)
    unit = json.loads((gate.result / 'probe-self-test.stdout').read_bytes())
    require(unit['schema'] == 'gamma.fx2-weight-exact-residual-selftest.v1' and unit['all_15_signed_values_exact'], 'fresh self-test failed')
    gate.write('synthetic-prerequisite.json', {'closed_suite': gate.inputs[UNIT], 'fresh_self_test': unit,
                                             'closed_seven_test_suite_repeated': False})
    packed, restored, receipts = {}, {}, {}
    directory = gate.work / 'models'; directory.mkdir()
    original = gate.native / 'models/6m-q4-fp32.tfwc2'
    for arm in ARMS:
        rows = []
        for phase in ('pack', 'repeat', 'restore'):
            mode = 'restore' if phase == 'restore' else arm
            source = packed[arm] if phase == 'restore' else original
            output = directory / (arm + '-' + phase + '.bin')
            name = arm + '-' + phase
            gate.run(name, [str(gate.probe), mode, str(source), str(output)], 45)
            require(output.is_file() and not Path(str(output) + '.partial').exists(), 'model publication incomplete')
            row = json.loads((gate.result / (name + '.stdout')).read_bytes())
            verify_probe(row, mode, source, output, gate.metadata['tensors'])
            if phase == 'restore':
                base.compare_bytes(gate, output, gate.buffers[base.CACHED + 'models/6m-q4-fp32.tfwc2'], name + '-original')
                restored[arm] = output
            else:
                data = output.read_bytes()
                if arm in ('P', 'K'):
                    base.compare_bytes(gate, output, gate.buffers[base.MARGINAL_MODEL], name + '-selected-marginal')
                else:
                    require(data[:8] == b'GFX2XOR1', 'exact-residual magic differs')
                    require(base.histogram_header(b'GFX2MAR1' + data[8:]) == base.histogram_header(gate.buffers[base.MARGINAL_MODEL]),
                            'paid original histograms differ')
                if phase == 'pack':
                    packed[arm] = output
                else:
                    base.compare_bytes(gate, output, packed[arm].read_bytes(), name + '-fresh-identity')
            output.chmod(0o444); gate.retained[output] = sha(output)
            gate.required.add(output); rows.append(row)
        require(rows[0] == rows[1], 'fresh pack receipt differs')
        receipts[arm] = {'packed': gate.artifact(packed[arm]), 'restored_original': gate.artifact(restored[arm]),
                         'repeat': gate.artifact(directory / (arm + '-repeat.bin')), 'pack_receipt': rows[0],
                         'canonical_original_sha256': sha(restored[arm]), 'original_parameter_bytes_compared_directly': True}
    gate.write('model-comparisons.json', {'arms': receipts, 'P_K_selected_marginal_identity': True,
                                         'all_original_streams_byte_identical': True, 'restores_used_for_native_inference': True})
    return packed, restored


def packages(gate, packed, restored):
    runtime = [gate.artifact(gate.native / name) for name in ('cmix', 'dictionary/english.dic')]
    restore_binary = gate.artifact(gate.probe)
    source_files = [gate.artifact(gate.work / 'source' / name) for name in (PROBE, base.HEADER)]
    build_options = 'g++ ' + ' '.join(FLAGS) + ' ' + PROBE + ' -o restore-model\n'
    # Options are charged once per compiler/decoder container. The original
    # native option string is common; restoration adds this prerequisite step.
    restore_options = 'restore-model restore packed-model model\n'
    packages, economics = {}, {}
    for arm in ARMS:
        files = runtime + [gate.artifact(packed[arm]), restore_binary]
        options = restore_options + base.OPTIONS
        package = {'counted_files': files, 'option_text': options,
                   'counted_bytes': sum(row['bytes'] for row in files) + len(options.encode()),
                   'dependency_closure_complete': False, 'inventory_scope': 'one experimental compiled container, direct persistent files only',
                   'generated_runtime_model': gate.artifact(restored[arm]), 'generated_model_counted_as_persistent_payload': False,
                   'generated_model_is_required_scratch': True, 'launcher_integration_measured': False,
                   'prospective_layout': {'cmix': runtime[0]['path'], 'dictionary/english.dic': runtime[1]['path'],
                                          'packed-model': str(packed[arm].relative_to(ROOT)),
                                          'restore-model': restore_binary['path'], 'generated_scratch': 'model'},
                   'baseline_native_loader_reads_selected_marginal_without_this_external_restorer': True,
                   'unresolved': gate.parent_packages['D']['unresolved']}
        gate.write(arm + '-package.json', package); packages[arm] = package
        model_delta = packed[arm].stat().st_size-2908329
        compiled_delta = 2*(model_delta+restore_binary['bytes']+len(restore_options.encode()))
        source_delta = 2*model_delta + restore_binary['bytes'] + sum(row['bytes'] for row in source_files) + len(build_options.encode()) + 2*len(restore_options.encode())
        economics[arm] = {'packed_model_bytes': packed[arm].stat().st_size, 'model_delta_vs_selected_marginal_bytes': model_delta,
                         'required_restore_binary_bytes_per_compiled_container': restore_binary['bytes'],
                         'generated_restored_model_scratch_bytes': restored[arm].stat().st_size,
                         'compiled_two_container_component_delta_bytes': compiled_delta,
                         'source_compressor_binary_decoder_raw_allowance_delta_bytes': source_delta,
                         'conservative_component_delta_bytes': max(compiled_delta, source_delta),
                         'compiled_component_improves': compiled_delta < 0,
                         'conservative_component_improves': max(compiled_delta, source_delta) < 0}
    gate.write('package-economics.json', {'arms': economics, 'selected_marginal_model_bytes': 2908329,
               'runtime_binary': restore_binary, 'restoration_sources': source_files, 'source_build_option_text': build_options,
               'restore_option_text_per_container': restore_options, 'native_binary_delta_bytes': 0,
               'compiled_and_source_allowances_are_alternatives_not_summed': True,
               'source_allowance_is_raw_source_budget_not_measured_source_zip': True,
               'dependent_libraries_and_final_launcher_closure_unmeasured': True,
               'complete_package_bytes': None, 'full_corpus_score_bytes': None, 'objective_credit_bytes': 0})
    return packages, economics


def execute(gate):
    driver = module_from_buffer('bound_exact_driver', 'lib/driver.py', gate.buffers['lib/driver.py'])
    gate.retain_sources(); gate.native = gate.work / 'native'
    for source, ref in gate.cached.items():
        target = gate.native / source.removeprefix(base.CACHED)
        gate.copy(source, target); target.chmod(0o555 if source == base.CACHED + 'cmix' else 0o444)
        gate.retained[target] = ref['sha256']
    gate.binaries[str(gate.native / 'cmix')] = base.RUNTIME['cmix'][1]
    packed, restored = pack_models(gate)
    inventories, economics = packages(gate, packed, restored)
    base.verify_runtime(gate)
    gate.run('fixture-preprocess', [str(gate.native / 'cmix'), '-s', 'dictionary/english.dic', 'prof_input/input', 'fixture.stored'], 30, work=gate.native)
    base.verify_runtime(gate)
    base.compare_bytes(gate, gate.native / 'fixture.stored', gate.storage, 'fixture-storage')
    gate.required.add(gate.native / 'fixture.stored')
    native, comparisons = {}, []
    for arm in ARMS:
        output, package = gate.result / arm, inventories[arm]
        result = driver.run(ID, gate.native / 'prof_input/input', base.RAW_BYTES, True, run_purpose='diagnostic',
                            run_scope_label=arm + '-restored-original-public-fixture',
                            run_context='Exact residual packing restored original parameter bytes before fresh native inference',
                            run_source='canonical-tool', module=base.Codec(gate, arm, restored[arm]), artifact_dir=output,
                            package_inventory=([(row['path'], row['bytes']) for row in package['counted_files']] +
                                               [('required-option-text', len(package['option_text'].encode()))], package))
        require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'], 'native inverse or repeat failed')
        for name in ('archive.bin', 'repeat.bin'):
            archive = base.compare_bytes(gate, output / name, gate.parent_archive, arm + '-' + name + '-parent')
            base.archive_header(gate, archive)
        base.compare_bytes(gate, output / 'restored.bin', gate.raw, arm + '-raw-inverse')
        for phase in base.PHASES:
            trace = gate.native / (arm + '-' + phase + '.trace')
            base.compare_bytes(gate, trace, gate.buffers[gate.anchor_trace], arm + '-' + phase + '-historical-anchor')
            comparisons.append(base.compare_trace(gate, gate.native / 'P-encode.trace', trace, base.MODELED_BYTES*8*28))
        native[arm] = {'archive_bytes': len(gate.parent_archive), 'archive_delta_vs_parent_bytes': 0,
                       'exact_original_raw_inverse': True, 'fresh_archive_repeat': True,
                       'native_probability_and_coder_stream_identity': True,
                       'restored_original_model': gate.artifact(restored[arm])}
    require(len(gate.commands) == 21 and all(row['returncode'] == 0 for row in gate.commands), 'phase population differs')
    gate.write('coder-records.json', {'all_nine_streams_match_native_parent': True, 'comparisons': comparisons})
    costs = {arm: [row for row in gate.commands if row['phase'] in {arm + '-' + phase for phase in base.PHASES}] for arm in ARMS}
    require(all(len(rows) == 3 for rows in costs.values()), 'native costs incomplete')
    gate.write('native-costs.json', {'arms': costs, 'timing_authority': 'shared-host process diagnostic',
                                   'kernel_only_cpu_seconds': None, 'missing_diagnostics': ['no kernel-only timer in immutable native binary']})
    return {'infrastructure_pass': True, 'closed_synthetic_suite_validated': True, 'fresh_probe_self_test': True,
            'exact_parameter_stream_restore': True, 'P_K_model_identity': True, 'roundtrip_ok': True, 'deterministic_ok': True,
            'native_probability_stream_identity': True, 'native_binary_reused_exactly': True,
            'native_phases': 9, 'native_compiles': 0, 'probe_compiles': 1, 'planned_processes': 21,
            'scope_bytes': base.RAW_BYTES, 'modeled_bytes': base.MODELED_BYTES, 'arms': native,
            'model_component_bytes': economics, 'archive_saved_bytes': 0,
            'component_economic_pass': economics['D']['conservative_component_improves'],
            'engineering_disposition': 'component_survives' if economics['D']['conservative_component_improves'] else 'reject_this_standalone_realization_on_component_cost',
            'final_launcher_package_integration_measured': False}


def main():
    load_helpers()
    gate = NativeGate(ROOT, ID, CAPS, bool(sys.argv[1:]))
    validate_inputs(gate)
    if sys.argv[1:]:
        print(json.dumps({'status': 'preflight_pass', 'inputs': len(gate.inputs), 'cached_native_files': len(gate.cached),
                          'planned_processes': 21, 'closed_synthetic_tests': 7, 'synthetic_suite_repeated': False,
                          'native_compiles': 0, 'codec_executed': False}))
        return 0
    gate.required = {gate.result / name for name in ('synthetic-prerequisite.json', 'model-comparisons.json', 'package-economics.json',
                                                     'coder-records.json', 'native-costs.json')}
    for arm in ARMS:
        gate.required.add(gate.result / (arm + '-package.json'))
        gate.required.update(gate.result / arm / name for name in ('result.json', 'archive.bin', 'repeat.bin', 'restored.bin'))
        gate.required.update(gate.work / 'native' / (arm + '-' + phase + '.trace') for phase in base.PHASES)
    stage = {'schema': 'gamma.enwiki9.fx2-weight-exact-residual-model-stage.v1', 'candidate_id': ID,
             'experiment': gate.reference, 'objective': gate.contract['objective'], 'status': 'running',
             'infrastructure_pass': False, 'objective_credit_bytes': 0, 'full_corpus_score_bytes': None,
             'larger_gate_authorized': False, 'continuous_guard_decision': 'pending canonical outer guard closure',
             'dependency_closure_complete': False, 'license_audit_complete': False,
             'isolated_resource_qualification_complete': False, 'full_corpus_reconstruction_proven': False,
             'scope': 'one fixed public model and exact restored-native comparison on public 50051-byte fixture',
             'economic_rule_is_infrastructure_requirement': False}
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
    for row in gate.commands:
        gate.required.update(gate.result / (row['phase'] + suffix) for suffix in ('.stdout', '.stderr', '.execution.json'))
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
