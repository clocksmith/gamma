"""Bounded source packaging, rejected inputs and clean relocated native replay."""
import copy
import dataclasses
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import midas_open_source_bundle_v1 as bundle
from tools import midas_open_codec_v1 as codec


def child_limits():
    for kind, ceiling in ((resource.RLIMIT_AS, 2 * 1024**3), (resource.RLIMIT_CPU, 120),
                          (resource.RLIMIT_FSIZE, 32 * 1024**2)):
        soft, hard = resource.getrlimit(kind)
        values = [ceiling, *(value for value in (soft, hard) if value != resource.RLIM_INFINITY)]
        resource.setrlimit(kind, (min(values), min(values)))


def rewrite_zip(data, transform):
    target = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as original, zipfile.ZipFile(target, "w") as output:
        members = [(copy.copy(info), original.read(info)) for info in original.infolist()]
        for info, payload in transform(members):
            output.writestr(info, payload)
    return target.getvalue()


class SourceBundleUnitTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="gamma-midas-bundle-unit-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.files = {"LICENSE": b"test fixture only\n", "projects/enwiki9/a.txt": b"abc\x00\xff"}
        self.data = bundle.encode_bundle(self.files)

    def test_deterministic_bundle_exact_manifest_and_safe_extraction(self):
        self.assertEqual(self.data, bundle.encode_bundle(dict(reversed(list(self.files.items())))))
        manifest, files = bundle.verify_bytes(self.data, bundle.digest(self.data))
        self.assertEqual(files, self.files)
        self.assertIsNone(manifest["complete_package_bytes"])
        self.assertFalse(manifest["complete_package_qualified"])
        source = self.root / "source.zip"; source.write_bytes(self.data)
        result = bundle.extract(source, self.root / "out", bundle.digest(self.data))
        self.assertFalse(result["code_executed"])
        self.assertEqual(result["objective_credit_bytes"], 0)
        for name, expected in self.files.items():
            self.assertEqual((self.root / "out" / name).read_bytes(), expected)
        self.assertEqual(sorted(str(path.relative_to(self.root / "out"))
                                for path in (self.root / "out").rglob("*") if path.is_file()),
                         sorted([*self.files, bundle.MANIFEST]))

    def test_refuses_bad_digest_traversal_aliases_links_and_duplicates(self):
        for bad in ("", "0" * 64, "A" * 64, "z" * 64):
            with self.assertRaises(ValueError):
                bundle.verify_bytes(self.data, bad)
        for name in ("../outside", "/absolute", "a/../b", "a//b", "a/./b", "a\\b", "a/", "a\x00b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                bundle.safe_name(name)
        def altered_name(members):
            members[0][0].filename = "../outside"
            return members
        def symlink(members):
            members[0][0].external_attr = 0o120777 << 16
            return members
        def duplicate(members):
            members[1][0].filename = members[0][0].filename
            return members
        for transform in (altered_name, symlink, duplicate):
            with self.subTest(transform=transform.__name__):
                data = rewrite_zip(self.data, transform)
                with self.assertRaises(ValueError):
                    bundle.verify_bytes(data, bundle.digest(data))

    def test_manifest_mismatch_unknown_files_and_source_mutation_rejected(self):
        def wrong_source(members):
            return [(info, b"changed" if info.filename == "LICENSE" else payload)
                    for info, payload in members]
        def missing_source(members):
            return [(info, payload) for info, payload in members if info.filename != "LICENSE"]
        def unknown_file(members):
            info = copy.copy(members[-1][0]); info.filename = "z-extra"
            return [*members, (info, b"extra")]
        def duplicate_json(members):
            return [(info, payload.replace(b'"schema":', b'"schema": "bad", "schema":', 1)
                     if info.filename == bundle.MANIFEST else payload) for info, payload in members]
        for transform in (wrong_source, missing_source, unknown_file, duplicate_json):
            data = rewrite_zip(self.data, transform)
            with self.subTest(transform=transform.__name__), self.assertRaises(ValueError):
                bundle.verify_bytes(data, bundle.digest(data))

    def test_bounds_cover_count_expansion_and_nonregular_files(self):
        with mock.patch.object(bundle, "MAX_FILES", 2), self.assertRaises(ValueError):
            bundle.verify_bytes(self.data, bundle.digest(self.data))
        with mock.patch.object(bundle, "LIMIT", len(self.data) + 1), self.assertRaisesRegex(ValueError, "expanded"):
            bundle.verify_bytes(self.data, bundle.digest(self.data))
        regular = self.root / "regular"; regular.write_bytes(b"abc")
        fifo = self.root / "fifo"; os.mkfifo(fifo)
        link = self.root / "link"; link.symlink_to(regular)
        for path in (fifo, link, self.root):
            with self.subTest(path=path), self.assertRaises((ValueError, OSError)):
                bundle.read_regular(path)
        with self.assertRaises(ValueError):
            bundle.read_regular(regular, 2)

    def test_equivalent_noncanonical_manifest_is_not_silently_rewritten(self):
        def compact(members):
            return [(info, json.dumps(json.loads(payload), separators=(",", ":")).encode()
                     if info.filename == bundle.MANIFEST else payload) for info, payload in members]
        data = rewrite_zip(self.data, compact)
        with self.assertRaisesRegex(ValueError, "noncanonical manifest"):
            bundle.verify_bytes(data, bundle.digest(data))

    def test_file_directory_prefix_collision_fails_before_extraction(self):
        def collision(members):
            for info, _ in members:
                if info.filename == "LICENSE":
                    info.filename = "projects"
            return sorted(members, key=lambda pair: pair[0].filename)
        data = rewrite_zip(self.data, collision)
        with self.assertRaisesRegex(ValueError, "prefix collision"):
            bundle.verify_bytes(data, bundle.digest(data))

    def test_collection_enforces_remaining_budget_before_read(self):
        gamma = self.root / "gamma"
        project = gamma / "projects/enwiki9"
        project.mkdir(parents=True)
        a, b = gamma / "a", gamma / "b"
        a.write_bytes(b"123"); b.write_bytes(b"456")
        rows = [{"path": str(path), "bytes": 3, "sha256": bundle.digest(path.read_bytes())}
                for path in (a, b)]
        with mock.patch.object(bundle, "ROOT", project), mock.patch.object(bundle, "LIMIT", 5), \
                mock.patch.object(codec, "inventory", return_value={"local_source_files": rows}), \
                mock.patch.object(bundle, "read_regular", wraps=bundle.read_regular) as read:
            with self.assertRaises(ValueError):
                bundle.collect(None)
            self.assertEqual([call.args[1] for call in read.call_args_list], [5, 2])

    def test_existing_outputs_are_never_replaced(self):
        source = self.root / "source.zip"; source.write_bytes(self.data)
        file = self.root / "file"; file.write_bytes(b"keep")
        empty = self.root / "empty"; empty.mkdir()
        directory = self.root / "directory"; directory.mkdir(); (directory / "keep").write_bytes(b"keep")
        link = self.root / "link"; link.symlink_to(directory, target_is_directory=True)
        dangling = self.root / "dangling"; dangling.symlink_to(self.root / "absent")
        for target in (file, empty, directory, link, dangling):
            with self.subTest(target=target):
                with self.assertRaises(FileExistsError):
                    bundle.publish_file(target, b"must not replace")
                with self.assertRaises(FileExistsError):
                    bundle.extract(source, target, bundle.digest(self.data))
        self.assertEqual(file.read_bytes(), b"keep")
        self.assertEqual((directory / "keep").read_bytes(), b"keep")
        self.assertTrue(link.is_symlink())
        self.assertEqual(list(self.root.glob(".midas-source-*")), [])


class RelocatedMidasBundleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("g++"):
            raise unittest.SkipTest("existing g++ required; no installation")
        cls.directory = tempfile.TemporaryDirectory(prefix="gamma-midas-relocated-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name)

    def command(self, args, cwd):
        if args[0] == sys.executable:
            args = [args[0], "-I", "-S", "-B", *args[1:]]
        result = subprocess.run(args, cwd=cwd, env={"PATH": os.defpath, "LC_ALL": "C",
                                "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True,
                                timeout=120, preexec_fn=child_limits)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_relocated_rebuild_repack_and_all_arm_inverse(self):
        work = self.root
        original = self.command([sys.executable, str(ROOT / "tools/midas_open_codec_v1.py"),
                                "--cache-dir", str(work / "original-cache"), "build"], ROOT)
        built = dataclasses.make_dataclass("Built", ["binary", "manifest"])(
            Path(original["binary"]), original["manifest"])
        archive = work / "source.zip"
        receipt = bundle.pack(built, archive)
        data = archive.read_bytes()
        self.assertIn("projects/enwiki9/programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/profile_forward.cpp",
                      [row["path"] for row in receipt["manifest"]["files"]])
        bundle.extract(archive, work / "restored", receipt["bundle_sha256"])
        restored = work / "restored/projects/enwiki9"
        rebuilt = self.command([sys.executable, str(restored / "tools/midas_open_codec_v1.py"),
                                "--cache-dir", str(work / "restored-cache"), "build"], restored)
        self.assertFalse(rebuilt["cache_hit"])
        self.assertNotEqual(original["manifest"]["identity"], rebuilt["manifest"]["identity"])
        binary_exact = Path(original["binary"]).read_bytes() == Path(rebuilt["binary"]).read_bytes()
        self.assertTrue(binary_exact, "relocated native executable differs on the bound toolchain")
        again = self.command([sys.executable, str(restored / "tools/midas_open_source_bundle_v1.py"),
                              "pack", "--cache-dir", str(work / "restored-cache"),
                              "--output", str(work / "repacked.zip")], restored)
        self.assertEqual((work / "repacked.zip").read_bytes(), data)
        self.assertEqual(again, receipt)
        raw = bytes((17 * index + 3) & 255 for index in range(65))
        known = json.loads((ROOT / "operations/evidence/20260905_midas_open_profile_parent_roundtrip_unit.json").read_text())
        arms = {}
        for arm in "PKFS":
            source = work / (arm + "-raw"); source.write_bytes(raw)
            encoded, inverse, repeat = [work / (arm + suffix) for suffix in ("-encode", "-inverse", "-repeat")]
            summary = self.command([rebuilt["binary"], "encode", arm, "65", str(source), str(encoded)], restored)
            source.unlink()  # This test's private fixture, not user/corpus input.
            self.command([rebuilt["binary"], "decode", arm, "65", str(encoded / "data"), str(inverse)], restored)
            self.command([rebuilt["binary"], "encode", arm, "65", str(inverse / "data"), str(repeat)], restored)
            archive_bytes = (encoded / "data").read_bytes()
            self.assertEqual(hashlib.sha256(archive_bytes).hexdigest(), known["finite_artifacts"]["arms"][arm]["archive_sha256"])
            self.assertEqual((inverse / "data").read_bytes(), raw)
            self.assertEqual((repeat / "data").read_bytes(), archive_bytes)
            self.assertEqual((inverse / "state.bin").read_bytes(), (encoded / "state.bin").read_bytes())
            self.assertEqual((repeat / "state.bin").read_bytes(), (encoded / "state.bin").read_bytes())
            arms[arm] = {"archive_hex": archive_bytes.hex(), "archive_bytes": len(archive_bytes),
                         "archive_sha256": bundle.digest(archive_bytes), "raw_inverse_exact": True,
                         "reencode_exact": True, "final_state_exact": True,
                         "source_removed_before_decode": True, "summary": summary,
                         "state_components": codec.state_records(encoded / "state.bin")}
        self.assertEqual(arms["P"]["archive_hex"], arms["K"]["archive_hex"])
        self.assertEqual(arms["P"]["state_components"]["parent_identity_projection"],
                         arms["K"]["state_components"]["parent_identity_projection"])
        identity_digest = lambda identity: bundle.digest(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode())
        artifacts = {"bundle": receipt, "extracted_repack_exact": True,
                     "relocated_binary_exact": binary_exact, "raw_hex": raw.hex(),
                     "original_binary": original["manifest"]["binary"],
                     "toolchain": original["manifest"]["identity"]["compiler"],
                     "arms": arms, "original_build_cache_identity_sha256": identity_digest(original["manifest"]["identity"]),
                     "relocated_build_cache_identity_sha256": identity_digest(rebuilt["manifest"]["identity"]),
                     "isolated_python_flags": ["-I", "-S", "-B"],
                     "compiler_dependency_files": len(original["manifest"]["identity"]["dependencies"]),
                     "no_corpus_access": True, "resource_qualified": False, "objective_credit_bytes": 0}
        print("MIDAS_SOURCE_BUNDLE_JSON=" + json.dumps(artifacts, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
