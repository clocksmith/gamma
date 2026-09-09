#!/usr/bin/env python3
"""Authenticated fixture adapter for the measured SMG binary/model/package."""
import hashlib
import json
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
ID = 'fx2_weight_sign_magnitude_fixture50051_q0_v1'
SPEC = 'operations/provenance/fx2_weight_sign_magnitude_fixture50051_v1_inputs.json'
PROFILE = 'operations/provenance/public_fx2_gcc15_toolchain_20260909.json'
BASE = 'tools/fx2_weight_adaptive_fixture50051_q0_v2.py'
SUPPORT = 'tools/fx2_weight_native_transfer250k_q0_v1.py'
PINNED = {
    BASE: '136e3bf4d67c17af04c45087a23520880aa26536fbb39f9b2a5d0e5347a9ab50',
    SUPPORT: '474b7d6e2bb3f89817d440c7a1c4e6902437d4e0ae0c78105da7b049da83ee0f',
}
PYTHON_INPUTS = (
    'tools/' + ID + '.py', BASE, SUPPORT, 'lib/fx2_native_gate_v1.py',
    'lib/artifacts.py', 'lib/driver.py', 'tools/research_contracts.py',
    'tools/enwiki9_python_source_closure.py',
)
CAPS = dict(cpus=[2], memory_bytes=9999998976, scratch_bytes=16000000000,
            swap_bytes=0, wall_seconds=900)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def same_identity(left, right):
    return (left['bytes'], left['sha256'].removeprefix('sha256:')) == (
        right['bytes'], right['sha256'].removeprefix('sha256:'))


def bound_ref(gate, row):
    path = row['path'].removeprefix(str(ROOT) + '/')
    require(not Path(path).is_absolute() and '..' not in Path(path).parts, 'invalid input path')
    require(path in gate.buffers and path in gate.inputs, 'missing input: ' + path)
    raw = gate.buffers[path]
    actual = digest(raw)
    require(actual == row['sha256'].removeprefix('sha256:') ==
            gate.inputs[path]['sha256'].removeprefix('sha256:'), 'input identity differs: ' + path)
    require('bytes' not in row or len(raw) == row['bytes'], 'input size differs: ' + path)
    return raw


def document(gate, path):
    require(path in gate.inputs, 'unbound document: ' + path)
    return json.loads(bound_ref(gate, gate.inputs[path]))


def economics(production, inner, zipped):
    expected = dict(model_delta_per_copy=-416, binary_delta_per_copy=0,
                    raw_source_delta=1638, runtime_pair_delta=-832,
                    source_compressor_plus_decoder_delta=806, option_delta_bytes=0)
    require(production['status'] == inner['status'] == zipped['status'] == 'passed',
            'antecedent execution failed')
    require(production['accounting'] == expected and
            all(inner[k] == v for k, v in expected.items()), 'native economics differ')
    require(inner['all_production_outputs_exact'] and inner['old_dispatch_negative_reproduced'],
            'missing production controls')
    reports = production['tensor_reports']
    require(len(reports) == 3 and all(
        x['exact_byte_comparison'] and x['tensor_count'] == 434 and
        x['payload_bytes'] == 39588806 and
        x['reference_digest_hex'] == x['target_digest_hex'] == reports[0]['reference_digest_hex']
        for x in reports), 'native tensor parity differs')
    require(zipped['zip_delta_bytes'] == -40 and zipped['decoder_binary_delta_bytes'] == 0 and
            zipped['decoder_model_delta_bytes'] == -416 and
            zipped['source_zip_plus_decoder_delta_bytes'] == -456 and
            zipped['inherited_runtime_pair_delta_bytes'] == -832 and
            zipped['option_delta_bytes'] == 0, 'ZIP economics differ')
    return dict(runtime_pair_delta=-832, source_zip_plus_decoder_delta=-456,
                source_compressor_plus_decoder_delta=806, raw_source_delta=1638,
                model_delta_per_copy=-416, binary_delta_per_copy=0, zip_delta_bytes=-40,
                option_delta_bytes=0, complete_package_bytes=None, full_corpus_score_bytes=None,
                objective_credit_bytes=0,
                meaning='ZIP realization only; preserve the failed +806 raw-source alternative. '
                        'Archive identity is required; no full hidden predictor-state claim.')


def check_budget(measured, budget):
    added = measured['zip_delta_bytes'] - measured['model_delta_per_copy']
    gross = -measured['runtime_pair_delta']
    require(added == 376 and added <= budget['maximumAddedPackageBytes'] and
            gross == 832 and gross - added == -measured['source_zip_plus_decoder_delta'] == 456,
            'measured ZIP component exceeds budget or arithmetic differs')
    return dict(compressed_source_increment_bytes=added, gross_runtime_saving_bytes=gross,
                net_zip_and_decoder_saving_bytes=gross - added)


def validate(gate):
    spec = document(gate, SPEC)
    require(spec['id'] == ID and spec['toolchain_profile'] == PROFILE, 'wrong fixture/profile')
    require(gate.contract['objective']['targetScoreBytes'] == 90000000 and
            gate.contract['parent'] == spec['parent'], 'wrong objective or parent')
    require(spec['native_terminal'] == spec['production_terminal'], 'ambiguous native antecedent')
    for row in spec['sources'] + list(spec['runtime'].values()) + list(spec['population'].values()) + list(spec['packages'].values()):
        bound_ref(gate, row)
    bound_ref(gate, spec['parent']['revision'])
    parent = document(gate, spec['parent_reflection'])
    terminal = document(gate, spec['parent_terminal'])
    require(parent['candidateId'] == spec['parent']['candidateId'] and
            parent['candidateRevision']['receipt'] == spec['parent']['revision'] and
            parent['validity']['valid'] and parent['decision']['promotionPredicatesPass'] and
            terminal['candidate_id'] == spec['parent']['candidateId'] and terminal['status'] == 'passed',
            'parent is not a valid selectable deployment')
    require(any(x['path'] == spec['parent_terminal'] and
                x['sha256'].removeprefix('sha256:') == digest(gate.buffers[x['path']])
                for x in parent['evidence']), 'parent reflection does not bind terminal')
    native = document(gate, spec['production_terminal'])
    zip_terminal = document(gate, spec['zip_terminal'])
    require(native['validity'] == zip_terminal['validity'] == 'valid' and
            zip_terminal['hypothesis_verdict'] == 'supported-scoped-source-zip-package-economics',
            'unselectable package evidence')
    require(native['result']['path'] == spec['production_result'] and
            zip_terminal['result']['path'] == spec['zip_result'], 'antecedent result path differs')
    production = json.loads(bound_ref(gate, native['result']))
    zipped = json.loads(bound_ref(gate, zip_terminal['result']))
    inner = json.loads(bound_ref(gate, production['production_receipt']))
    gate.economics = economics(production, inner, zipped)
    gate.economics.update(check_budget(gate.economics, gate.contract['budget']))
    outputs = inner['production_outputs']
    require(len(outputs) == 6 and all(x['bytes'] == 104960 and
            x['sha256'] == outputs[0]['sha256'] for x in outputs), 'production output population differs')
    for row in outputs:
        bound_ref(gate, row)
    for arm, binary, model in (('P', 'cmix.P', 'models/model.P'), ('D', 'cmix', 'models/model.D')):
        package = zipped['arms'][arm]
        require(same_identity(spec['runtime'][binary], inner['native_builds'][arm]) and
                same_identity(spec['runtime'][binary], package['native_binary']) and
                same_identity(spec['runtime'][model], package['members']['models/model.D']) and
                same_identity(spec['runtime']['dictionary/english.dic'], package['members']['dictionary/english.dic']) and
                same_identity(spec['packages'][arm], package['archive']) and
                package['exact_extraction'] and package['deterministic_repeat'] and
                package['exact_relocated_build'], 'runtime/package identity differs')
    require(len(spec['sources']) == len({x['relative'] for x in spec['sources']}) == 125,
            'native source population differs')
    require(all(same_identity(x, zipped['arms']['D']['members'][x['relative']])
                for x in spec['sources']), 'native source differs from measured ZIP')
    population = spec['population']
    require([population[k]['bytes'] for k in ('raw', 'stored', 'archive', 'trace')] ==
            [50051, 32488, 3223, 7275072], 'fixture population differs')
    require(population['raw']['sha256'] == '890b3e1210a24a249768d86bd5a79a1775ce19b2d56984ce3069ee26359ef2e6' and
            population['stored']['sha256'] == 'be65dc4d4afc30647dcaab0f7e6191e50295c7c2a626fdeedbfa5a684a1eaf9d' and
            population['archive']['sha256'] == 'cc94af1a3af764b9c3906f1a30397ed987e71df19b02dca81c50b62146b27805' and
            population['trace']['sha256'] == 'afde9a32c6f122fac22def6f072568173d9de9dbc5ddc7951d897ca523773403',
            'retained fixture identity differs')
    gate.spec = spec


def activation(gate, name, arm):
    selected = 'S' if arm == 'D' else 'A'
    expected = ('Gamma weight loader selected=' + selected +
                ' tensors=434 histogram_tensors=111 histogram_symbols=5868864 '
                'side_information_bytes=0 canonical=1').encode()
    found = [x for x in (gate.result / (name + '.stderr')).read_bytes().splitlines()
             if x.startswith(b'Gamma weight loader selected=')]
    require(found == [expected], 'wrong loader activation: ' + name)


def codec_class(base):
    class Codec(base.Codec):
        def invoke(self, phase, args):
            gate, native = self.gate, self.native
            name = self.prefix + '-' + phase
            binary = native / ('cmix.P' if self.arm == 'P' else 'cmix')
            binary.chmod(0o555)
            gate.binaries[str(binary)] = gate.spec['runtime'][binary.name]['sha256']
            gate.verify()
            require(not (native / 'ppm.temp').exists(), 'unclosed prior PPM scratch')
            env = {'GAMMA_FX2_CODER_TRACE': str(native / (name + '.trace'))}
            if self.arm != 'P':
                env['GAMMA_FX2_WEIGHT_BOOKKEEPING'] = '1'
            gate.run(name, [str(binary), *args, '--transformer', self.model], 120, env, work=native)
            activation(gate, name, self.arm)
            require(not (native / 'ppm.temp').exists(), 'PPM scratch remained after success')
            gate.verify()
    return Codec


def execute_fixture(execute, driver, gate, support):
    original = driver.run

    def recorded_run(*args, **kwargs):
        arm = kwargs['module'].arm
        files, package = kwargs['package_inventory']
        if arm == 'P':
            old = gate.work / 'native/cmix.P'
            old_ref = gate.artifact(old)
            package['counted_files'] = [old_ref if Path(x['path']).name == 'cmix' else x
                                        for x in package['counted_files']]
            files = [(old_ref['path'] if Path(path).name == 'cmix' else path, size) for path, size in files]
        package['meaning'] = ('Diagnostic overlapping inventory with candidate source; selected native binary/model. '
                              'Measured ZIP accounting is recorded separately.')
        kwargs['package_inventory'] = (files, package)
        kwargs['run_context'] = 'Exact SMG deployment; retained archives and complete recorded coder traces required'
        gate.write(arm + '-package.json', package)
        result = original(*args, **kwargs)
        result['arm'] = arm
        gate.write('fixture/' + arm + '/result.json', result)
        return result

    driver.run = recorded_run
    try:
        result = execute(gate, support)
    finally:
        driver.run = original
    require(result['archive_saved_bytes'] == 0, 'fixture cannot claim an archive gain')
    gate.write('package-economics.json', {
        **gate.economics, 'dependency_closure_complete': False,
        'production_terminal': gate.artifact(ROOT / gate.spec['production_terminal']),
        'zip_terminal': gate.artifact(ROOT / gate.spec['zip_terminal']),
        'zip_result': gate.artifact(ROOT / gate.spec['zip_result']),
    })
    result.update(source_zip_plus_decoder_delta=-456, runtime_pair_delta=-832,
                  raw_source_plus_decoder_delta=806, full_hidden_predictor_state_verified=False)
    return result


def load_source(path, refs, name, aliases=()):
    require(path in refs, 'missing Python source binding: ' + path)
    source = ROOT / path
    require(source.resolve() == source, 'aliased Python source: ' + path)
    raw = source.read_bytes()
    require(digest(raw) == refs[path]['sha256'].removeprefix('sha256:') and
            (path not in PINNED or digest(raw) == PINNED[path]), 'Python source changed: ' + path)
    module = types.ModuleType(name)
    module.__file__ = str(source)
    for alias in (name, *aliases):
        sys.modules[alias] = module
    exec(compile(raw, str(source), 'exec'), module.__dict__)
    return module


def bootstrap():
    path = 'operations/adaptive/experiments/' + ID + '.json'
    raw = (ROOT / path).read_bytes()
    if sys.argv[1:] != ['--validate-only']:
        require(json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) ==
                dict(path=path, sha256='sha256:' + digest(raw)), 'experiment binding changed')
    contract = json.loads(raw)
    refs = {x['path']: x for x in contract['inputs']}
    require(len(refs) == len(contract['inputs']), 'duplicate input paths')
    for path in PYTHON_INPUTS:
        require(path in refs and digest((ROOT / path).read_bytes()) ==
                refs[path]['sha256'].removeprefix('sha256:'), 'unbound Python closure: ' + path)
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / 'tools'))
    load_source('tools/enwiki9_python_source_closure.py', refs, 'enwiki9_python_source_closure',
                ('projects.enwiki9.tools.enwiki9_python_source_closure',))
    load_source('tools/research_contracts.py', refs, 'research_contracts',
                ('projects.enwiki9.tools.research_contracts',))
    driver = load_source('lib/driver.py', refs, 'lib.driver')
    native = load_source('lib/fx2_native_gate_v1.py', refs, '_smg_native_gate')
    base = load_source(BASE, refs, '_smg_fixture_spine')
    support = load_source(SUPPORT, refs, '_smg_fixture_support')

    class NativeGate(native.NativeGate):
        def verify(self):
            self.toolchain = json.loads(self.buffers[PROFILE])
            super().verify()

    base.ID, base.SPEC, base.CAPS = ID, SPEC, CAPS
    base.NativeGate, base.GateFailure, base.require, base.sha = NativeGate, native.GateFailure, require, native.sha
    base.bootstrap = lambda: None
    base.validate, base.activation, base.Codec = validate, activation, codec_class(base)
    support.require, support.POPULATIONS = require, ({'name': 'fixture'},)
    base.support_module = lambda gate: support
    inherited = base.execute
    base.execute = lambda gate, helper: execute_fixture(inherited, driver, gate, helper)
    return base


def main():
    require(sys.argv[1:] in ([], ['--validate-only']), 'unexpected arguments')
    return bootstrap().main()


if __name__ == '__main__':
    raise SystemExit(main())
