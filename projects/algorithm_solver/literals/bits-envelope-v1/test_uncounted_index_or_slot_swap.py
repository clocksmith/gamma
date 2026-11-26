"""Negative tests for the TotalByteEnvelope: an uncounted index or a slot swap must be rejected.

Extends the slot-swap fixture of Gamma 06562147d (sixbit-v1/reproducibility/test_escape_slot_swap.py)
from press counts to bytes. The fixtures are built from the pinned c-w-compact package: its 80
packets are concatenated into one records blob with an index of 81 big-endian uint32 offsets,
beside the frozen dictionary. The honest claim is derived here by hand from file lengths and the
fixed packet header (LTE6, 32-byte dictionary hash, uint32 count = 40 B), not by calling the
checker, and must pass with 0 B drift. Every other fixture changes one thing and must fail.

    python3 -B -m unittest discover -s projects/algorithm_solver/literals/bits-envelope-v1 -v

Run from a Gamma checkout that contains the pin; GAMMA_CHECKOUT=/path overrides. Nothing in the
checkout is written.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ENVELOPE = HERE / "envelope.py"
GAMMA = Path(os.environ.get("GAMMA_CHECKOUT") or HERE.parents[3]).resolve()
PIN = "59ff04415ff2afd04ff2ed451340f4f02852bf18"
JOB = "projects/algorithm_solver/literals/sixbit-v1/run-v1/c-w-compact/"
FRAMING = 4 + 32 + 4  # LTE6 + dictionary hash + code count
DECODER = 1536        # the historical decoder charge in the frozen manifest
FROZEN_PACKAGE_BYTES = 13492


def git(*args):
    return subprocess.check_output(["git", "-C", str(GAMMA), *args])


class UncountedIndexOrSlotSwap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        git("rev-parse", PIN + "^{commit}")
        cls.manifest = json.loads(git("show", f"{PIN}:{JOB}manifest.json"))
        cls.dictionary = git("show", f"{PIN}:{JOB}dictionary.ltd")
        ids = list(cls.manifest["programs"])
        cls.packets = [git("show", f"{PIN}:{JOB}packets/{pid}.lte") for pid in ids]
        cls.tmp = tempfile.TemporaryDirectory(prefix="bits-envelope-")
        cls.root = Path(cls.tmp.name)
        offsets = [0]
        for packet in cls.packets:
            offsets.append(offsets[-1] + len(packet))
        cls.index = b"".join(o.to_bytes(4, "big") for o in offsets)
        cls.records = b"".join(cls.packets)
        n = len(cls.packets)
        cls.honest = {
            "payload": len(cls.records) - FRAMING * n,
            "framing": FRAMING * n,
            "dictionary": len(cls.dictionary),
            "index": 4 * (n + 1),
            "decoder": DECODER,
            "vocabulary": cls.manifest["vocabulary"],
            "ordered_vocab_sha256": hashlib.sha256(cls.dictionary).hexdigest(),
        }
        cls.honest["total"] = sum(cls.honest[k] for k in ("payload", "framing", "dictionary", "index", "decoder"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def bundle(self, name, dictionary=None, records=None, index=None, extra=None):
        folder = self.root / name
        folder.mkdir()
        (folder / "dictionary.ltd").write_bytes(self.dictionary if dictionary is None else dictionary)
        (folder / "records.bin").write_bytes(self.records if records is None else records)
        (folder / "index.bin").write_bytes(self.index if index is None else index)
        files = {"dictionary.ltd": "dictionary", "records.bin": "records", "index.bin": "index"}
        for filename, data in (extra or {}).items():
            (folder / filename).write_bytes(data)
        (folder / "bundle.json").write_text(json.dumps(
            {"records": len(self.packets), "escape": True, "decoder_bytes": DECODER, "files": files}))
        return folder

    def run_check(self, folder, claim):
        path = folder.parent / (folder.name + "-claim.json")
        path.write_text(json.dumps(claim))
        return subprocess.run([sys.executable, "-B", str(ENVELOPE), "--bundle", str(folder), str(path)],
                              capture_output=True, text=True)

    def assertRejected(self, result, reason):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(reason, result.stderr)

    def claim(self, **changes):
        claim = dict(self.honest, vocabulary=list(self.honest["vocabulary"]))
        claim.update(changes)
        return claim

    # -------------------------------------------------------------- the honest claim

    def test_honest_claim_has_zero_drift(self):
        result = self.run_check(self.bundle("honest"), self.claim())
        self.assertEqual(result.returncode, 0, result.stderr)
        out = json.loads(result.stdout)
        self.assertEqual(out["drift"], 0)
        self.assertEqual(out["random_access_total"], self.honest["total"])
        # The bundle is the frozen package plus exactly its index: 13,492 + 4 x 81 bytes.
        self.assertEqual(self.honest["total"], FROZEN_PACKAGE_BYTES + 4 * 81)

    # -------------------------------------------------------------- uncounted index

    def test_claim_without_index_is_rejected(self):
        claim = self.claim()
        del claim["index"]
        claim["total"] -= self.honest["index"]
        self.assertRejected(self.run_check(self.bundle("no-index-field"), claim), "uncounted index")

    def test_claim_with_zero_index_is_rejected(self):
        claim = self.claim(index=0, total=self.honest["total"] - self.honest["index"])
        self.assertRejected(self.run_check(self.bundle("zero-index"), claim), "uncounted index")

    def test_frozen_package_total_as_random_access_claim_is_rejected(self):
        # The frozen package_bytes, presented as if it were the random-access size.
        claim = self.claim(index=0, total=FROZEN_PACKAGE_BYTES)
        self.assertRejected(self.run_check(self.bundle("frozen-total"), claim), "uncounted index")

    def test_index_moved_into_payload_is_rejected(self):
        claim = self.claim(index=0, payload=self.honest["payload"] + self.honest["index"])
        self.assertRejected(self.run_check(self.bundle("index-as-payload"), claim), "uncounted index")

    def test_one_byte_drift_is_rejected(self):
        claim = self.claim(total=self.honest["total"] - 1)
        self.assertRejected(self.run_check(self.bundle("drift"), claim), "do not sum")

    def test_unlisted_file_is_rejected(self):
        folder = self.bundle("unlisted", extra={"spare.ltd": self.dictionary})
        self.assertRejected(self.run_check(folder, self.claim()), "bundle files and roles differ")

    def test_index_that_is_not_the_record_boundaries_is_rejected(self):
        offsets = [int.from_bytes(self.index[i:i + 4], "big") for i in range(0, len(self.index), 4)]
        offsets[1] += 1
        bad = b"".join(o.to_bytes(4, "big") for o in offsets)
        self.assertRejected(self.run_check(self.bundle("bad-index", index=bad), self.claim()), "")

    # -------------------------------------------------------------- slot swap

    def swapped_vocabulary(self):
        vocabulary = list(self.manifest["vocabulary"])
        j = next(k for k in range(1, len(vocabulary)) if vocabulary[k] != vocabulary[0])
        vocabulary[0], vocabulary[j] = vocabulary[j], vocabulary[0]
        return vocabulary

    def test_claimed_vocabulary_slot_swap_is_rejected(self):
        # 06562147d's fixture: same eligible set, same dictionary file, two manifest slots swapped.
        claim = self.claim(vocabulary=self.swapped_vocabulary())
        self.assertRejected(self.run_check(self.bundle("claim-swap"), claim), "ordered vocabulary differs")

    def test_dictionary_slot_swap_with_packets_kept_is_rejected(self):
        # Swap two slots in the stored dictionary; the packets still name the old dictionary.
        vocabulary = self.swapped_vocabulary()
        raw = [b"LTD1", len(vocabulary).to_bytes(4, "big")]
        for entry in vocabulary:
            raw += [len(entry.encode()).to_bytes(4, "big"), entry.encode()]
        swapped = b"".join(raw)
        self.assertEqual(len(swapped), len(self.dictionary))  # same bytes, other order
        claim = self.claim(vocabulary=vocabulary, ordered_vocab_sha256=hashlib.sha256(swapped).hexdigest())
        self.assertRejected(self.run_check(self.bundle("dict-swap", dictionary=swapped), claim),
                            "packet names a different dictionary")

    # -------------------------------------------------------------- the frozen packages

    def test_frozen_packages_reconcile_and_are_not_random_access_totals(self):
        result = subprocess.run([sys.executable, "-B", str(ENVELOPE), str(GAMMA)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = {r["job"]: r for r in json.loads(result.stdout)["packages"]}
        self.assertEqual(set(rows), {"b-w-compact", "b-u-compact", "c-w-compact", "c-u-compact"})
        for row in rows.values():
            self.assertEqual(row["package_bytes_drift"], 0)
            self.assertEqual(row["index"], 0)
            self.assertIsNone(row["random_access_total"])
        self.assertEqual(rows["c-w-compact"]["total"], FROZEN_PACKAGE_BYTES)


if __name__ == "__main__":
    unittest.main()
