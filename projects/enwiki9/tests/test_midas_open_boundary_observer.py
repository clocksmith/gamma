"""Synthetic observer parity, exact snapshot coverage, and bounded diagnostics.

No corpus is read. Set MIDAS_OBSERVER_UNIT_DIR to a new directory to retain the
source-bound build and fixtures. Run only on the owner's assigned CPU/budget.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import midas_open_boundary_observer_v1 as observer


def independent_ranges(state):
    """Parse the frozen one-layer geometry without trusting native range labels."""
    offset = 0
    ranges = {"complete_state": (0, len(state))}

    def integer(width=8):
        nonlocal offset
        if offset + width > len(state):
            raise ValueError("independent state parser truncated")
        result = int.from_bytes(state[offset:offset + width], "little")
        offset += width
        return result

    def magic(value):
        nonlocal offset
        if state[offset:offset + 5] != value:
            raise ValueError("independent state parser magic differs")
        offset += 5

    def blob(name):
        nonlocal offset
        size = integer(); begin = offset
        if size > len(state) - offset:
            raise ValueError("independent state parser blob truncated")
        offset += size
        ranges[name] = (begin, size)
        return begin, size

    def vector(expected, width):
        nonlocal offset
        if integer() != expected:
            raise ValueError("independent frozen vector shape differs")
        if expected * width > len(state) - offset:
            raise ValueError("independent frozen vector truncated")
        offset += expected * width

    magic(b"GMST\1")
    for name in ("complete_predictor", "parent_identity_projection", "normalized_coder", "reference_model_projection"):
        blob(name)
    if offset != len(state):
        raise ValueError("independent state parser trailing bytes")
    offset = ranges["complete_predictor"][0]; magic(b"MBIT\1")
    blob("scheduler"); blob("byte_prefix")
    offset = ranges["scheduler"][0]; magic(b"MSCH\1")
    offset += 1 + 8 + 8 + 1 + 1024
    blob("decoded_prefix"); blob("sequence_origin"); backend, backend_size = blob("backend")
    ranges["scheduler_update_counters"] = (offset, 16); offset += 16
    blob("discarded_shadow")
    if offset != sum(ranges["scheduler"]):
        raise ValueError("independent scheduler does not close")
    offset = backend; magic(b"OPFI\1")
    if integer(4) != 0x4F504601:
        raise ValueError("independent model tag differs")
    offset += 8 + 1 + 3
    prefix = integer(1); offset += prefix
    ranges["model_header_prefix"] = (backend, offset - backend)
    ranges["model_probability_cache"] = (offset, 1024); offset += 1024
    begin = offset; vector(8 * 64, 2)
    ranges["recurrent_memory"] = (begin, offset - begin)
    # CanonicalGradientDescriptors for geometry {{64,1,1,64,8,8},1,256,0,64}:
    # output; 1 layer; shared relative bias; embedding; final normalization/bias.
    shapes = ((16384, 2), (512, 2), (1024, 2), (64, 2), (64, 2), (16, 2),
              (64, 2), (4096, 2), (4608, 2), (72, 2), (8192, 2), (4096, 2),
              (64, 2), (64, 2), (16384, 4), (64, 2), (64, 2), (256, 2))
    begin = offset
    for count, width in shapes:
        vector(count, width)
    ranges["parameters"] = (begin, offset - begin)
    begin = offset; integer()
    for count, width in shapes:
        vector(count if width == 2 else 0, 2)
        vector(count if width == 2 else 0, 2)
        vector(count if width == 4 else 0, 4)
    ranges["optimizer_moments_and_compensation"] = (begin, offset - begin)
    blob("incremental_cache")
    if offset != backend + backend_size:
        raise ValueError("independent model parser does not close")
    del ranges["backend"]
    return ranges


class BoundaryObserverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("g++"):
            raise AssertionError("provisioned compiler missing; no installation is attempted")
        retained = os.environ.get("MIDAS_OBSERVER_UNIT_DIR")
        if retained:
            cls.work = Path(retained).absolute(); cls.work.mkdir(mode=0o700)
        else:
            cls.directory = tempfile.TemporaryDirectory(prefix="gamma-midas-observer-")
            cls.addClassCleanup(cls.directory.cleanup); cls.work = Path(cls.directory.name)
        cls.built = observer.build(cls.work / "cache")
        cls.raw = bytes((17 * i + 3) & 255 for i in range(65))
        source = cls.work / "synthetic65"; source.write_bytes(cls.raw)
        cls.outputs, cls.receipts = {}, {}
        retained_hashes = {
            "P": "b42868fca6dce9d28652b6e27249df60f62506f56f60a9ace6df63ff40dd010e",
            "K": "b42868fca6dce9d28652b6e27249df60f62506f56f60a9ace6df63ff40dd010e",
            "F": "4db5dec01cd26e87d63de549c5c3250c42e3da979fe785812d1b71796c3417ad",
            "S": "246317ec4aa9ff5f0eeb23b58788a92b96c4a727db8f7b10e76fec671ad569a0",
        }
        for arm in "PKFS":
            output = cls.work / f"{arm}-encode"
            receipt = observer.execute(cls.built, operation="encode", arm=arm, max_raw_bytes=65,
                                       source=source, output=output, wall_seconds=120, snapshots=True)
            observed = receipt["bundle"]["artifacts"]["data"]["sha256"]
            if observed != retained_hashes[arm]:
                raise AssertionError(f"observer changed retained {arm} archive: {observed}")
            cls.outputs[arm] = {"encode": output}; cls.receipts[arm] = [receipt]
        source.unlink()  # Decoder receives only its archive in a fresh process.
        for arm in "PKFS":
            encoded = cls.outputs[arm]["encode"]
            decoded, repeat = cls.work / f"{arm}-decode", cls.work / f"{arm}-repeat"
            for operation, source, output in (("decode", encoded / "data", decoded), ("encode", decoded / "data", repeat)):
                receipt = observer.execute(cls.built, operation=operation, arm=arm, max_raw_bytes=65,
                                           source=source, output=output, wall_seconds=120, snapshots=True)
                cls.receipts[arm].append(receipt)
            cls.outputs[arm].update({"decode": decoded, "repeat": repeat})

    def native_rejection(self, *arguments):
        result = subprocess.run([str(self.built.binary), *map(str, arguments)], capture_output=True,
                                text=True, timeout=120, env={"PATH": os.defpath, "LC_ALL": "C"})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertTrue(result.stderr.startswith("midas_open_boundary_observer_v1: "), result.stderr)

    def test_unchanged_archives_independent_decoder_and_repeat_all_arms(self):
        for arm, outputs in self.outputs.items():
            encoded, decoded, repeat = [outputs[name] for name in ("encode", "decode", "repeat")]
            self.assertEqual((decoded / "data").read_bytes(), self.raw)
            self.assertEqual((encoded / "data").read_bytes(), (repeat / "data").read_bytes())
            for path in (decoded, repeat):
                comparison = observer.compare(encoded, path)
                self.assertTrue(comparison["equal"], comparison)
                for name in ("state.bin", "probabilities.bin", "boundaries.jsonl", "snapshots.bin"):
                    self.assertEqual((encoded / name).read_bytes(), (path / name).read_bytes(), (arm, name))
            self.assertEqual([(row["kind"], row["bit_position"]) for row in observer.boundary_rows(encoded / "boundaries.jsonl", 65)],
                             [("initial", 0), ("boundary", 256), ("boundary", 512), ("final", 520)])
        p, k = (self.outputs[arm]["encode"] for arm in "PK")
        self.assertTrue(observer.compare(p, k, projection="parent")["equal"])
        self.assertFalse(observer.compare(p, k)["equal"])
        print("BOUNDARY_OBSERVER_SYNTHETIC_JSON=" + json.dumps({
            "raw_hex": self.raw.hex(), "raw_source_removed_before_decode": True,
            "arms": self.receipts, "cpu_affinity": sorted(os.sched_getaffinity(0)),
            "scope": "synthetic65 exact archives and every32byte state/probability observations",
            "resource_qualified": False, "objective_credit_bytes": 0}, sort_keys=True))

    def test_independent_state_ranges_and_mutations_cover_every_component(self):
        mutated_names = set()
        for arm in "PKFS":
            output = self.outputs[arm]["encode"]
            rows = list(observer.boundary_rows(output / "boundaries.jsonl", 65))
            snapshots = list(observer.snapshot_records(output / "snapshots.bin"))
            self.assertEqual(len(rows), len(snapshots))
            for row, snapshot in zip(rows, snapshots):
                expected = independent_ranges(snapshot["state"])
                self.assertEqual({part["name"]: (part["offset"], part["bytes"]) for part in row["parts"]}, expected)
                observer.validate_snapshot(row, snapshot)
                for part in row["parts"]:
                    if part["bytes"] == 0:
                        continue
                    corrupted = dict(snapshot); data = bytearray(snapshot["state"])
                    # Alter an actual retained byte, not a digest supplied to the checker.
                    data[part["offset"] + part["bytes"] - 1] ^= 1; corrupted["state"] = bytes(data)
                    with self.assertRaisesRegex(ValueError, "snapshot digest differs"):
                        observer.validate_snapshot(row, corrupted)
                    changed = corrupted["state"][part["offset"]:part["offset"] + part["bytes"]]
                    self.assertNotEqual(hashlib.sha256(changed).hexdigest(), part["sha256"])
                    mutated_names.add(part["name"])
        self.assertEqual(mutated_names, set(observer.PART_NAMES))

    def test_first_divergence_and_missing_truncated_extra_trace_diagnostics(self):
        reference = self.outputs["P"]["encode"]
        with tempfile.TemporaryDirectory(dir=self.work) as directory:
            root = Path(directory); changed = root / "changed"; shutil.copytree(reference, changed)
            path = changed / "probabilities.bin"; original = path.read_bytes(); data = bytearray(original)
            data[21 + 2 * 257] ^= 1; path.write_bytes(data)
            result = observer.compare(reference, changed, diagnostic=root / "first-probability.json")
            self.assertEqual((result["kind"], result["bit_position"]), ("probability", 257))
            self.assertEqual(result["reference_context"]["first_bit"], 253)
            self.assertEqual(len(result["reference_context"]["probabilities"]), 9)
            path.write_bytes(original)
            boundary = changed / "boundaries.jsonl"; boundary_original = boundary.read_bytes()
            rows = [json.loads(line) for line in boundary_original.splitlines()]
            parameters = next(part for part in rows[1]["parts"] if part["name"] == "parameters")
            parameters["sha256"] = "f" * 64
            boundary.write_text("".join(json.dumps(row) + "\n" for row in rows))
            result = observer.compare(reference, changed, diagnostic=root / "first-state.json")
            self.assertEqual((result["kind"], result["bit_position"]), ("boundary", 256))
            self.assertEqual(result["components"], ["parameters"])
            self.assertEqual(result["previous"]["reference"]["bit_position"], 0)
            self.assertEqual(result["next"]["reference"]["bit_position"], 512)
            boundary.write_bytes(boundary_original)
            for number, payload in enumerate((original[:-1], original + b"\0\0", None)):
                if payload is None:
                    path.unlink()
                else:
                    path.write_bytes(payload)
                diagnostic = root / f"incomplete-{number}.json"
                result = observer.compare(reference, changed, diagnostic=diagnostic)
                self.assertFalse(result["equal"])
                self.assertEqual(result["kind"], "trace-completeness")
                self.assertEqual(json.loads(diagnostic.read_text()), result)
            path.write_bytes(original)
            for payload in (boundary_original.rsplit(b"\n", 2)[0] + b"\n", boundary_original + b"{}\n"):
                boundary.write_bytes(payload)
                self.assertEqual(observer.compare(reference, changed)["kind"], "trace-completeness")
            with self.assertRaises(FileExistsError):
                observer.compare(reference, reference, diagnostic=root / "first-probability.json")

    def test_identical_invalid_bundles_cannot_pass_comparison(self):
        with tempfile.TemporaryDirectory(dir=self.work) as directory:
            changed = Path(directory) / "changed"
            shutil.copytree(self.outputs["P"]["encode"], changed)
            path = changed / "probabilities.bin"
            original = path.read_bytes(); data = bytearray(original)
            data[21:23] = b"\0\0"; path.write_bytes(data)
            self.assertEqual(observer.compare(changed, changed)["kind"], "trace-completeness")
            path.write_bytes(original)
            state = changed / "state.bin"; data = bytearray(state.read_bytes())
            data[-1] ^= 1; state.write_bytes(data)
            self.assertEqual(observer.compare(changed, changed)["kind"], "trace-completeness")
            state.unlink()
            self.assertEqual(observer.compare(changed, changed)["kind"], "trace-completeness")

    def test_empty_digest_mode_and_rejection_publication(self):
        with tempfile.TemporaryDirectory(dir=self.work) as directory:
            root = Path(directory); empty = root / "empty"; empty.write_bytes(b"")
            encoded, decoded = root / "encoded", root / "decoded"
            for operation, source, output in (("encode", empty, encoded), ("decode", encoded / "data", decoded)):
                receipt = observer.execute(self.built, operation=operation, arm="P", max_raw_bytes=1,
                                           source=source, output=output, wall_seconds=120)
                self.assertEqual(receipt["bundle"]["summary"]["boundary_records"], 2)
                self.assertEqual((output / "snapshots.bin").read_bytes(), b"MOSNAP01\0")
            self.assertEqual((decoded / "data").read_bytes(), b"")
            self.assertTrue(observer.compare(encoded, decoded)["equal"])
            occupied = root / "occupied"; occupied.mkdir(); (occupied / "keep").write_bytes(b"untouched")
            self.native_rejection("encode", "P", 1, empty, occupied, "digest")
            self.assertEqual((occupied / "keep").read_bytes(), b"untouched")
            symlink = root / "symlink"; symlink.symlink_to(empty)
            fifo = root / "fifo"; os.mkfifo(fifo)
            too_large = root / "too-large"; too_large.write_bytes(bytes(130))
            bad = root / "bad"; data = bytearray((encoded / "data").read_bytes()); data[-1] ^= 1; bad.write_bytes(data)
            output = root / "refused"
            for arguments in (("encode", "P", 1, symlink, output, "digest"),
                              ("encode", "P", 1, fifo, output, "digest"),
                              ("encode", "P", 130, too_large, output, "snapshots"),
                              ("decode", "F", 1, encoded / "data", output, "digest"),
                              ("decode", "P", 1, bad, output, "digest"),
                              ("encode", "P", 0, empty, output, "digest")):
                self.native_rejection(*arguments)
                self.assertFalse(output.exists())
                self.assertEqual(list(root.glob(".midas-observer-*")), [])
                self.assertEqual(list(root.glob(".midas-observed-*")), [])


if __name__ == "__main__":
    unittest.main()
