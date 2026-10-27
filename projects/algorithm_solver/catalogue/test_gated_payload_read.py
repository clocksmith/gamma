"""Inert synthetic content only; no catalogue payload acquisition or execution."""
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from . import gated_payload_read as g
from . import test_boundary_policy as boundary_tests


class GatedPayloadReadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.body = b'inert synthetic bytes\x00\xff\n'
        self.payload = self.root / 'payload.bin'
        self.payload.write_bytes(self.body)
        raw, self.pins = boundary_tests.BoundaryPolicyTests().fixture()
        self.paths = {name: str(self.root / (name + '.json')) for name in raw}
        for name, value in raw.items():
            Path(self.paths[name]).write_bytes(value)
        self.kwargs = dict(problem_id='leetcode:2', language='python', payload_kind='source',
                           artifact_paths=self.paths, trusted_hashes=self.pins,
                           expected_sha256=hashlib.sha256(self.body).hexdigest(),
                           expected_size=len(self.body), maximum_bytes=1024,
                           expected_git_blob_oid=hashlib.sha1(
                               b'blob ' + str(len(self.body)).encode() + b'\0' + self.body).hexdigest())

    def read(self, path=None, **changes):
        return g.read_payload(self.payload if path is None else path, **(self.kwargs | changes))

    def test_same_read_receipt_and_existing_gate_for_both_kinds_and_languages(self):
        for kind in ('source', 'statement'):
            for lang in ('python', 'javascript'):
                with self.subTest(kind=kind, language=lang):
                    raw, receipt = self.read(payload_kind=kind, language=lang)
                    self.assertEqual(raw, self.body)
                    self.assertEqual(receipt['sha256'], hashlib.sha256(raw).hexdigest())
                    self.assertEqual(receipt['bytes'], len(raw))
                    self.assertEqual(receipt['git_blob_oid'], self.kwargs['expected_git_blob_oid'])
                    self.assertEqual(receipt['path'], str(self.payload))
                    self.assertEqual(receipt['gate']['payload_kind'], kind)
                    self.assertEqual(receipt['gate']['language'], lang)
                    self.assertTrue(receipt['identity_verified'])
                    self.assertEqual(receipt['payload_read_count'], 1)
                    self.assertFalse(receipt['semantic_qualification_created'])
                    self.assertFalse(receipt['source_publication_authorized'])

    def test_gate_immediately_precedes_exactly_one_reader_each_time(self):
        events = []
        gate, reader = g.boundary_policy.authorize_before_open, g.public_batch_adapter.bounded_regular_read
        def authorize(*args, **kwargs):
            result = gate(*args, **kwargs)
            events.append('gate')
            return result
        def read(*args, **kwargs):
            events.append('read')
            return reader(*args, **kwargs)
        with patch.object(g.boundary_policy, 'authorize_before_open', side_effect=authorize) as a, \
                patch.object(g.public_batch_adapter, 'bounded_regular_read', side_effect=read) as r:
            self.read()
            self.read()
        self.assertEqual(events, ['gate', 'read', 'gate', 'read'])
        self.assertEqual((a.call_count, r.call_count), (2, 2))
        self.assertEqual(r.call_args.args, (str(self.payload),))
        self.assertEqual(r.call_args.kwargs, {'maximum_bytes': 1024})

    def test_policy_denial_never_calls_payload_reader(self):
        with patch.object(g.public_batch_adapter, 'bounded_regular_read') as reader:
            for pid in ('leetcode:3', 'leetcode:4', 'leetcode:5', 'leetcode:6'):
                with self.subTest(pid=pid), self.assertRaises(PermissionError):
                    self.read(problem_id=pid)
            reader.assert_not_called()

    def test_old_success_or_receipt_cannot_reuse_authority_after_metadata_tamper(self):
        _, old = self.read()
        Path(self.paths['policy']).write_bytes(b'changed synthetic metadata')
        with patch.object(g.public_batch_adapter, 'bounded_regular_read') as reader:
            with self.assertRaises(ValueError):
                self.read()
            reader.assert_not_called()
        self.assertTrue(old['gate']['authorized'])

    def test_every_live_metadata_anchor_is_rechecked(self):
        for name in self.paths:
            path = Path(self.paths[name])
            before = path.read_bytes()
            path.write_bytes(before + b' ')
            with self.subTest(name=name), patch.object(g.public_batch_adapter, 'bounded_regular_read') as reader:
                with self.assertRaises(ValueError):
                    self.read()
                reader.assert_not_called()
            path.write_bytes(before)

    def test_malformed_requests_rejected_before_any_gate_or_reader(self):
        changes = [dict(problem_id=x) for x in (None, 2, True, '2', 'leetcode:02', 'leetcode:2\n', 'leetcode:２')]
        changes += [dict(language=x) for x in (None, [], 'ruby')]
        changes += [dict(payload_kind=x) for x in ('cases', 'serving', None, [])]
        changes += [dict(expected_sha256=x) for x in (None, 'x'*64, 'A'*64, '0'*63, '0'*64+'\n')]
        changes += [dict(expected_git_blob_oid=x) for x in ('', 'g'*40, 'a'*39, True)]
        changes += [dict(expected_size=x) for x in (-1, True, 1.5, 1025)]
        changes += [dict(maximum_bytes=x) for x in (0, -1, True, 1.5, 64*1024**2+1)]
        changes += [dict(artifact_paths={}), dict(trusted_hashes={}),
                    dict(trusted_hashes=self.pins | {'policy':'bad'}),
                    dict(artifact_paths=self.paths | {'policy':'relative'})]
        with patch.object(g.boundary_policy, 'authorize_before_open') as gate, \
                patch.object(g.public_batch_adapter, 'bounded_regular_read') as reader:
            for change in changes:
                with self.subTest(change=change), self.assertRaises(ValueError):
                    self.read(**change)
            for path in ('relative', '/', '/tmp//file', '/tmp/../file', '/tmp/./file', '/tmp/file/', '/tmp/\0file', b'/tmp/file'):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    self.read(path)
            gate.assert_not_called()
            reader.assert_not_called()

    def test_denied_or_wrong_identity_decision_cannot_open(self):
        good = g.boundary_policy.authorize_before_open('leetcode:2', self.paths, self.pins, language='python')
        bad = [None, {}, good | {'authorized': 1}, good | {'authorized': False},
               good | {'problem_id':'leetcode:1'}, good | {'language':'javascript'},
               good | {'payload_kind':'statement'}]
        with patch.object(g.public_batch_adapter, 'bounded_regular_read') as reader:
            for decision in bad:
                with self.subTest(decision=decision), patch.object(
                        g.boundary_policy, 'authorize_before_open', return_value=decision), self.assertRaises(PermissionError):
                    self.read()
            reader.assert_not_called()

    def test_each_expected_identity_mismatch_retains_same_read_receipt_without_retry(self):
        cases = [('sha256', dict(expected_sha256='0'*64)),
                 ('bytes', dict(expected_size=len(self.body)+1)),
                 ('git_blob_oid', dict(expected_git_blob_oid='0'*40))]
        for field, change in cases:
            with self.subTest(field=field), patch.object(
                    g.public_batch_adapter, 'bounded_regular_read', wraps=g.public_batch_adapter.bounded_regular_read) as reader:
                with self.assertRaises(g.PayloadIdentityError) as caught:
                    self.read(**change)
                receipt = caught.exception.receipt
                self.assertEqual(receipt['mismatches'], [field])
                self.assertFalse(receipt['identity_verified'])
                self.assertEqual(receipt['sha256'], hashlib.sha256(self.body).hexdigest())
                self.assertTrue(receipt['gate']['authorized'])
                self.assertNotIn('raw', receipt)
                self.assertEqual(reader.call_count, 1)

    def test_payload_tampered_after_gate_is_rejected_from_the_one_read(self):
        gate = g.boundary_policy.authorize_before_open
        def authorize(*args, **kwargs):
            decision = gate(*args, **kwargs)
            self.payload.write_bytes(b'tampered inert bytes')
            return decision
        with patch.object(g.boundary_policy, 'authorize_before_open', side_effect=authorize):
            with self.assertRaises(g.PayloadIdentityError):
                self.read()

    def test_receipt_uses_returned_bytes_not_a_second_open(self):
        reader = g.public_batch_adapter.bounded_regular_read
        def read(*args, **kwargs):
            raw = reader(*args, **kwargs)
            self.payload.unlink()
            return raw
        with patch.object(g.public_batch_adapter, 'bounded_regular_read', side_effect=read) as mocked:
            raw, receipt = self.read()
        self.assertEqual(raw, self.body)
        self.assertEqual(receipt['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(mocked.call_count, 1)
        self.assertFalse(self.payload.exists())

    def test_optional_identity_pins_and_empty_regular_file(self):
        raw, receipt = self.read(expected_size=None, expected_git_blob_oid=None)
        self.assertEqual(raw, self.body)
        self.assertIsNone(receipt['expected']['bytes'])
        self.payload.write_bytes(b'')
        raw, receipt = self.read(expected_sha256=hashlib.sha256(b'').hexdigest(), expected_size=0,
                                 expected_git_blob_oid=None)
        self.assertEqual(raw, b'')
        self.assertEqual(receipt['bytes'], 0)

    def test_no_follow_leaf_and_directory_symlinks(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.payload)
        with self.assertRaises(OSError):
            self.read(alias)
        directory = self.root / 'directory'
        directory.mkdir()
        (directory / 'payload').write_bytes(self.body)
        alias.unlink()
        alias.symlink_to(directory, target_is_directory=True)
        with self.assertRaises(OSError):
            self.read(alias / 'payload')

    def test_symlink_replacement_after_gate_is_rejected(self):
        gate = g.boundary_policy.authorize_before_open
        replacement = self.root / 'other'
        replacement.write_bytes(self.body)
        def authorize(*args, **kwargs):
            result = gate(*args, **kwargs)
            self.payload.unlink()
            self.payload.symlink_to(replacement)
            return result
        with patch.object(g.boundary_policy, 'authorize_before_open', side_effect=authorize), self.assertRaises(OSError):
            self.read()

    def test_special_files_and_size_bound_use_existing_reader(self):
        fifo = self.root / 'fifo'
        os.mkfifo(fifo)
        with self.assertRaises(ValueError):
            self.read(fifo)
        with self.assertRaises(ValueError):
            self.read(self.root)
        with self.assertRaises(ValueError):
            self.read(maximum_bytes=len(self.body)-1, expected_size=None)

    def test_observed_change_during_read_is_rejected_by_existing_reader(self):
        original = os.fstat
        calls = []
        def changed(fd):
            value = original(fd)
            calls.append(fd)
            if len(calls) == 2:
                fields = {name:getattr(value, name) for name in
                          ('st_mode','st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')}
                fields['st_ctime_ns'] += 1
                return SimpleNamespace(**fields)
            return value
        with patch.object(g.public_batch_adapter.os, 'fstat', side_effect=changed), self.assertRaises(ValueError):
            self.read()
        self.assertEqual(len(calls), 2)


if __name__ == '__main__':
    unittest.main()
