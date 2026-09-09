#!/usr/bin/env python3
"""Count the fixed prefix dictionary with the existing FX2 auxiliary codec."""
import hashlib
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.fx2_native_gate_v1 import NativeGate, require, sha
from lib import driver

ID = 'fx2_prefix_dictionary_component_v1'
PLAN = 'operations/provenance/fx2_prefix_dictionary_component_v1_plan.json'
SUPPORT = 'tools/fx2_weight_native_transfer250k_q0_v1.py'
CAPS = dict(cpus=[2], memory_bytes=9999998976, swap_bytes=0,
            scratch_bytes=16000000000, wall_seconds=3600)
PHASE_CAP = 360
RAW_BYTES = 411996
RAW_SHA256 = '4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a'
PREFIX_BYTES = 362457
PREFIX_SHA256 = 'b442e63a75837033e7ef3ef29081926a8e80f4c8ae3a818edede6d8846071e04'


def write_new(path, data):
    with path.open('xb') as stream:
        stream.write(data)


def identity(path, size, digest, label):
    require(path.stat().st_size == size and sha(path) == digest,
            label + ' identity differs')


def bound_module(g, path):
    data = g.buffers[path]
    require(hashlib.sha256(data).hexdigest() ==
            g.inputs[path]['sha256'].removeprefix('sha256:'), 'module binding differs')
    module = types.ModuleType('bound_' + Path(path).stem)
    module.__file__ = str(ROOT / path)
    exec(compile(data, module.__file__, 'exec'), module.__dict__)
    return module


def validate(g):
    plan = json.loads(g.buffers[PLAN])
    require(plan['id'] == ID and plan['caps'] == CAPS and
            plan['phase_elapsed_seconds'] == PHASE_CAP, 'plan identity or bounds differ')
    references = list(plan['files'].values()) + plan['native_sources']
    if 'helper_expected' in plan:
        references.append(plan['helper_expected'])
    for row in references:
        data = g.buffers[row['path']]
        digest = row['sha256'].removeprefix('sha256:')
        require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == digest and
                g.inputs[row['path']]['sha256'].removeprefix('sha256:') == digest,
                'consumed input binding differs: ' + row['path'])
    dictionary = plan['files']['dictionary']
    require(dictionary['bytes'] == RAW_BYTES and dictionary['sha256'].removeprefix('sha256:') == RAW_SHA256,
            'fixed dictionary differs')
    for row in plan['runtime_files']:
        identity(Path(row['path']), row['bytes'], row['sha256'].removeprefix('sha256:'), 'runtime')
    return plan


def cleanup(g, support, name):
    closed = False
    try:
        g.closure()
        closed = True
    finally:
        record = support.cleanup_native_transient(g, closed)
        g.write(name + '-cleanup.json', record)
    require(record['cleanup_complete'], 'native transient cleanup failed')
    return record


class Codec:
    def __init__(self, g, arm, encoder, helper, support):
        require(arm in ('P', 'K', 'D'), 'unknown arm')
        self.g, self.arm, self.encoder, self.helper, self.support = g, arm, encoder, helper, support
        self.native = g.work / 'native'
        self.calls = 0
        self.restored = None
        self.phases = []

    def invoke(self, name, command, accepted=(0,)):
        try:
            self.g.run(name, [str(value) for value in command], PHASE_CAP,
                       work=self.native, accepted=accepted)
        finally:
            cleanup(self.g, self.support, name)

    def restore(self, name, encoded, output):
        # BPD1 alone cannot detect truncation at a complete record boundary.
        identity(encoded, PREFIX_BYTES, PREFIX_SHA256, 'prefix input')
        require(not output.exists(), 'restoration output already exists')
        self.invoke(name, [self.helper, encoded, output])
        identity(encoded, PREFIX_BYTES, PREFIX_SHA256, 'prefix input after restore')
        identity(output, RAW_BYTES, RAW_SHA256, 'restored dictionary')

    def restore_rejections(self, name, encoded, restored):
        identity(encoded, PREFIX_BYTES, PREFIX_SHA256, 'collision prefix input')
        identity(restored, RAW_BYTES, RAW_SHA256, 'collision existing output')
        self.invoke(name + '-collision', [self.helper, encoded, restored], accepted=(4,))
        identity(encoded, PREFIX_BYTES, PREFIX_SHA256, 'collision prefix input after restore')
        identity(restored, RAW_BYTES, RAW_SHA256, 'collision output after restore')
        data = encoded.read_bytes()
        boundary = data.rfind(b'\n', 5, len(data) - 1) + 1
        require(boundary > 5, 'missing complete record truncation boundary')
        truncated = self.native / (name + '.truncated.bpd')
        rejected = self.native / (name + '.rejected.raw')
        write_new(truncated, data[:boundary])
        require(not rejected.exists(), 'rejection output already exists')
        self.invoke(name + '-truncated', [self.helper, truncated, rejected], accepted=(3,))
        identity(truncated, boundary, hashlib.sha256(data[:boundary]).hexdigest(), 'truncated input after restore')
        require(not rejected.exists(), 'failed inverse published an output')
        identity(restored, RAW_BYTES, RAW_SHA256, 'dictionary after negative controls')
        self.g.write(name + '-rejections.json', dict(existing_output_preserved=True,
                     complete_record_truncation_rejected=True, truncated_input=self.g.artifact(truncated),
                     negative_output_absent=True))

    def prefix(self, name, source):
        identity(source, RAW_BYTES, RAW_SHA256, 'prefix source')
        encoded, report = self.encoder(source.read_bytes())
        require(len(encoded) == PREFIX_BYTES and hashlib.sha256(encoded).hexdigest() == PREFIX_SHA256,
                'fixed prefix representation differs')
        output = self.native / (name + '.bpd')
        write_new(output, encoded)
        identity(source, RAW_BYTES, RAW_SHA256, 'prefix source after encoding')
        self.g.write(name + '-prefix.json', dict(source=self.g.artifact(source),
                     encoded=self.g.artifact(output), encoder_report=report))
        return output

    def compress(self, raw):
        require(len(raw) == RAW_BYTES and hashlib.sha256(raw).hexdigest() == RAW_SHA256,
                'encoder dictionary differs')
        require(self.calls < 2, 'unexpected encoder invocation')
        phase = 'encode' if self.calls == 0 else 'repeat'
        source = self.g.work / 'dictionary.bin' if self.calls == 0 else self.restored
        require(source is not None, 'repeat requires independent decode')
        identity(source, RAW_BYTES, RAW_SHA256, 'encoder physical source')
        self.calls += 1
        name = self.arm + '-' + phase
        if self.arm in ('K', 'D'):
            encoded = self.prefix(name, source)
            if self.arm == 'K':
                source = self.native / (name + '.bookkeeping.raw')
                self.restore(name + '-restore', encoded, source)
                if phase == 'encode':
                    self.restore_rejections(name + '-restore', encoded, source)
            else:
                source = encoded
        before = self.g.artifact(source)
        target = self.native / (name + '.archive')
        require(not target.exists(), 'archive output already exists')
        self.invoke(name, [self.native / 'cmix', '-c', source, target])
        identity(source, before['bytes'], before['sha256'].removeprefix('sha256:'), 'compression input')
        self.phases.append(dict(phase=phase, input=before, output=self.g.artifact(target)))
        return target.read_bytes()

    def decompress(self, archive):
        require(self.calls == 1 and self.restored is None, 'unexpected decoder invocation')
        name = self.arm + '-decode'
        source = self.native / (name + '.archive')
        write_new(source, archive)
        output = self.native / (name + ('.bpd' if self.arm == 'D' else '.raw'))
        require(not output.exists(), 'decoder output already exists')
        self.invoke(name, [self.native / 'cmix', '-d', source, output])
        identity(source, len(archive), hashlib.sha256(archive).hexdigest(), 'decoder archive')
        if self.arm == 'D':
            restored = self.native / (name + '.raw')
            self.restore(name + '-restore', output, restored)
        else:
            restored = output
        identity(restored, RAW_BYTES, RAW_SHA256, 'decoded dictionary')
        self.restored = restored
        self.phases.append(dict(phase='decode', input=self.g.artifact(source),
                                output=self.g.artifact(restored)))
        return restored.read_bytes()


def economics(parent_bytes, treatment_bytes, helper_bytes, source_bytes):
    saving = parent_bytes - treatment_bytes
    return dict(archive_saving_bytes_per_copy=saving, helper_binary_bytes=helper_bytes,
                added_raw_source_bytes=source_bytes,
                diagnostic_net_bytes=2 * (saving - helper_bytes) - source_bytes,
                diagnostic_formula='2*(P_archive-D_archive-helper_binary)-header_source-helper_source',
                complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0)


def execute(g, support):
    plan = validate(g)
    g.retain_sources()
    native = g.work / 'native'
    native.mkdir()
    binary = native / 'cmix'
    g.copy(plan['files']['binary']['path'], binary)
    binary.chmod(0o555)
    g.binaries[str(binary)] = sha(binary)
    g.copy(plan['files']['dictionary']['path'], g.work / 'dictionary.bin')
    source = g.work / 'source' / plan['files']['restore_source']['path']
    helper = g.work / 'restore-dictionary'
    g.run('build-restore', ['/usr/bin/g++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                          '-Os', '-s', '-march=x86-64-v3',
                          str(source), '-o', str(helper)], PHASE_CAP)
    if 'helper_expected' in plan:
        expected = plan['helper_expected']
        identity(helper, expected['bytes'], expected['sha256'].removeprefix('sha256:'), 'compiled helper')
    g.binaries[str(helper)] = sha(helper)
    encoder = bound_module(g, plan['files']['prefix_encoder']['path']).encode_dictionary
    binary_ref, helper_ref = g.artifact(binary), g.artifact(helper)
    source_refs = [g.artifact(ROOT / plan['files'][key]['path']) for key in ('restore_header', 'restore_source')]
    prefix_encoder_ref = g.artifact(ROOT / plan['files']['prefix_encoder']['path'])
    reports, archives = {}, {}
    for arm in ('P', 'K', 'D'):
        codec = Codec(g, arm, encoder, helper, support)
        counted = [binary_ref] + ([helper_ref] + source_refs if arm == 'D' else [])
        package = dict(counted_files=counted, counted_bytes=sum(row['bytes'] for row in counted),
                       scope='Matched auxiliary dictionary component; common binary plus archive',
                       runtime_inventory=plan['runtime_files'], complete_submission_package=False,
                       package_integration_executed=False, prefix_encoder_role='offline package construction',
                       offline_construction_source_files=[prefix_encoder_ref],
                       offline_construction_source_bytes=prefix_encoder_ref['bytes'],
                       offline_source_excluded_from_diagnostic_formula=True,
                       required_invocations=['cmix -c INPUT OUTPUT', 'cmix -d INPUT OUTPUT'] +
                       (['restore-dictionary INPUT OUTPUT'] if arm == 'D' else []))
        g.write(arm + '-package.json', package)
        result = driver.run(ID, g.work / 'dictionary.bin', RAW_BYTES, True,
                            run_purpose='diagnostic', run_scope_label=arm + '-fixed-dictionary',
                            run_context='Fixed dictionary asset only; no corpus or transformer inference',
                            run_source='canonical-tool', module=codec,
                            artifact_dir=g.result / arm,
                            package_inventory=([(row['path'], row['bytes']) for row in counted], package))
        require(result['roundtrip_ok'] and result['determinism']['single_host_byte_equal'],
                'dictionary inverse or repeat failed')
        result['arm'] = arm
        g.write(arm + '/result.json', result)
        reports[arm] = dict(result=result, phases=codec.phases)
        archives[arm] = result['compressed_size']
        g.write(arm + '-phases.json', dict(phases=codec.phases))
    require((g.result / 'P/archive.bin').read_bytes() == (g.result / 'K/archive.bin').read_bytes(),
            'P/K auxiliary parent archives differ')
    g.verify()
    validate(g)
    return dict(correctness_pass=True, parent_bookkeeping_identity=True, archive_bytes=archives,
                reports=reports, common_auxiliary_binary=binary_ref,
                native_restore_helper=helper_ref, restoration_source_files=source_refs,
                offline_prefix_encoder_source=prefix_encoder_ref,
                native_restore_collision_and_truncation_controls_pass=True,
                repeat_starts_from_independently_restored_dictionary=True,
                native_package_integration_executed=False, inference_state_identity_claimed=False,
                **economics(archives['P'], archives['D'], helper_ref['bytes'],
                            sum(row['bytes'] for row in source_refs)))


def main():
    require(sys.argv[1:] in ([], ['--validate-only']), 'unexpected arguments')
    g = NativeGate(ROOT, ID, CAPS, validate_only=bool(sys.argv[1:]))
    validate(g)
    if sys.argv[1:]:
        print(json.dumps(dict(frozen_inputs_verified=len(g.inputs))))
        return 0
    support = bound_module(g, SUPPORT)
    support.require = require
    stage = dict(schema='gamma.enwiki9.prefix-dictionary-component-stage.v1', candidate_id=ID,
                 objective_credit_bytes=0, complete_package_bytes=None, full_corpus_score_bytes=None)
    try:
        stage.update(execute(g, support), status='passed')
    except Exception as error:
        stage.update(status='failed', failure_class=getattr(error, 'category', 'implementation_or_evidence_failure'),
                     error=str(error))
    try:
        stage['transient_cleanup'] = cleanup(g, support, 'terminal')
    except Exception as error:
        stage.update(status='failed', cleanup_blocked=str(error))
    g.write('stage-decision.json', stage)
    # ppm.temp is sparse transient scratch, even when failed cleanup retains it.
    g.write('artifacts.json', dict(files=[g.artifact(path) for path in sorted(g.result.rglob('*'))
                                       if path.is_file() and path.name != 'ppm.temp']))
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
