#!/usr/bin/env python3
"""Transfer the exact SMG deployment through the retained two-population gate."""
import hashlib
import json
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
ID = 'fx2_weight_sign_magnitude_transfer250k_q0_v1'
SPEC = 'operations/provenance/fx2_weight_sign_magnitude_transfer250k_v1_inputs.json'
HELPER = 'tools/fx2_weight_sign_magnitude_fixture50051_q0_v1.py'
HELPER_SHA = 'c020320b78be9c9f79e2a434c30b95078c9f35999f929c067dfae82bd808d3c7'
BASE = 'tools/fx2_weight_adaptive_transfer250k_q0_v1.py'
BASE_SHA = '3df3b78c975bfd46cc89d395e14c656fff3c567a46c376eb267662f496d8482a'
CAPS = dict(cpus=[2], memory_bytes=9999998976, scratch_bytes=16000000000,
            swap_bytes=0, wall_seconds=1100)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_populations(helper, gate):
    spec = gate.spec
    populations = spec['populations']
    require([(p['name'], p['offset'], p['modeled']) for p in populations] ==
            [('opening', 0, 151210), ('distant', 500000000, 166098)], 'wrong populations')
    terminal = helper.document(gate, spec['transfer_terminal'])
    reflection = helper.document(gate, spec['transfer_reflection'])
    require(terminal['validity'] == 'valid' and reflection['validity']['valid'] and
            terminal['scientific_measurements']['coder_records_identical'], 'invalid retained transfer')
    require(any(row['path'] == spec['transfer_terminal'] and
                helper.digest(gate.buffers[row['path']]) == row['sha256'].removeprefix('sha256:')
                for row in reflection['evidence']), 'transfer reflection omits terminal')
    retained = {p['name']: p for p in terminal['population']['populations']}
    for population in populations:
        prior = retained[population['name']]
        require(population['raw'] == prior['raw'] and population['stored'] == prior['stored'] and
                population['archive'] == prior['arms']['P']['archive'] and
                population['trace'] in terminal['coder_records'], 'retained coordinates differ')
        for key in ('raw', 'stored', 'archive', 'trace'):
            helper.bound_ref(gate, population[key])
        require(population['raw']['bytes'] == 250000 and
                population['stored']['bytes'] == population['modeled'] + 10 and
                population['trace']['bytes'] == population['modeled'] * 8 * 28,
                'wrong population lengths')
    fixture = helper.document(gate, spec['parent_terminal'])
    require(fixture['all_parent_records_identical'] and fixture['archive_saving_bytes'] == 0 and
            fixture['package_economics'] == gate.economics, 'fixture deployment changed')


def execute_transfer(execute, driver, gate, support):
    original = driver.run

    def recorded_run(*args, **kwargs):
        codec = kwargs['module']
        name, arm = codec.population['name'], codec.arm
        files, package = kwargs['package_inventory']
        if arm == 'P':
            old = gate.artifact(gate.work / 'native/cmix.P')
            package['counted_files'] = [old if Path(row['path']).name == 'cmix' else row
                                       for row in package['counted_files']]
            files = [(old['path'] if Path(path).name == 'cmix' else path, size)
                     for path, size in files]
        package['meaning'] = ('Diagnostic overlapping inventory with candidate source and selected native binary/model; '
                              'the measured ZIP package alternative is counted once, not once per population.')
        kwargs['package_inventory'] = (files, package)
        kwargs['run_context'] = 'Exact SMG transfer; retained native archives and recorded coder state required'
        gate.write(name + '-' + arm + '-package.json', package)
        result = original(*args, **kwargs)
        result['arm'] = name + '-' + arm
        gate.write(name + '/' + arm + '/result.json', result)
        return result

    driver.run = recorded_run
    try:
        result = execute(gate, support)
    finally:
        driver.run = original
    require(result['archive_saved_bytes'] == 0 and result['all_populations_complete'],
            'transfer archive or population invariant failed')
    gate.write('package-economics.json', {
        **gate.economics, 'dependency_closure_complete': False,
        'production_terminal': gate.artifact(ROOT / gate.spec['production_terminal']),
        'zip_terminal': gate.artifact(ROOT / gate.spec['zip_terminal']),
        'native_fixture_terminal': gate.artifact(ROOT / gate.spec['parent_terminal']),
        'scope': 'One fixed package improvement; never multiply by populations or phases.',
    })
    result.update(source_zip_plus_decoder_delta=-456, runtime_pair_delta=-832,
                  raw_source_plus_decoder_delta=806, full_hidden_predictor_state_verified=False)
    return result


def bootstrap():
    contract_path = 'operations/adaptive/experiments/' + ID + '.json'
    raw = (ROOT / contract_path).read_bytes()
    digest = lambda b: hashlib.sha256(b).hexdigest()
    if sys.argv[1:] != ['--validate-only']:
        require(json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) ==
                dict(path=contract_path, sha256='sha256:' + digest(raw)), 'experiment binding differs')
    contract = json.loads(raw)
    refs = {row['path']: row for row in contract['inputs']}
    require(len(refs) == len(contract['inputs']), 'duplicate inputs')
    for path in ('tools/' + ID + '.py', HELPER, BASE):
        source = ROOT / path
        require(source.resolve() == source and path in refs and
                digest(source.read_bytes()) == refs[path]['sha256'].removeprefix('sha256:'),
                'unbound runner/helper: ' + path)
    helper_raw = (ROOT / HELPER).read_bytes()
    require(digest(helper_raw) == HELPER_SHA and digest((ROOT / BASE).read_bytes()) == BASE_SHA,
            'measured helper changed')
    helper = types.ModuleType('_smg_transfer_helper')
    helper.__file__ = str(ROOT / HELPER)
    exec(compile(helper_raw, helper.__file__, 'exec'), helper.__dict__)
    for path in helper.PYTHON_INPUTS:
        require(path in refs and digest((ROOT / path).read_bytes()) ==
                refs[path]['sha256'].removeprefix('sha256:'), 'unbound Python closure: ' + path)
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / 'tools'))
    helper.load_source('tools/enwiki9_python_source_closure.py', refs, 'enwiki9_python_source_closure',
                       ('projects.enwiki9.tools.enwiki9_python_source_closure',))
    helper.load_source('tools/research_contracts.py', refs, 'research_contracts',
                       ('projects.enwiki9.tools.research_contracts',))
    driver = helper.load_source('lib/driver.py', refs, 'lib.driver')
    native = helper.load_source('lib/fx2_native_gate_v1.py', refs, '_smg_transfer_native_gate')
    base = helper.load_source(BASE, refs, '_smg_transfer_spine')
    support = helper.load_source(helper.SUPPORT, refs, '_smg_transfer_support')
    helper.ID, helper.SPEC = ID, SPEC

    class NativeGate(native.NativeGate):
        def verify(self):
            self.toolchain = json.loads(self.buffers[helper.PROFILE])
            super().verify()

    def validate(gate):
        helper.validate(gate)
        validate_populations(helper, gate)

    def support_module(gate):
        support.require, support.POPULATIONS = require, gate.spec['populations']
        return support

    base.ID, base.SPEC, base.CAPS = ID, SPEC, CAPS
    base.NativeGate, base.GateFailure, base.require, base.sha = NativeGate, native.GateFailure, require, native.sha
    base.bootstrap = lambda: None
    base.validate, base.Codec, base.activation = validate, helper.codec_class(base), helper.activation
    base.support_module = support_module
    inherited = base.execute
    base.execute = lambda gate, support: execute_transfer(inherited, driver, gate, support)
    return base


def main():
    require(sys.argv[1:] in ([], ['--validate-only']), 'unexpected arguments')
    return bootstrap().main()


if __name__ == '__main__':
    raise SystemExit(main())
