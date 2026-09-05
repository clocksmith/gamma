#!/usr/bin/env python3
"""Confirm the frozen native weight loader on two retained canonical slices."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ID = 'fx2_weight_native_transfer250k_q0_v1'
PARENT_ID = 'fx2_weight_native_fixture50051_q0_v1'
PARENT = 'results/' + PARENT_ID + '/'
NATIVE = PARENT + 'work/native/'
TRANSFER = 'results/fx2_cmix_transformer_transfer250k_q0_v2/'
NATIVE_AUDIT = 'operations/provenance/public_fx2_weight_native_terminal_20260905.json'
NATIVE_REFLECTION = 'operations/adaptive/reflections/20260905T230139Z_d8475c03dc.json'
TRANSFER_AUDIT = 'operations/provenance/public_fx2_transfer250k_terminal_20260905.json'
TRANSFER_REFLECTION = 'operations/adaptive/reflections/20260905T204313Z_bd6edb2ed4.json'
VOCABULARY = 'operations/provenance/public_fx2_authenticated_vocabulary_20260905.json'
CAPS = {'cpus': [2], 'memory_bytes': 9999998976, 'scratch_bytes': 16000000000, 'swap_bytes': 0, 'wall_seconds': 1100}
ARMS = ('P', 'K', 'D')
PHASES = ('encode', 'decode', 'reencode')
FRONTEND = 'gamma-public-fx2-literal-first-block-v1'
CORPUS_SHA = '159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc'
FIXED_RECEIPTS = {
    NATIVE_AUDIT: '9370d51f64049b536a909f79115ffe6bbd91dea2ff5157eb18ea24cadd74ef1e',
    NATIVE_REFLECTION: '9bcc8540bf9fb03a4b89d44c0a6b9c7f07f85f587a7af0848f830a0a0ad41cda',
    TRANSFER_AUDIT: 'f3ed442ecdebee0de90dae1fd4e6404f923b3b837cf69fc4b445b7714f6fd534',
    TRANSFER_REFLECTION: '0f80e18dbd4bd7c6f20116bd31cf58163164d6bea6b4d18e1aa7df89db6a13be',
}
RUNTIME = {
    'cmix': (496136, 'c848acc756c8ced70422dfc4c8da03ac936417754b877eb8addf0143ce2ba100'),
    'dictionary/english.dic': (411996, '4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a'),
    'models/6m-q4-fp32.tfwc2': (2930652, '7f4db6c8c843a7e6264b6a48ed4805e9e431f543df7a9a0ecb37a35a5e4b8860'),
    'models/model.D': (2908329, '5cae4299a64af88b88a637f3c14e9ee54a5fd98c559e391f35dfa7d832b00e4a'),
}
POPULATIONS = (
    {'name': 'opening', 'offset': 0, 'modeled': 151210, 'archive_bytes': 33429,
     'raw_sha': '665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3',
     'stored_sha': '9cc29963608bb990b820bc88e836532b4c2a1cfc1a5b633a14b1c3bad78765ab',
     'archive_sha': '70325310e96b83b48677d76d53141e69ddb47519b4cdffd1c85f51fe2c444dbe'},
    {'name': 'distant', 'offset': 500000000, 'modeled': 166098, 'archive_bytes': 9499,
     'raw_sha': 'f0d01801279f29e353d1dd932a43133e191ea905da6626575b1ee174957717b8',
     'stored_sha': '4d9e14e8a0e482824f8322f03e2133bc0c62a6bfdd6e8c4772a87bd8173b91db',
     'archive_sha': 'f92f4ea6f9bfe1d368609da6e6c889cd1b983a4b93ed1bb71c5221371b6a8c8e'},
)


def load_helpers():
    """Load only the source buffers verified against the frozen contract."""
    contract_path = 'operations/adaptive/experiments/' + ID + '.json'
    content = (ROOT / contract_path).read_bytes()
    if sys.argv[1:] != ['--validate-only']:
        reference = json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON'])
        if reference['path'] != contract_path or hashlib.sha256(content).hexdigest() != reference['sha256'].removeprefix('sha256:'):
            raise ValueError('experiment changed before loading helper')
    inputs = {row['path']: row for row in json.loads(content)['inputs']}
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
    globals().update({name: namespace[name] for name in ('GateFailure', 'NativeGate', 'require', 'sha')})


def bound_ref(gate, ref):
    name = ref['path']
    require(name in gate.buffers, 'missing consumed binding: ' + name)
    digest = ref['sha256'].removeprefix('sha256:')
    data = gate.buffers[name]
    require(gate.inputs[name]['sha256'].removeprefix('sha256:') == digest and hashlib.sha256(data).hexdigest() == digest, 'receipt binding differs: ' + name)
    if 'bytes' in ref:
        require(len(data) == ref['bytes'], 'receipt byte count differs: ' + name)
    return data


def check_storage(data, population, vocabulary):
    require(len(data) == population['modeled'] + 10 and data[:10] == bytes.fromhex('8000000000070003d090'), 'WRT storage length or literal frame differs')
    allowed = set(vocabulary['vocabulary_bytes'])
    require(all(value in allowed for value in data[10:]), 'WRT body exceeds authenticated alphabet')


def check_archive(data, population, vocabulary):
    require(len(data) == population['archive_bytes'] and data[:9] == bytes.fromhex('47465631070003d090'), 'archive length or literal frame differs')
    require(data[14:46].hex() == vocabulary['vocabulary_bitmap_hex'], 'archive vocabulary bitmap differs')
    encoded_length = int.from_bytes(data[9:14], 'big')
    require(encoded_length == (1 << 39) + population['modeled'], 'archive modeled length or trained-map flag differs')


def validate_consumed_inputs(gate):
    for source in ('lib/driver.py', 'tools/research_contracts.py', 'tools/enwiki9_python_source_closure.py'):
        require(source in gate.inputs, 'missing Python runtime binding: ' + source)
        bound_ref(gate, gate.inputs[source])
    receipts = {name: json.loads(bound_ref(gate, {'path': name, 'sha256': digest})) for name, digest in FIXED_RECEIPTS.items()}
    audit, transfer = receipts[NATIVE_AUDIT], receipts[TRANSFER_AUDIT]
    require(audit['candidate_id'] == PARENT_ID and audit['validity'] == transfer['validity'] == 'valid', 'parent audit is not valid')
    for reflection_name, audit_name, candidate in ((NATIVE_REFLECTION, NATIVE_AUDIT, PARENT_ID), (TRANSFER_REFLECTION, TRANSFER_AUDIT, 'fx2_cmix_transformer_transfer250k_q0_v2')):
        reflection = receipts[reflection_name]
        require(reflection['candidateId'] == candidate and reflection['validity']['valid'] is True and reflection['decision']['promotionPredicatesPass'] is True, 'parent reflection is not selectable')
        require(any(ref['path'] == audit_name and ref['sha256'].removeprefix('sha256:') == FIXED_RECEIPTS[audit_name] for ref in reflection['evidence']), 'reflection does not bind audit')
    require(gate.contract['parent']['candidateId'] == PARENT_ID and gate.contract['parent']['revision'] == audit['candidate_revision'], 'candidate ancestry differs')
    objective = gate.contract['objective']
    require(objective == receipts[NATIVE_REFLECTION]['objective'] and objective['targetScoreBytes'] == 99000000 and objective['corpusBytes'] == 1000000000 and objective['corpusSha256'] == CORPUS_SHA, 'objective or corpus identity differs')
    require(transfer['frontend_identity'] == FRONTEND and transfer['scientific_measurements'] == {'deterministic_ok': True, 'mapping_gate_pass': True, 'roundtrip_ok': True}, 'prior transfer evidence differs')
    require(audit['source_bindings']['all_inputs_match'] and audit['source_bindings']['original_byte_model_unchanged'], 'native source closure differs')
    require(audit['resources']['cleanup_complete'] and audit['resources']['closed_process_list_empty'] and not any(audit['resources']['guard_flags'].values()), 'native guard is not closed and clean')
    for key in ('tensor_comparison_pass', 'coder_records_identical', 'all_archives_match_original_parent', 'pre_corpus_economic_gate_pass'):
        require(audit['scientific_measurements'][key] is True, 'native antecedent failed: ' + key)
    indexed = {row['path']: row for row in audit['artifacts']}
    require(len(indexed) == len(audit['artifacts']), 'native artifact inventory has duplicate paths')
    gate.packages, gate.cached_files = {}, {}
    for arm in ARMS:
        path = PARENT + arm + '-package.json'
        package = json.loads(bound_ref(gate, indexed[path]))
        require(len(package['counted_files']) == 135 and package['dependency_closure_complete'] is False and package['source_runtime_overlap_counted_twice'] is True, 'inherited package scope differs')
        require(package['counted_bytes'] == sum(ref['bytes'] for ref in package['counted_files']) + len(package['option_text'].encode()) <= 10000000, 'inherited inventory arithmetic differs')
        for ref in package['counted_files']:
            require(ref['path'].startswith(NATIVE) and indexed[ref['path']] == ref, 'cached native file lacks matching audit reference')
            bound_ref(gate, ref)
            require(ref['path'] not in gate.cached_files or gate.cached_files[ref['path']] == ref, 'conflicting repeated package member')
            gate.cached_files[ref['path']] = ref
        gate.packages[arm] = package
    require(len(gate.cached_files) == 134 and gate.packages['P'] == gate.packages['K'], 'cached source closure or bookkeeping package differs')
    for relative, (size, digest) in RUNTIME.items():
        bound_ref(gate, {'path': NATIVE + relative, 'bytes': size, 'sha256': digest})
        require(NATIVE + relative in gate.cached_files, 'runtime missing from inherited closure')
    economics_path = PARENT + 'package-economics.json'
    gate.economics = json.loads(bound_ref(gate, indexed[economics_path]))
    require(gate.economics == audit['package_economics'] and gate.economics['native_binary'] == gate.cached_files[NATIVE + 'cmix'], 'package economics are not bound to cached binary')
    economics = gate.economics
    require(economics['model_delta_per_copy'] == RUNTIME['models/model.D'][0] - RUNTIME['models/6m-q4-fp32.tfwc2'][0] == -22323, 'inherited model delta differs')
    require(economics['binary_delta_per_copy'] == RUNTIME['cmix'][0] - economics['parent_binary']['bytes'] == 12288, 'inherited binary delta differs')
    require(economics['runtime_pair_delta'] == 2 * (economics['model_delta_per_copy'] + economics['binary_delta_per_copy']) == -20070, 'runtime component arithmetic differs')
    require(economics['source_compressor_plus_decoder_delta'] == economics['raw_source_delta'] + economics['binary_delta_per_copy'] + 2 * economics['model_delta_per_copy'] == -21489, 'source component arithmetic differs')
    require(economics['option_delta_bytes'] == 0 and economics['needed_libraries_identical'] is True and economics['pre_corpus_economic_gate_pass'] is True and economics['dependency_closure_complete'] is False and economics['full_corpus_score_bytes'] is None, 'inherited economic scope differs')
    require(all(p['option_text'] == economics['option_text'] for p in gate.packages.values()), 'deployment option accounting differs')
    vocabulary = json.loads(bound_ref(gate, gate.inputs[VOCABULARY]))
    symbols = vocabulary['vocabulary_bytes']
    require(symbols == sorted(set(symbols)) and len(symbols) == vocabulary['vocabulary_size'] == 205 and all(type(value) is int and 0 <= value <= 255 for value in symbols), 'authenticated alphabet differs')
    bitmap = bytes(sum(1 << (value % 8) for value in symbols if value // 8 == index) for index in range(32))
    require(bitmap.hex() == vocabulary['vocabulary_bitmap_hex'] and vocabulary['embedded_weights']['sha256'] == RUNTIME['models/6m-q4-fp32.tfwc2'][1], 'vocabulary/model association differs')
    gate.vocabulary = vocabulary
    transfer_index = {row['path']: row for row in transfer['artifacts']}
    for population in POPULATIONS:
        name = population['name']
        row = transfer['outputs'][name]
        require(row['raw_offset'] == population['offset'] and row['raw_bytes'] == 250000 and row['modeled_bytes'] == population['modeled'], 'retained coordinates differ')
        refs = (
            {'path': TRANSFER + 'work/' + name + '.raw', 'bytes': 250000, 'sha256': population['raw_sha']},
            {'path': TRANSFER + 'work/' + name + '.stored', 'bytes': population['modeled'] + 10, 'sha256': population['stored_sha']},
            {'path': TRANSFER + name + '/archive.bin', 'bytes': population['archive_bytes'], 'sha256': population['archive_sha']},
        )
        for ref in refs:
            require(transfer_index[ref['path']] == ref, 'retained population lacks audit binding')
            bound_ref(gate, ref)
        require(row['archive'] == refs[2] and row['restored']['sha256'] == population['raw_sha'] and row['repeat']['sha256'] == population['archive_sha'], 'parent exact inverse/repeat identity differs')
        check_storage(gate.buffers[refs[1]['path']], population, vocabulary)
        check_archive(gate.buffers[refs[2]['path']], population, vocabulary)


def compare_bytes(gate, path, expected, label):
    actual = path.read_bytes()
    if actual != expected:
        first = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b), min(len(actual), len(expected)))
        start = max(0, first - 16)
        gate.write('first-divergence.json', {'kind': label, 'actual': gate.artifact(path), 'expected_bytes': len(expected), 'expected_sha256': hashlib.sha256(expected).hexdigest(), 'first_byte': first, 'context_start': start, 'actual_hex': actual[start:first + 17].hex(), 'expected_hex': expected[start:first + 17].hex()})
        raise ValueError(label + ' differs at byte ' + str(first))
    return actual


def compare_trace(gate, reference, target, expected_bytes):
    observations = {}
    for role, path in (('reference', reference), ('target', target)):
        row = {'path': str(path.relative_to(ROOT)), 'observed_bytes': None,
               'observed_complete_records': None, 'observed_partial_record_bytes': None}
        try:
            info = path.lstat()
            require(stat.S_ISREG(info.st_mode), 'trace is not a regular file')
            row.update(observed_bytes=info.st_size, observed_complete_records=info.st_size // 28,
                       observed_partial_record_bytes=info.st_size % 28)
        except (OSError, ValueError) as error:
            row['inspection_error'] = type(error).__name__ + ': ' + str(error)
        observations[role] = row
    if any(row['observed_bytes'] != expected_bytes for row in observations.values()):
        gate.write('first-divergence.json', {'kind': 'trace-completeness', 'record_bytes': 28,
                                            'expected_bytes': expected_bytes, 'expected_records': expected_bytes // 28,
                                            **observations})
        raise ValueError('coder trace is missing, unreadable, truncated or oversized')
    return gate.compare_trace(reference, target, expected_bytes)


def verify_runtime(gate, native):
    for relative, (size, digest) in RUNTIME.items():
        path = native / relative
        require(path.resolve() == path and path.stat().st_size == size and sha(path) == digest, 'cached runtime changed: ' + relative)
    require(not (native / 'ppm.temp').exists(), 'PPM temporary state was not closed')


def activation(gate, phase, arm):
    found = [line for line in (gate.result / (phase + '.stderr')).read_bytes().splitlines() if line.startswith(b'Gamma weight loader selected=')]
    expected = ('Gamma weight loader selected=' + arm + ' tensors=434 histogram_tensors=' + ('0' if arm == 'P' else '111') + ' histogram_symbols=' + ('0' if arm == 'P' else '5868864') + ' side_information_bytes=' + ('7169' if arm == 'D' else '0') + ' canonical=' + ('1' if arm == 'D' else '0')).encode()
    require(found == [expected], 'loader activation differs in ' + phase)


class Codec:
    def __init__(self, gate, native, population, arm):
        self.gate, self.native, self.population, self.arm = gate, native, population, arm
        self.count = 0
        self.prefix = population['name'] + '-' + arm
        self.model = 'models/model.D' if arm == 'D' else 'models/6m-q4-fp32.tfwc2'

    def invoke(self, phase, arguments):
        name = self.prefix + '-' + phase
        verify_runtime(self.gate, self.native)
        env = {'GAMMA_FX2_CODER_TRACE': str(self.native / (name + '.trace'))}
        if self.arm != 'P':
            env['GAMMA_FX2_WEIGHT_BOOKKEEPING'] = '1'
        self.gate.run(name, [str(self.native / 'cmix'), *arguments, '--transformer', self.model], 120, env, work=self.native)
        verify_runtime(self.gate, self.native)
        activation(self.gate, name, self.arm)

    def compress(self, raw):
        require(raw == self.gate.buffers[TRANSFER + 'work/' + self.population['name'] + '.raw'], 'encoder population changed')
        require(self.count < 2, 'unexpected extra encoder call')
        phase = 'encode' if self.count == 0 else 'reencode'
        self.count += 1
        name = self.prefix + '-' + phase
        with (self.native / (name + '.raw')).open('xb') as handle:
            handle.write(raw)
        self.invoke(phase, ['-c', 'dictionary/english.dic', name + '.raw', name + '.cmix'])
        return (self.native / (name + '.cmix')).read_bytes()

    def decompress(self, archive):
        name = self.prefix + '-decode'
        with (self.native / (name + '.cmix')).open('xb') as handle:
            handle.write(archive)
        self.invoke('decode', ['-d', 'dictionary/english.dic', name + '.cmix', name + '.raw'])
        return (self.native / (name + '.raw')).read_bytes()


def execute(gate):
    from lib import driver
    gate.retain_sources()
    native = gate.work / 'native'
    for source, ref in gate.cached_files.items():
        target = native / source.removeprefix(NATIVE)
        gate.copy(source, target)
        target.chmod(0o555 if source == NATIVE + 'cmix' else 0o444)
        gate.retained[target] = ref['sha256']
    gate.binaries[str(native / 'cmix')] = RUNTIME['cmix'][1]
    verify_runtime(gate, native)
    packages = {}
    for arm, original in gate.packages.items():
        files = [gate.artifact(native / ref['path'].removeprefix(NATIVE)) for ref in original['counted_files']]
        package = {**original, 'counted_files': files, 'inherited_package': {'path': PARENT + arm + '-package.json', 'sha256': gate.inputs[PARENT + arm + '-package.json']['sha256']}}
        require(sum(ref['bytes'] for ref in files) + len(package['option_text'].encode()) == original['counted_bytes'], 'copied package components differ')
        gate.write(arm + '-package.json', package)
        packages[arm] = package
    gate.write('package-economics.json', {**gate.economics, 'inherited_unchanged': True, 'inherited_receipt': gate.artifact(ROOT / (PARENT + 'package-economics.json')), 'transfer_native_binary': gate.artifact(native / 'cmix')})
    populations = []
    for population in POPULATIONS:
        name = population['name']
        raw = native / (name + '.raw')
        gate.copy(TRANSFER + 'work/' + name + '.raw', raw)
        raw.chmod(0o444)
        gate.retained[raw] = population['raw_sha']
        verify_runtime(gate, native)
        gate.run(name + '-preprocess', [str(native / 'cmix'), '-s', 'dictionary/english.dic', raw.name, name + '.stored'], 30, work=native)
        verify_runtime(gate, native)
        storage = compare_bytes(gate, native / (name + '.stored'), gate.buffers[TRANSFER + 'work/' + name + '.stored'], name + '-WRT-storage')
        check_storage(storage, population, gate.vocabulary)
        arms, traces = {}, []
        expected_archive = gate.buffers[TRANSFER + name + '/archive.bin']
        for arm in ARMS:
            package = packages[arm]
            output = gate.result / name / arm
            result = driver.run(ID, raw, 250000, True, run_purpose='diagnostic', run_scope_label=name + '-250k-' + arm, run_context='Cached native fixed weight marginals; exact cold-slice transfer on previously examined populations', run_source='canonical-tool', module=Codec(gate, native, population, arm), artifact_dir=output, package_inventory=([(ref['path'], ref['bytes']) for ref in package['counted_files']] + [('required-option-text', len(package['option_text'].encode()))], package))
            require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'], 'native inversion or repeat failed')
            for file in ('archive.bin', 'repeat.bin'):
                archive = compare_bytes(gate, output / file, expected_archive, name + '-' + arm + '-' + file)
                check_archive(archive, population, gate.vocabulary)
            compare_bytes(gate, output / 'restored.bin', gate.buffers[TRANSFER + 'work/' + name + '.raw'], name + '-' + arm + '-raw-inverse')
            for phase in PHASES:
                traces.append(compare_trace(gate, native / (name + '-P-encode.trace'), native / (name + '-' + arm + '-' + phase + '.trace'), population['modeled'] * 8 * 28))
            arms[arm] = {'result': gate.artifact(output / 'result.json'), 'archive': gate.artifact(output / 'archive.bin'), 'repeat': gate.artifact(output / 'repeat.bin'), 'restored': gate.artifact(output / 'restored.bin'), 'exact_parent_archive': True, 'exact_inverse': True, 'exact_repeat': True, 'loader_activation_verified': True}
        gate.write(name + '-coder-records.json', {'record_bytes': 28, 'records_per_phase': population['modeled'] * 8, 'all_exact': True, 'comparisons': traces})
        populations.append({'name': name, 'raw_offset': population['offset'], 'raw_bytes': 250000, 'raw': gate.artifact(raw), 'stored': gate.artifact(native / (name + '.stored')), 'modeled_bytes': population['modeled'], 'archive_bytes': population['archive_bytes'], 'first_block_header_hex': storage[5:10].hex(), 'mapping_gate_pass': True, 'arms': arms, 'coder_records': gate.artifact(gate.result / (name + '-coder-records.json'))})
        gate.write('populations.json', {'completed': populations, 'all_populations_complete': len(populations) == len(POPULATIONS), 'objective_credit_bytes': 0})
    require(len(gate.commands) == 20 and sum(not row['phase'].endswith('-preprocess') for row in gate.commands) == 18, 'native phase population differs')
    return {'native_binary': gate.artifact(native / 'cmix'), 'build_reused_exactly': True, 'compile_processes': 0, 'frontend_identity': FRONTEND, 'scope_bytes': 500000, 'modeled_bytes': 317308, 'populations': populations, 'mapping_gate_pass': True, 'roundtrip_ok': True, 'deterministic_ok': True, 'coder_records_identical': True, 'all_archives_match_original_parent': True, 'archive_saved_bytes': 0, 'inherited_package_components_unchanged': True, 'package_economics': gate.economics}


def cleanup_native_transient(gate, children_closed):
    """Record sparse scratch metadata; never read it as codec evidence."""
    native = gate.work / 'native'
    transient = native / 'ppm.temp'
    record = {'schema': 'gamma.enwiki9.fx2-transient-cleanup.v1', 'path': str(transient.relative_to(ROOT)),
              'role': 'transient PPM scratch, not a mandatory codec artifact', 'content_hashed': False,
              'child_closure_verified': children_closed, 'before': None, 'after': None,
              'removed': False, 'residual_present': None, 'cleanup_complete': False,
              'no_residual_before_cleanup': False, 'missing_diagnostics': []}
    metadata = lambda info: {'device': info.st_dev, 'inode': info.st_ino, 'mode': info.st_mode,
                             'links': info.st_nlink, 'logical_bytes': info.st_size,
                             'allocated_bytes': info.st_blocks * 512,
                             'mtime_ns': info.st_mtime_ns, 'ctime_ns': info.st_ctime_ns}
    try:
        before = transient.lstat()
    except FileNotFoundError:
        record.update(status='absent', residual_present=False, cleanup_complete=True, no_residual_before_cleanup=True)
        return record
    except OSError as error:
        record.update(status='inspection_failed', error=type(error).__name__ + ': ' + str(error))
        record['missing_diagnostics'].append('owned transient metadata and presence unavailable')
        return record
    record.update(before=metadata(before), residual_present=True)
    if not children_closed:
        record.update(status='retained_children_not_closed')
        record['missing_diagnostics'].append('safe removal not established because child closure failed')
        return record
    try:
        require(native.resolve() == native and stat.S_ISREG(before.st_mode), 'owned transient path is aliased or not a regular file')
        gate.closure()
        require(metadata(transient.lstat()) == record['before'], 'owned transient changed before removal')
        transient.unlink()
        record['removed'] = True
        try:
            record['after'] = metadata(transient.lstat())
        except FileNotFoundError:
            record.update(status='removed', residual_present=False, cleanup_complete=True)
        except OSError:
            record['residual_present'] = None
            raise
        else:
            raise ValueError('owned transient reappeared after removal')
    except Exception as error:
        record.update(status='cleanup_failed', cleanup_complete=False, error=type(error).__name__ + ': ' + str(error))
        record['missing_diagnostics'].append('final transient absence or safe removal could not be established')
    return record


def index_artifacts(gate, transient):
    """Preserve explicit missing evidence if a failed child has not closed."""
    errors, artifacts = [], []
    own_metadata = {gate.result / name for name in ('stage-decision.json', 'artifacts.json', 'artifact-index-diagnostics.json')}
    mandatory = []
    for population in POPULATIONS:
        name = population['name']
        mandatory += [gate.work / 'native' / (name + '.stored'), gate.result / (name + '-coder-records.json')]
        for arm in ARMS:
            mandatory += [gate.result / name / arm / filename for filename in ('result.json', 'archive.bin', 'restored.bin', 'repeat.bin')]
            mandatory += [gate.work / 'native' / (name + '-' + arm + '-' + phase + '.trace') for phase in PHASES]
    for path in mandatory:
        try:
            require(stat.S_ISREG(path.lstat().st_mode), 'mandatory evidence is not a regular file')
        except (OSError, ValueError) as error:
            errors.append({'path': str(path.relative_to(ROOT)), 'operation': 'mandatory-evidence-presence', 'error': type(error).__name__ + ': ' + str(error)})
    paths = []
    def enumeration_error(error):
        errors.append({'path': str(error.filename or gate.result), 'operation': 'enumerate-artifacts', 'error': type(error).__name__ + ': ' + str(error)})
    for directory, directories, files in os.walk(gate.result, onerror=enumeration_error, followlinks=False):
        base = Path(directory)
        directories[:] = [name for name in directories if base / name != transient]
        paths.extend(base / name for name in directories + files)
    for path in sorted(paths):
        if path == transient or transient in path.parents or path in own_metadata:
            continue
        try:
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                artifacts.append(gate.artifact(path))
            elif not stat.S_ISDIR(info.st_mode):
                raise ValueError('artifact entry is not a regular file or directory')
        except (OSError, ValueError) as error:
            errors.append({'path': str(path.relative_to(ROOT)), 'operation': 'fingerprint-artifact', 'error': type(error).__name__ + ': ' + str(error)})
    indexed = {row['path'] for row in artifacts}
    for path in mandatory:
        if str(path.relative_to(ROOT)) not in indexed:
            errors.append({'path': str(path.relative_to(ROOT)), 'operation': 'mandatory-evidence-index', 'error': 'mandatory evidence has no successful fingerprint'})
    return artifacts, {'complete': not errors, 'errors': errors, 'indexed_files': len(artifacts),
                       'index_metadata_excluded': [str(path.relative_to(ROOT)) for path in sorted(own_metadata)]}


def main():
    load_helpers()
    require(sys.argv[1:] in ([], ['--validate-only']), 'unexpected arguments')
    validate = bool(sys.argv[1:])
    gate = NativeGate(ROOT, ID, CAPS, validate)
    validate_consumed_inputs(gate)
    if validate:
        print(json.dumps({'status': 'preflight_pass', 'inputs': len(gate.inputs), 'cached_native_files': len(gate.cached_files), 'raw_populations': 2, 'native_processes_planned': 18, 'preprocess_processes_planned': 2, 'compile_processes_planned': 0, 'codec_executed': False}))
        return 0
    stage = {'schema': 'gamma.enwiki9.fx2-weight-native-transfer-stage.v1', 'candidate_id': ID, 'experiment': gate.reference, 'objective_credit_bytes': 0, 'full_corpus_score_bytes': None, 'larger_gate_authorized': False, 'continuous_guard_decision': 'pending canonical outer guard closure', 'population_scope': 'Two previously examined cold canonical slices; fresh execution confirmation, no statistical holdout or mature-history claim'}
    try:
        stage.update(execute(gate), status='passed')
    except Exception as error:
        category = error.category if isinstance(error, GateFailure) else 'missing_or_unreadable_evidence' if isinstance(error, (OSError, KeyError, json.JSONDecodeError)) else 'invariant_failed'
        stage.update(status='execution_failed', failure_class=category, error=type(error).__name__ + ': ' + str(error))
    stage['child_closure_ok'] = False
    try:
        gate.closure()
        stage['child_closure_ok'] = True
    except Exception as error:
        stage.update(status='execution_failed', closure_error=str(error))
    cleanup = cleanup_native_transient(gate, stage['child_closure_ok'])
    if not cleanup['cleanup_complete'] or (stage['status'] == 'passed' and not cleanup['no_residual_before_cleanup']):
        stage.update(status='execution_failed', transient_cleanup_error='owned PPM transient failed cleanup or the successful-process no-residual control')
    gate.write('transient-cleanup.json', cleanup)
    stage['transient_cleanup'] = gate.artifact(gate.result / 'transient-cleanup.json')
    stage['positive_control_no_residual'] = cleanup['no_residual_before_cleanup']
    # This exact owned scratch entry is never hashed, including when removal
    # is blocked. Mandatory archives, inverses, repeats and traces stay indexed.
    transient = gate.work / 'native/ppm.temp'
    stage['artifact_index_exclusions'] = [{'path': cleanup['path'], 'role': cleanup['role'],
                                           'reason': 'transient metadata and cleanup outcome recorded separately',
                                           'status': cleanup['status'], 'residual_present': cleanup['residual_present']}]
    try:
        gate.closure()
        gate.verify()
    except Exception as error:
        stage.update(status='execution_failed', final_verification_error=str(error))
    stage['commands'] = gate.commands
    gate.write('stage-decision.json', {**stage, 'status': 'publishing' if stage['status'] == 'passed' else stage['status'], 'artifact_index_status': 'pending'})
    try:
        artifacts, diagnostics = index_artifacts(gate, transient)
        stage['artifact_index_status'] = 'complete' if diagnostics['complete'] else 'incomplete'
        if not diagnostics['complete']:
            stage.update(status='execution_failed', artifact_index_errors=diagnostics['errors'])
        gate.write('artifact-index-diagnostics.json', diagnostics)
        stage['artifact_index_diagnostics'] = gate.artifact(gate.result / 'artifact-index-diagnostics.json')
        gate.write('artifacts.json', artifacts)
        stage['artifacts'] = gate.artifact(gate.result / 'artifacts.json')
    except Exception as error:
        stage.update(status='execution_failed', artifact_index_status='failed', artifact_index_error=type(error).__name__ + ': ' + str(error))
    gate.write('stage-decision.json', stage)
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
