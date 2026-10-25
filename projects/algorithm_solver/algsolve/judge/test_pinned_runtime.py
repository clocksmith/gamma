"""Synthetic adapter checks; never execute a candidate or sandbox payload."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import pinned_runtime as runtime
from . import sandbox


class PinnedRuntimeTests(unittest.TestCase):
    def test_only_additional_mount_is_exact_readonly_binary(self):
        base = sandbox.bwrap_argv(Path('/task-host'), sandbox.Limits(), ['/runtime/node', 'runner.cjs'])
        actual = runtime.bwrap_argv(Path('/task-host'), sandbox.Limits(), ['/runtime/node', 'runner.cjs'], Path('/private/node'))
        insertion = ['--dir', '/runtime', '--ro-bind', '/private/node', '/runtime/node']
        at = actual.index('--dir')
        self.assertEqual(actual[at:at + len(insertion)], insertion)
        self.assertEqual(actual[:at] + actual[at + len(insertion):], base)
        self.assertIn('--unshare-all', actual)
        self.assertIn('--clearenv', actual)

    def test_unapproved_binary_fails_before_dependency_inspection(self):
        with tempfile.TemporaryDirectory() as directory:
            node = Path(directory) / 'node'
            node.write_bytes(b'not an approved executable')
            node.chmod(0o755)
            with self.assertRaisesRegex(sandbox.SandboxUnavailable, 'approved runtime identity'):
                runtime.freeze_runtime(node)

    def test_nonexecutable_binary_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            node = Path(directory) / 'node'
            node.write_bytes(b'inert')
            node.chmod(0o644)
            with self.assertRaisesRegex(sandbox.SandboxUnavailable, 'already be an executable'):
                runtime.freeze_runtime(node)

    def test_manifest_drift_prevents_monitor(self):
        with patch.object(runtime, 'freeze_runtime', return_value={'changed': True}), patch.object(runtime, '_run_monitored') as monitor:
            with self.assertRaisesRegex(sandbox.SandboxUnavailable, 'manifest drift'):
                runtime.run_node(Path('/unused'), manifest={}, files={})
            monitor.assert_not_called()

    def test_manifest_requires_exact_dependencies_and_no_extra_keys(self):
        expected = {"node_sha256": runtime.NODE_SHA256, "dependencies": [{"path": "/usr/lib/example", "sha256": "frozen"}]}
        with patch.object(runtime, "_current_manifest", return_value=expected):
            runtime.validate_manifest(expected)
            for altered in ({}, {**expected, "extra_mount": "/workspace"}, {**expected, "dependencies": []}):
                with self.assertRaisesRegex(sandbox.SandboxUnavailable, "dependency drift"):
                    runtime.validate_manifest(altered)

    def test_snapshot_and_cleanup_with_inert_monitor(self):
        data = b'inert runtime test fixture'
        digest = hashlib.sha256(data).hexdigest()
        manifest = {'node_bytes': len(data)}
        captured = []
        with tempfile.TemporaryDirectory() as directory:
            node = Path(directory) / 'node'
            node.write_bytes(data)
            node.chmod(0o755)
            def observe(task_dir, argv, stdin, limits, status, snapshot):
                captured.append(snapshot.parent)
                self.assertEqual(snapshot.read_bytes(), data)
                self.assertEqual(snapshot.stat().st_mode & 0o777, 0o555)
                self.assertEqual(argv, ['/runtime/node', '--version'])
                self.assertEqual((task_dir / 'input').read_bytes(), b'inert')
                self.assertNotEqual(snapshot, node)
                return 'observed-without-executing'
            with patch.object(runtime, 'NODE_SHA256', digest), patch.object(runtime, 'freeze_runtime', return_value=manifest), patch.object(runtime, '_run_monitored', side_effect=observe):
                self.assertEqual(runtime.run_node(node, manifest=manifest, files={'input': b'inert'}, node_args=['--version']), 'observed-without-executing')
            self.assertFalse(captured[0].exists())

    def test_snapshot_hash_mismatch_blocks_monitor(self):
        with tempfile.TemporaryDirectory() as directory:
            node = Path(directory) / 'node'
            node.write_bytes(b'changed after freeze')
            manifest = {'node_bytes': node.stat().st_size}
            with patch.object(runtime, 'freeze_runtime', return_value=manifest), patch.object(runtime, '_run_monitored') as monitor:
                with self.assertRaisesRegex(sandbox.SandboxUnavailable, 'changed while snapshotting'):
                    runtime.run_node(node, manifest=manifest, files={})
                monitor.assert_not_called()

    def test_status_channel_is_not_candidate_stdout(self):
        self.assertFalse(runtime._payload_exited(b'', 0))
        self.assertFalse(runtime._payload_exited(b'{"exit-code":0}\n{"exit-code":0}\n', 0))
        self.assertTrue(runtime._payload_exited(b'{"exit-code":0}\n', 0))


if __name__ == '__main__':
    unittest.main()
