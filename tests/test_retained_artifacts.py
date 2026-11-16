"""Real Git fixtures and adversarial I/O controls for retained output restoration."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SPEC = importlib.util.spec_from_file_location("retained_artifacts", Path(__file__).resolve().parents[1] / "tools/retained_artifacts.py")
artifacts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(artifacts)


class Response(io.BytesIO):
    status = 200

    def __init__(self, data, url, length=None):
        super().__init__(data)
        self.url = url
        self.headers = {} if length is None else {"Content-Length": str(length)}
        self.largest_read = 0

    def geturl(self):
        return self.url

    def read(self, size=-1):
        self.largest_read = max(size, self.largest_read)
        return super().read(size)


class RetainedArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gamma-retained-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.name = "outputs/run/proof.bin"
        self.data = bytes(range(256)) * 601
        source = self.repo / self.name
        source.parent.mkdir(parents=True)
        source.write_bytes(self.data)
        source.chmod(0o755)
        (self.repo / "empty.raw").write_bytes(b"")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Retained bytes")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.git("update-ref", "refs/remotes/origin/main", self.revision)
        self.catalog = artifacts.build_catalog(self.repo, self.revision, [self.name, "empty.raw"])
        self.row = next(row for row in self.catalog["files"] if row["path"] == self.name)
        self.catalog_path = self.root / "catalog.json"
        self.write_catalog(self.catalog)
        self.destination = self.root / "restore"
        self.empty_repo = self.root / "no-objects"
        self.empty_repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.empty_repo)], check=True)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True)

    def write_catalog(self, catalog):
        self.catalog_path.write_text(json.dumps(catalog))

    def test_build_reads_only_explicit_committed_bytes_and_modes(self):
        (self.repo / self.name).write_bytes(b"uncommitted different bytes")
        self.assertEqual(self.row["sha256"], hashlib.sha256(self.data).hexdigest())
        self.assertEqual(self.row["bytes"], len(self.data))
        self.assertEqual(self.row["mode"], "100755")
        self.assertEqual(self.row["url"], artifacts.artifact_url(self.revision, self.name))
        self.assertEqual(self.catalog["fileCount"], 2)
        self.assertEqual(artifacts.read_catalog(self.catalog_path), self.catalog)
        for paths in [["outputs"], ["missing"], [self.name, self.name], ["../escape"], ["/absolute"], ["outputs//x"]]:
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                artifacts.build_catalog(self.repo, self.revision, paths)
        self.git("update-ref", "-d", "refs/remotes/origin/main")
        with self.assertRaisesRegex(ValueError, "origin/main"):
            artifacts.build_catalog(self.repo, self.revision, [self.name])

    def test_local_restore_survives_loss_of_original_repository(self):
        clone = self.root / "independent-clone"
        subprocess.run(["git", "clone", "-q", "--no-local", str(self.repo), str(clone)], check=True)
        import shutil
        shutil.rmtree(self.repo)
        for row in self.catalog["files"]:
            artifacts.restore_file(row, self.destination, clone)
        artifacts.check_files(self.catalog["files"], self.destination)
        self.assertEqual((self.destination / self.name).read_bytes(), self.data)
        self.assertEqual((self.destination / self.name).stat().st_mode & 0o777, 0o755)
        artifacts.restore_file(self.row, self.destination, clone)  # Idempotent, not an overwrite.
        (self.destination / self.name).write_bytes(b"local edit")
        with self.assertRaises(ValueError):
            artifacts.restore_file(self.row, self.destination, clone)
        self.assertEqual((self.destination / self.name).read_bytes(), b"local edit")

    def test_remote_fetch_is_explicit_streamed_and_identity_verified(self):
        with patch.object(artifacts, "open_remote") as remote:
            with self.assertRaisesRegex(ValueError, "explicit --fetch"):
                artifacts.restore_file(self.row, self.destination, self.empty_repo)
            remote.assert_not_called()
        response = Response(self.data, self.row["url"], len(self.data))
        with patch.object(artifacts, "open_remote", return_value=response) as remote:
            artifacts.restore_file(self.row, self.destination, self.empty_repo, fetch=True)
            remote.assert_called_once()
        self.assertLessEqual(response.largest_read, artifacts.CHUNK_BYTES)
        self.assertEqual((self.destination / self.name).read_bytes(), self.data)

    def test_corrupt_remote_never_publishes_partial_bytes(self):
        cases = [(self.data + b"x", None, self.row), (self.data[:-1], None, self.row),
                 (b"x" * len(self.data), len(self.data), self.row),
                 (self.data, len(self.data) + 1, self.row),
                 (self.data, len(self.data), {**self.row, "sha256": "0" * 64}),
                 (self.data, len(self.data), {**self.row, "gitBlob": "0" * 40})]
        for data, length, row in cases:
            with self.subTest(length=length, size=len(data)):
                with patch.object(artifacts, "open_remote", return_value=Response(data, row["url"], length)), self.assertRaises(ValueError):
                    artifacts.restore_file(row, self.destination, self.empty_repo, fetch=True)
                self.assertFalse((self.destination / self.name).exists())
                self.assertEqual(list(self.destination.rglob("*.restore-*")), [])
        for response in [Response(self.data, "https://evil.example/object", len(self.data)), Response(self.data, self.row["url"], len(self.data))]:
            response.status = 302
            with patch.object(artifacts, "open_remote", return_value=response), self.assertRaises(ValueError):
                artifacts.restore_file(self.row, self.destination, self.empty_repo, fetch=True)

    def test_repeated_identities_fetch_once_and_restore_independent_files(self):
        second = {**self.row, "path": "outputs/repeat/proof.bin", "mode": "100644"}
        second["url"] = artifacts.artifact_url(second["sourceCommit"], second["path"])
        with patch.object(artifacts, "open_remote", return_value=Response(self.data, self.row["url"], len(self.data))) as remote:
            artifacts.restore_files([self.row, second], self.destination, self.empty_repo, fetch=True)
            remote.assert_called_once()
        first_path, second_path = self.destination / self.name, self.destination / second["path"]
        self.assertEqual(second_path.stat().st_mode & 0o777, 0o644)
        first_path.write_bytes(b"modified original")
        self.assertEqual(second_path.read_bytes(), self.data)
        third = {**self.row, "path": "outputs/third.bin"}
        third["url"] = artifacts.artifact_url(third["sourceCommit"], third["path"])
        with self.assertRaises(ValueError):
            artifacts.restore_file(third, self.destination, self.empty_repo, from_restored=self.name)
        self.assertFalse((self.destination / third["path"]).exists())

    def test_no_overwrite_even_when_a_writer_races_atomic_publication(self):
        def raced(*args, **kwargs):
            (self.destination / self.name).write_bytes(b"other session work")
            raise FileExistsError("racing destination")
        with patch.object(artifacts.os, "link", side_effect=raced), self.assertRaises(FileExistsError):
            artifacts.restore_file(self.row, self.destination, self.repo)
        self.assertEqual((self.destination / self.name).read_bytes(), b"other session work")
        self.assertEqual(list(self.destination.rglob("*.restore-*")), [])

    def test_symlink_destinations_and_catalog_remote_injection_are_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.destination.mkdir()
        (self.destination / "outputs").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            artifacts.restore_file(self.row, self.destination, self.repo)
        self.assertEqual(list(outside.iterdir()), [])
        (self.destination / "outputs").unlink()
        (self.destination / self.name).parent.mkdir(parents=True)
        (self.destination / self.name).symlink_to(outside / "missing")
        with self.assertRaises(OSError):
            artifacts.restore_file(self.row, self.destination, self.repo)
        for key, bad in [("path", "../escape"), ("path", ".git/hooks/post-checkout"), ("url", "http://127.0.0.1/private"), ("url", self.row["url"] + "?redirect=evil"),
                         ("mode", "120000"), ("bytes", True), ("sha256", "x" * 64)]:
            value = copy.deepcopy(self.catalog)
            value["files"][1 if value["files"][0]["path"] != self.name else 0][key] = bad
            self.write_catalog(value)
            with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                artifacts.read_catalog(self.catalog_path)
        self.catalog_path.write_text('{"schema": "a", "schema": "b"}')
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            artifacts.read_catalog(self.catalog_path)

    def test_restore_rejects_bad_remote_even_for_programmatic_callers(self):
        with patch.object(artifacts, "open_remote") as remote:
            with self.assertRaisesRegex(ValueError, "noncanonical"):
                artifacts.restore_file({**self.row, "url": "https://evil.example/file"}, self.destination, self.empty_repo, fetch=True)
            remote.assert_not_called()

    def test_boundary_rejects_tracked_and_force_added_outputs(self):
        with self.assertRaisesRegex(ValueError, "still tracked"):
            artifacts.check_boundary([self.row], self.repo)
        self.git("rm", "--cached", "-q", self.name)
        artifacts.check_boundary([self.row], self.repo)
        (self.repo / ".gitignore").write_text("outputs/\n")
        self.git("add", "-f", self.name)
        nested = self.repo / "subdir"
        nested.mkdir()
        with self.assertRaisesRegex(ValueError, "still tracked"):
            artifacts.check_boundary([self.row], nested)
        with self.assertRaisesRegex(ValueError, "No retained"):
            artifacts.selected(self.catalog, "unknown")
        self.assertEqual(artifacts.selected(self.catalog, "outputs"), [self.row])

    def test_missing_promisor_blob_never_causes_implicit_network(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                self.send_error(404)
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.git("config", "remote.origin.url", f"http://127.0.0.1:{server.server_port}/missing")
            self.git("config", "remote.origin.promisor", "true")
            self.git("config", "extensions.partialClone", "origin")
            (self.repo / ".git/objects" / self.row["gitBlob"][:2] / self.row["gitBlob"][2:]).unlink()
            with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                artifacts.build_catalog(self.repo, self.revision, [self.name])
            self.assertEqual(requests, [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_cli_build_check_and_boundary_are_standalone_stdlib(self):
        out = self.root / "built.json"
        self.assertEqual(artifacts.main(["build", "--repo", str(self.repo), "--revision", self.revision,
                                        "--paths", json.dumps([self.name]), "--out", str(out)]), 0)
        self.assertEqual(artifacts.main(["build", "--repo", str(self.repo), "--revision", self.revision,
                                        "--paths", json.dumps([self.name]), "--out", str(out)]), 0)
        unchanged = out.read_bytes()
        self.assertEqual(artifacts.main(["build", "--repo", str(self.repo), "--revision", self.revision,
                                        "--paths", json.dumps(["empty.raw"]), "--out", str(out)]), 1)
        self.assertEqual(out.read_bytes(), unchanged)
        args = ["restore", "--catalog", str(out), "--repo", str(self.repo), "--root", str(self.destination)]
        self.assertEqual(artifacts.main(args), 0)
        self.assertEqual(artifacts.main(["check", "--catalog", str(out), "--root", str(self.destination)]), 0)
        self.assertEqual(artifacts.main(["check-boundary", "--catalog", str(out), "--root", str(self.repo)]), 1)
        (self.destination / self.name).chmod(0o644)
        with self.assertRaisesRegex(ValueError, "mode"):
            artifacts.check_files([self.row], self.destination)


if __name__ == "__main__":
    unittest.main()
