"""Standalone MIDAS I/O, reference identity, state closure and bounded inventory."""
import hashlib
import dataclasses
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import midas_open_codec_v1 as codec


def child_limits():
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))


class StandaloneMidasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("g++"):
            raise unittest.SkipTest("g++ required; never installed by tests")
        cls.directory = tempfile.TemporaryDirectory(prefix="gamma-midas-standalone-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.work = Path(cls.directory.name)
        cls.cache = cls.work / "cache"
        command = [sys.executable, str(ROOT / "tools/midas_open_codec_v1.py"),
                   "--cache-dir", str(cls.cache), "build"]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                               timeout=120, preexec_fn=child_limits)
        if built.returncode:
            raise AssertionError(built.stdout + built.stderr)
        cls.first_build = json.loads(built.stdout)
        cls.built = codec.build(cls.cache)

    def native(self, *args, success=True, binary=None):
        result = subprocess.run([str(binary or self.built.binary), *map(str, args)],
                                cwd=ROOT, capture_output=True, text=True,
                                timeout=120, preexec_fn=child_limits)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def test_cached_build_is_reused(self):
        self.assertFalse(self.first_build["cache_hit"])
        self.assertTrue(self.built.cache_hit)
        repeated = codec.build(self.cache)
        self.assertTrue(repeated.cache_hit)
        self.assertEqual(repeated.binary, self.built.binary)
        self.assertEqual(repeated.manifest, self.built.manifest)

    def test_all_arms_keep_retained_archives_and_exact_states(self):
        with tempfile.TemporaryDirectory(dir=self.work) as directory:
            root = Path(directory)
            raw = bytes((17 * i + 3) & 255 for i in range(65))
            source = root / "source"; source.write_bytes(raw)
            retained = json.loads((ROOT / "operations/evidence/20260905_midas_open_profile_parent_roundtrip_unit.json").read_text())
            identities = {}
            for arm in "PKFS":
                encoded, decoded, repeat = [root / (arm + suffix) for suffix in ("-encode", "-decode", "-repeat")]
                encoded_record = codec.execute(self.built, operation="encode", arm=arm, max_raw_bytes=65,
                                               source=source, output=encoded, wall_seconds=120)
                self.assertEqual(hashlib.sha256((encoded / "data").read_bytes()).hexdigest(),
                                 retained["finite_artifacts"]["arms"][arm]["archive_sha256"])
                self.native("decode", arm, 65, encoded / "data", decoded)
                self.assertEqual((decoded / "data").read_bytes(), raw)
                self.assertEqual((decoded / "state.bin").read_bytes(), (encoded / "state.bin").read_bytes())
                self.native("encode", arm, 65, decoded / "data", repeat)
                self.assertEqual((repeat / "data").read_bytes(), (encoded / "data").read_bytes())
                self.assertEqual((repeat / "state.bin").read_bytes(), (encoded / "state.bin").read_bytes())
                identities[arm] = encoded_record["state_components"]["parent_identity_projection"]
                self.assertFalse(encoded_record["resource_qualified"])
            self.assertEqual(identities["P"], identities["K"])

    def test_extended_synthetic_reference_roundtrip(self):
        reference = codec.build(self.cache, reference=True)
        with tempfile.TemporaryDirectory(dir=self.work) as directory:
            root = Path(directory)
            raw = bytes((17 * i + 3) & 255 for i in range(1024))
            source = root / "source"; source.write_bytes(raw)
            inc, ref, inverse, repeat = [root / name for name in ("incremental", "reference", "inverse", "repeat")]
            inc_record = codec.execute(self.built, operation="encode", arm="F", max_raw_bytes=1024,
                                       source=source, output=inc, wall_seconds=120)
            ref_record = codec.execute(reference, operation="encode", arm="F", max_raw_bytes=1024,
                                       source=source, output=ref, wall_seconds=120)
            self.assertEqual((inc / "data").read_bytes(), (ref / "data").read_bytes())
            self.assertEqual(inc_record["state_components"]["reference_model_projection"],
                             ref_record["state_components"]["reference_model_projection"])
            source.unlink()  # Private synthetic source only; decoder receives the archive alone.
            self.native("decode", "F", 1024, inc / "data", inverse)
            self.assertEqual((inverse / "data").read_bytes(), raw)
            self.assertEqual((inc / "state.bin").read_bytes(), (inverse / "state.bin").read_bytes())
            self.native("encode", "F", 1024, inverse / "data", repeat)
            self.assertEqual((inc / "data").read_bytes(), (repeat / "data").read_bytes())
            self.assertEqual(inc_record["operation"]["model_updates"], 32)
            artifacts = {"raw_hex": raw.hex(), "raw_sha256": hashlib.sha256(raw).hexdigest(),
                         "archive_hex": (inc / "data").read_bytes().hex(),
                         "archive_sha256": hashlib.sha256((inc / "data").read_bytes()).hexdigest(),
                         "incremental": inc_record, "reference": ref_record,
                         "inverse_exact": True, "reencode_exact": True, "source_removed_before_decode": True}
            print("STANDALONE_SYNTHETIC_JSON=" + json.dumps(artifacts, sort_keys=True))

    def test_fail_closed_inputs_and_atomic_outputs(self):
        with tempfile.TemporaryDirectory(dir=self.work) as directory:
            root = Path(directory); source = root / "source"; source.write_bytes(b"abc")
            occupied = root / "occupied"; occupied.mkdir(); (occupied / "keep").write_bytes(b"untouched")
            self.native("encode", "P", 3, source, occupied, success=False)
            self.assertEqual((occupied / "keep").read_bytes(), b"untouched")
            symlink = root / "source-link"; symlink.symlink_to(source)
            fifo = root / "fifo"; os.mkfifo(fifo)
            output = root / "rejected"
            for args in (("encode", "P", 3, symlink), ("encode", "P", 3, fifo), ("encode", "P", 2, source),
                         ("encode", "P", 250001, source), ("encode", "P", 0, source),
                         ("encode", "bad", 3, source), ("decode", "P", 3, source)):
                self.native(*args, output, success=False)
                self.assertFalse(output.exists())
                self.assertEqual(list(root.glob(".midas-codec-*")), [])
            empty = root / "empty"; empty.write_bytes(b"")
            encoded, decoded = root / "encoded", root / "decoded"
            self.native("encode", "P", 1, empty, encoded)
            self.native("decode", "P", 1, encoded / "data", decoded)
            self.assertEqual((decoded / "data").read_bytes(), b"")
            damaged = root / "damaged"; data = bytearray((encoded / "data").read_bytes()); data[-1] ^= 1
            damaged.write_bytes(data)
            self.native("decode", "P", 1, damaged, output, success=False)
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".midas-codec-*")), [])
            (root / "output-link").symlink_to(occupied, target_is_directory=True)
            self.native("encode", "P", 3, source, root / "output-link", success=False)
            self.assertEqual((occupied / "keep").read_bytes(), b"untouched")

    def test_inventory_is_measured_not_complete_package_credit(self):
        result = codec.inventory(self.built)
        self.assertGreater(result["binary"]["bytes"], 0)
        self.assertGreater(result["local_source_bytes"], 0)
        self.assertTrue(result["runtime"]["files"])
        self.assertEqual(result["runtime"]["missing"], [])
        self.assertFalse(result["complete_package_qualified"])
        self.assertIsNone(result["complete_package_bytes"])
        self.assertEqual(result["objective_credit_bytes"], 0)
        print("STANDALONE_INVENTORY_JSON=" + json.dumps(result, sort_keys=True))

    def test_interrupted_synthetic_encode_leaves_no_training_staging(self):
        with tempfile.TemporaryDirectory(dir=self.work) as directory:
            root = Path(directory)
            source, output = root / "synthetic", root / "output"
            source.write_bytes(b"\x19" * 250000)
            # An intentional operational-stop test, not a completed population
            # or a scientific gate. The fixed neural driver remains unfinished
            # at this bound; no archive result is inspected or credited.
            with self.assertRaises(subprocess.TimeoutExpired):
                codec.execute(self.built, operation="encode", arm="F", max_raw_bytes=250000,
                              source=source, output=output, wall_seconds=1)
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".midas-codec-*")), [])

    def test_inventory_and_execution_reject_stale_build_bindings(self):
        with tempfile.TemporaryDirectory(dir=self.work) as directory:
            root = Path(directory)
            replaced_binary = root / "program"; replaced_binary.write_bytes(b"not the compiled program")
            stale_binary = dataclasses.replace(self.built, binary=replaced_binary)
            with self.assertRaisesRegex(ValueError, "build manifest"):
                codec.inventory(stale_binary)
            with self.assertRaisesRegex(ValueError, "build manifest"):
                codec.execute(stale_binary, operation="encode", arm="P", max_raw_bytes=1,
                              source=root / "absent", output=root / "output", wall_seconds=1)
            header = root / "private.hpp"; header.write_bytes(b"old source")
            bound = codec.file_record(header)
            manifest = json.loads(json.dumps(self.built.manifest))
            manifest["identity"]["dependencies"].append(bound)
            stale_source = dataclasses.replace(self.built, manifest=manifest)
            header.write_bytes(b"new source")
            with self.assertRaisesRegex(ValueError, "dependency changed"):
                codec.inventory(stale_source)

    def test_state_reader_rejects_truncation_and_trailing_bytes(self):
        with tempfile.TemporaryDirectory(dir=self.work) as directory:
            state = Path(directory) / "state"
            for data in (b"", b"GMST\x01", b"GMST\x01" + b"\xff" * 8,
                         b"GMST\x01" + b"\x00" * 32 + b"extra"):
                state.write_bytes(data)
                with self.assertRaises(ValueError):
                    codec.state_records(state)


if __name__ == "__main__":
    unittest.main()
