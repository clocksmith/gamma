"""Synthetic, model-free tests of whole-release integrity and activation."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from algsolve import recognition_bundle as bundle


def npy(rows):
    header = repr({'descr': '<f4', 'fortran_order': False, 'shape': (len(rows), len(rows[0]))})
    padding = (-(10 + len(header) + 1)) % 64
    raw_header = (header + ' ' * padding + '\n').encode('latin1')
    return b'\x93NUMPY\x01\x00' + struct.pack('<H', len(raw_header)) + raw_header + b''.join(
        struct.pack('<' + 'f' * len(row), *row) for row in rows)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.releases = self.root / 'releases'
        self.state = self.root / 'state'

    def fixture(self, label='first', mutate=None):
        source = self.root / ('source-' + label)
        source.mkdir()
        components = {
            'index_keys': 'index/keys.json', 'index_vectors': 'index/vectors.npy',
            'documents': 'index/documents.json', 'aliases': 'index/aliases.json',
            'preprocessing': 'identity/preprocessing.json', 'runtime': 'identity/runtime.json',
            'vector_binding': 'index/vector-binding.json',
            'model_manifests': ['identity/model.json'],
            'bits_catalogue': 'public/labs/two-button/challenges.json',
            'bits_manifest': 'public/labs/two-button/problems/manifest.json',
        }
        rows = [[1., 0.], [0., 1.]]
        docs = [{'problem_id': 'leetcode:' + str(i), 'text': f'Synthetic {label} title {i}'} for i in (1, 2)]
        for row in docs:
            row.update(document_sha256=hashlib.sha256(row['text'].encode()).hexdigest(), bytes=len(row['text'].encode()))
        packet_path = 'public/labs/two-button/problems/first.json'
        payloads = {
            components['index_keys']: ['lc:first', 'lc:second'],
            components['index_vectors']: npy(rows),
            components['documents']: {'documents': docs},
            components['aliases']: {'by_key': {'lc:first': 'leetcode:1', 'lc:second': 'leetcode:2'}},
            components['preprocessing']: {key: 'synthetic-' + key for key in
                ('encoder', 'model', 'adapter', 'tokenizer', 'pooling', 'normalization', 'truncation', 'document_instruction')},
            components['runtime']: {'name': 'synthetic-runtime'},
            'identity/model.json': {'name': 'synthetic-model', 'weights_sha256': '0' * 64},
            components['bits_catalogue']: {'problems': [
                {'key': 'lc:' + key, 'slug': key, 'title': docs[i]['text'], 'problem_id': docs[i]['problem_id']}
                for i, key in enumerate(('first', 'second'))]},
            packet_path: {'schema': 'gamma.bits-public-statement.v1', 'problem': {
                'problem_id': 'leetcode:1', 'key': 'lc:first', 'slug': 'first', 'title': docs[0]['text'],
                'statement': 'Synthetic permitted description; no solution or cases.'}},
            'public/labs/two-button/index.html': '<title>Synthetic BITS</title>',
        }
        packet_hash = hashlib.sha256(bundle.encoded(payloads[packet_path])).hexdigest()
        payloads[components['bits_manifest']] = {'problems': {
            'lc:first': {'problem_id': 'leetcode:1', 'scope': 'public-statement', 'path': packet_path, 'sha256': packet_hash},
            'lc:second': {'problem_id': 'leetcode:2', 'scope': 'metadata-only'}}}
        if mutate:
            mutate(payloads, components, rows)
        for name, value in payloads.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value if isinstance(value, bytes) else value.encode() if isinstance(value, str) else bundle.encoded(value))
        roles = {path: bundle.COMPONENT_ROLES[key] for key, path in components.items() if key in bundle.COMPONENT_ROLES}
        roles.update({'identity/model.json': 'model-manifest', packet_path: 'bits-packet',
                      'public/labs/two-button/index.html': 'public-ui'})
        files = {}
        def descriptor(name):
            raw = (source / name).read_bytes()
            public = name.startswith('public/')
            return {'role': roles[name], 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                    'publication': 'public' if public else 'private', 'permission_id': 'approved-' + label if public else None}
        for name in payloads:
            files[name] = descriptor(name)
        binding = {'schema': 'gamma.recognition-vector-binding.v1', 'component_sha256': {
            key: files[path]['sha256'] for key, path in components.items()
            if key not in ('vector_binding', 'model_manifests', 'bits_catalogue', 'bits_manifest')},
            'rows': [{'problem_id': doc['problem_id'], 'document_sha256': doc['document_sha256'],
                      'vector_row_sha256': hashlib.sha256(struct.pack('<ff', *row)).hexdigest(),
                      'origin': 'generated', 'provenance_sha256': hashlib.sha256(b'synthetic-not-real-execution').hexdigest()}
                     for doc, row in zip(docs, rows)]}
        binding['component_sha256']['model_manifests'] = {'identity/model.json': files['identity/model.json']['sha256']}
        (source / components['vector_binding']).write_bytes(bundle.encoded(binding))
        files[components['vector_binding']] = descriptor(components['vector_binding'])
        registry = {'approved-' + label: {'authority': 'Synthetic test operator', 'reference': 'Test-only approval fixture',
                    'scope': 'public-recognition-assets', 'assets': {name: row['sha256'] for name, row in files.items()
                                                                  if row['publication'] == 'public'}}}
        spec = {'schema': bundle.SCHEMA, 'ordered_problem_ids': ['leetcode:1', 'leetcode:2'], 'vector_dimension': 2,
                'components': components, 'files': files,
                'publication_permissions': {name: bundle.digest(value) for name, value in registry.items()}}
        return source, spec, registry

    def prepare(self, label='first', mutate=None):
        source, spec, registry = self.fixture(label, mutate)
        directory = bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)
        return directory, spec, registry

    def test_complete_bundle_preserves_metadata_only_competitors_and_is_resumable(self):
        source, spec, registry = self.fixture()
        directory = bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)
        self.assertEqual(directory.name, bundle.digest(spec))
        manifest = bundle.verify_release(directory, expected_release_id=directory.name, publication_permissions=registry)
        self.assertEqual(manifest['ordered_problem_ids'], ['leetcode:1', 'leetcode:2'])
        self.assertEqual(bundle.prepare_release(source, self.releases, spec, publication_permissions=registry), directory)
        self.assertFalse((directory / 'public/labs/two-button/problems/second.json').exists())

    def test_canonical_metadata_only_competitor_needs_no_slug_or_implementation(self):
        def canonical(payloads, components, rows):
            payloads[components['index_keys']][1] = 'leetcode:2'
            aliases = payloads[components['aliases']]['by_key']
            aliases['leetcode:2'] = aliases.pop('lc:second')
            payloads[components['bits_catalogue']]['problems'][1].update(key='leetcode:2', slug=None)
            packets = payloads[components['bits_manifest']]['problems']
            packets['leetcode:2'] = packets.pop('lc:second')
        directory, spec, registry = self.prepare('canonical', canonical)
        manifest = bundle.verify_release(directory, publication_permissions=registry)
        self.assertEqual(manifest['ordered_problem_ids'], ['leetcode:1', 'leetcode:2'])
        self.assertEqual(json.loads((directory / spec['components']['index_keys']).read_text())[1], 'leetcode:2')
        self.assertNotIn('implementation', json.dumps(manifest))

    def test_canonical_key_cannot_be_rebound_or_given_an_unproven_slug(self):
        def guessed(payloads, components, rows):
            payloads[components['index_keys']][1] = 'leetcode:2'
            aliases = payloads[components['aliases']]['by_key']
            aliases['leetcode:2'] = aliases.pop('lc:second')
            payloads[components['bits_catalogue']]['problems'][1].update(key='leetcode:2', slug='guessed-slug')
            packets = payloads[components['bits_manifest']]['problems']
            packets['leetcode:2'] = packets.pop('lc:second')
        source, spec, registry = self.fixture('guessed', guessed)
        with self.assertRaisesRegex(ValueError, 'independently mapped alias'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)

    def test_content_change_and_unlisted_public_payload_fail_closed(self):
        directory, spec, registry = self.prepare()
        packet = directory / 'public/labs/two-button/problems/first.json'
        packet.write_bytes(packet.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'size/hash'):
            bundle.verify_release(directory, publication_permissions=registry)
        directory2, _, registry2 = self.prepare('second')
        (directory2 / 'public/solution-guide.txt').write_text('unlisted')
        with self.assertRaisesRegex(ValueError, 'unlisted'):
            bundle.verify_release(directory2, publication_permissions=registry2)

    def test_external_publication_grant_required_before_public_payload_open(self):
        directory, spec, registry = self.prepare()
        with patch.object(bundle, '_sha_file', side_effect=AssertionError('payload opened')):
            with self.assertRaisesRegex(ValueError, 'publication grant missing'):
                bundle.verify_release(directory, publication_permissions={})
        changed = copy.deepcopy(registry)
        changed['approved-first']['reference'] = 'different provenance'
        with self.assertRaisesRegex(ValueError, 'provenance changed'):
            bundle.verify_release(directory, publication_permissions=changed)

    def test_duplicate_catalogue_and_packet_key_mismatch_are_not_silently_accepted(self):
        def duplicate(payloads, components, rows):
            catalogue = payloads[components['bits_catalogue']]['problems']
            catalogue[1] = dict(catalogue[0])
        source, spec, registry = self.fixture('duplicate', duplicate)
        with self.assertRaisesRegex(ValueError, 'BITS/index keys'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)
        self.assertEqual(list(self.releases.iterdir()), [])
        def missing(payloads, components, rows):
            del payloads[components['bits_manifest']]['problems']['lc:second']
        source, spec, registry = self.fixture('missing', missing)
        with self.assertRaisesRegex(ValueError, 'packet manifest keys'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)

    def test_alias_order_and_document_byte_hashes_are_checked(self):
        def alias(payloads, components, rows):
            payloads[components['aliases']]['by_key']['lc:second'] = 'leetcode:1'
        source, spec, registry = self.fixture('alias', alias)
        with self.assertRaisesRegex(ValueError, 'alias/index order'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)
        def document(payloads, components, rows):
            payloads[components['documents']]['documents'][0]['text'] += ' changed'
        source, spec, registry = self.fixture('document', document)
        with self.assertRaisesRegex(ValueError, 'document bytes/hash'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)

    def test_vectors_require_finiteness_normalization_and_exact_order(self):
        for label, bad, message in [('nonfinite', float('nan'), 'nonfinite'), ('norm', 2., 'normalization')]:
            def mutate(payloads, components, rows, bad=bad):
                rows[0] = [bad, 0.]
                payloads[components['index_vectors']] = npy(rows)
            source, spec, registry = self.fixture(label, mutate)
            with self.assertRaisesRegex(ValueError, message):
                bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)
        def reorder(payloads, components, rows):
            payloads[components['index_vectors']] = npy(rows[::-1])
        source, spec, registry = self.fixture('reorder', reorder)
        with self.assertRaisesRegex(ValueError, 'vector row/order'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)

    def test_dimensions_and_binding_runtime_drift_fail(self):
        source, spec, registry = self.fixture('dimensions')
        spec['vector_dimension'] = 3
        with self.assertRaisesRegex(ValueError, 'dimensions differ'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)
        source, spec, registry = self.fixture('runtime')
        name = spec['components']['runtime']
        (source / name).write_bytes(bundle.encoded({'name': 'changed-runtime'}))
        spec['files'][name]['sha256'] = hashlib.sha256((source / name).read_bytes()).hexdigest()
        spec['files'][name]['bytes'] = (source / name).stat().st_size
        with self.assertRaisesRegex(ValueError, 'execution/document/component binding'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)

    def test_symlink_traversal_and_solution_scope_are_rejected(self):
        source, spec, registry = self.fixture('symlink')
        name = spec['components']['documents']
        original = source / name
        outside = self.root / 'outside.json'
        outside.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)
        source, spec, registry = self.fixture('traversal')
        spec['files']['../outside.json'] = spec['files'].pop(name)
        with self.assertRaisesRegex(ValueError, 'unsafe bundle path'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)
        def solution(payloads, components, rows):
            packet = payloads['public/labs/two-button/problems/first.json']
            packet['solution'] = 'not a statement'
            payloads[components['bits_manifest']]['problems']['lc:first']['sha256'] = hashlib.sha256(bundle.encoded(packet)).hexdigest()
        source, spec, registry = self.fixture('solution', solution)
        with self.assertRaisesRegex(ValueError, 'solution guides/cases'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)

    def test_solution_body_cannot_hide_in_public_identity_metadata(self):
        def leaked(payloads, components, rows):
            payloads[components['bits_catalogue']]['problems'][0]['solution'] = 'not metadata'
        source, spec, registry = self.fixture('metadata-leak', leaked)
        with self.assertRaisesRegex(ValueError, 'identity metadata only'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)

    def test_duplicate_json_metadata_fields_are_rejected(self):
        def duplicate(payloads, components, rows):
            payloads[components['aliases']] = b'{"by_key":{},"by_key":{"lc:first":"leetcode:1","lc:second":"leetcode:2"}}'
        source, spec, registry = self.fixture('duplicate-json', duplicate)
        with self.assertRaisesRegex(ValueError, 'duplicate JSON field'):
            bundle.prepare_release(source, self.releases, spec, publication_permissions=registry)

    def test_atomic_activation_single_snapshot_and_one_operation_rollback(self):
        first, _, first_registry = self.prepare('first')
        second, _, second_registry = self.prepare('second')
        registry = {**first_registry, **second_registry}
        bundle.activate_release(self.state, first, expected_current_release_id=None, publication_permissions=registry)
        bundle.activate_release(self.state, second, expected_current_release_id=first.name, publication_permissions=registry)
        active = bundle.resolve_active_release(self.state, expected_release_id=second.name, publication_permissions=registry)
        self.assertTrue(active['components']['index_keys'].is_relative_to(second))
        self.assertEqual(active['public_root'], second / 'public')
        bundle.rollback_release(self.state, expected_current_release_id=second.name, publication_permissions=registry)
        restored = bundle.resolve_active_release(self.state, expected_release_id=first.name, publication_permissions=registry)
        self.assertTrue(restored['components']['index_vectors'].is_relative_to(first))
        self.assertEqual(restored['public_root'], first / 'public')
        self.assertTrue(second.exists())

    def test_stale_request_or_compare_and_swap_cannot_mix_releases(self):
        first, _, first_registry = self.prepare('first')
        second, _, second_registry = self.prepare('second')
        registry = {**first_registry, **second_registry}
        bundle.activate_release(self.state, first, expected_current_release_id=None, publication_permissions=registry)
        before = (self.state / 'active.json').read_bytes()
        with self.assertRaises(bundle.ReleaseMismatch):
            bundle.activate_release(self.state, second, expected_current_release_id='0' * 64, publication_permissions=registry)
        with self.assertRaises(bundle.ReleaseMismatch):
            bundle.resolve_active_release(self.state, expected_release_id=second.name, publication_permissions=registry)
        self.assertEqual((self.state / 'active.json').read_bytes(), before)

    def test_interrupted_pointer_publication_preserves_previous_complete_snapshot(self):
        first, _, first_registry = self.prepare('first')
        second, _, second_registry = self.prepare('second')
        registry = {**first_registry, **second_registry}
        bundle.activate_release(self.state, first, expected_current_release_id=None, publication_permissions=registry)
        before = (self.state / 'active.json').read_bytes()
        with patch.object(bundle.os, 'replace', side_effect=OSError('synthetic interruption')):
            with self.assertRaisesRegex(OSError, 'synthetic interruption'):
                bundle.activate_release(self.state, second, expected_current_release_id=first.name, publication_permissions=registry)
        self.assertEqual((self.state / 'active.json').read_bytes(), before)
        self.assertEqual(list(self.state.glob('.active-*')), [])
        self.assertEqual(bundle.resolve_active_release(self.state, publication_permissions=registry)['release_id'], first.name)

    def test_rollback_can_recover_when_the_current_candidate_is_corrupt(self):
        first, _, first_registry = self.prepare('first')
        second, _, second_registry = self.prepare('second')
        registry = {**first_registry, **second_registry}
        bundle.activate_release(self.state, first, expected_current_release_id=None, publication_permissions=registry)
        bundle.activate_release(self.state, second, expected_current_release_id=first.name, publication_permissions=registry)
        (second / 'index/vectors.npy').unlink()
        bundle.rollback_release(self.state, expected_current_release_id=second.name, publication_permissions=registry)
        restored = bundle.resolve_active_release(self.state, expected_release_id=first.name, publication_permissions=registry)
        self.assertEqual(restored['public_root'], first / 'public')

    def test_rollback_revalidates_retained_assets_before_pointer_write(self):
        first, _, first_registry = self.prepare('first')
        second, _, second_registry = self.prepare('second')
        registry = {**first_registry, **second_registry}
        bundle.activate_release(self.state, first, expected_current_release_id=None, publication_permissions=registry)
        bundle.activate_release(self.state, second, expected_current_release_id=first.name, publication_permissions=registry)
        before = (self.state / 'active.json').read_bytes()
        (first / 'index/vectors.npy').unlink()
        with self.assertRaisesRegex(ValueError, 'unlisted or missing'):
            bundle.rollback_release(self.state, expected_current_release_id=second.name, publication_permissions=registry)
        self.assertEqual((self.state / 'active.json').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
