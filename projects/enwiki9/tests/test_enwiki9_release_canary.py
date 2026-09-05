"""Bounded release acceptance; --bundle retains an independently verifiable receipt."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import enwiki9_clean_room_replay as replay
import enwiki9_dependency_closure as closure
import research_contracts

FIXTURE = ROOT / "tests/fixtures/enwiki9_release_canary"
CANDIDATE = "release_canary_rle_q0_v1"


def closure_args(bundle: Path) -> argparse.Namespace:
    return argparse.Namespace(
        candidate_id=CANDIDATE, source_root=FIXTURE / "package", bundle=bundle,
        entry_point="codec.c", platform="linux-x86-64",
        build_command_json=json.dumps(["/usr/bin/gcc", "-std=c99", "-O2", "{entry_point}", "-o", "{package}/codec"]),
        compress_command_json=json.dumps(["{package}/codec", "c", "{corpus}", "{archive}"]),
        decompress_command_json=json.dumps(["{package}/codec", "d", "{archive}", "{restored}"]),
        dependencies=FIXTURE / "dependencies.json", roles=None, required_option=["-std=c99", "-O2"],
        missing=[], declare_complete=True, require_license_audit=True)


class ReleaseCanaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="enwiki9-release-canary-test-")
        self.addCleanup(temporary.cleanup)
        self.tmp_path = Path(temporary.name)

    def test_tiny_input_cannot_enter_full_corpus_replay(self):
        tmp_path = self.tmp_path
        corpus = tmp_path / "synthetic.bin"
        corpus.write_bytes(b"a" * 1024)
        binding = research_contracts.objective_binding()
        replay.validate_corpus(corpus, binding, canary=True)
        with self.assertRaisesRegex(ValueError, "canonical full enwik9"):
            replay.validate_corpus(corpus, binding, canary=False)


    def test_canary_scope_is_bounded(self):
        tmp_path = self.tmp_path
        corpus = tmp_path / "oversized.bin"
        with corpus.open("wb") as stream:
            stream.truncate(replay.CANARY_MAX_INPUT_BYTES + 1)
        with self.assertRaisesRegex(ValueError, "synthetic bytes"):
            replay.validate_corpus(corpus, research_contracts.objective_binding(), canary=True)


    def test_missing_or_implicit_package_member_is_rejected(self):
        tmp_path = self.tmp_path
        package = tmp_path / "package"
        shutil.copytree(FIXTURE / "package", package)
        records = [{"path": p.name, "bytes": p.stat().st_size, "sha256": closure.digest(p)}
                   for p in sorted(package.iterdir())]
        replay.verify_package_copy(package, records)
        (package / "implicit").symlink_to(package / "codec.c")
        with self.assertRaisesRegex(ValueError, "symlink"):
            replay.verify_package_copy(package, records)
        (package / "implicit").unlink()
        (package / "codec.c").unlink()
        with self.assertRaisesRegex(ValueError, "counted manifest"):
            replay.verify_package_copy(package, records)


    def test_counted_license_and_approved_identifier_are_required(self):
        manifest = {"complete": True, "countedFiles": [{"path": "LICENSE", "role": "license"}],
                    "dependencies": json.loads((FIXTURE / "dependencies.json").read_text())}
        assert research_contracts.dependency_license_audit(manifest)["approved"]
        missing = copy.deepcopy(manifest)
        missing["countedFiles"] = []
        assert not research_contracts.dependency_license_audit(missing)["approved"]
        unapproved = copy.deepcopy(manifest)
        unapproved["dependencies"][0]["license"] = "unknown"
        assert not research_contracts.dependency_license_audit(unapproved)["approved"]


    def test_canary_cannot_claim_score(self):
        tmp_path = self.tmp_path
        path = tmp_path / "forged.json"
        path.write_text(json.dumps({"schema": "gamma.enwiki9.release-canary.v1",
                                   "evidenceClass": "synthetic-canary", "objectiveCredit": True,
                                   "fullCorpusProof": True, "officialScoreBytes": 1}))
        with self.assertRaisesRegex(ValueError, "cannot carry objective"):
            replay.validate_canary_receipt(path)


def run_canary(bundle: Path) -> Path:
    """Real package/build/replay/decode plus retained negative acceptance cases."""
    manifest_path = closure.materialize(closure_args(bundle))
    manifest = closure.load_json(manifest_path)
    corpus = bundle / "synthetic-input.bin"
    corpus.write_bytes(bytes(range(256)) * 4 + b"A" * 4096 + b"\x00" * 2048 + b"canary\n" * 64)
    args = argparse.Namespace(manifest=manifest_path, corpus=corpus, canary=True,
                              geekbench5_single_core_score=None, peer_receipt=None,
                              receipt_id=bundle.name, sample_interval_seconds=0.1)
    receipt_path = replay.replay(args)
    result = replay.validate_canary_receipt(receipt_path)

    negative = bundle / "missing-file"
    negative.mkdir()
    shutil.copytree(bundle / "package", negative / "package")
    negative_manifest = negative / "dependency-closure.json"
    shutil.copy2(manifest_path, negative_manifest)
    (negative / "package/codec.c").unlink()
    rejections = {}
    checks = {
        "missingManifestFile": lambda: research_contracts.validate_artifact(negative_manifest),
        "missingCleanBuildFile": lambda: replay.verify_package_copy(negative / "package", manifest["countedFiles"]),
        "tinyInputAsFullCorpus": lambda: replay.validate_corpus(corpus, research_contracts.objective_binding(), canary=False),
        "canaryAsObjectiveReceipt": lambda: research_contracts.validate_artifact(receipt_path),
    }
    for name, check in checks.items():
        try:
            check()
        except ValueError as exc:
            rejections[name] = {"rejected": True, "error": str(exc)}
        else:
            raise AssertionError(f"negative acceptance was admitted: {name}")
    license_report = closure.load_json(bundle / "license-audit.json")
    assert license_report["manifestSha256"] == "sha256:" + closure.digest(manifest_path)
    assert license_report["audit"] == research_contracts.dependency_license_audit(manifest)
    audit_path = bundle / "canary-validation.json"
    replay.write_json(audit_path, {
        "schema": "gamma.enwiki9.release-canary-validation.v1",
        "evidenceClass": "synthetic-canary", "objectiveCredit": False, "fullCorpusProof": False,
        "receipt": replay.artifact(audit_path, receipt_path),
        "harness": replay.artifact(audit_path, Path(__file__)),
        "closureTool": replay.artifact(audit_path, Path(closure.__file__)),
        "licenseReport": replay.artifact(audit_path, bundle / "license-audit.json"),
        "result": result, "negativeCases": rejections, "verdict": "canary-pass",
        "reproduce": ["python3", "tests/test_enwiki9_release_canary.py", "--bundle", "results/" + CANDIDATE + "/release/NEW_RECEIPT"],
        "verify": ["python3", "tools/enwiki9_clean_room_replay.py", "--verify-canary", str(receipt_path.relative_to(ROOT))],
    })
    return audit_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True,
                        help=f"new results/{CANDIDATE}/release/RECEIPT directory")
    args = parser.parse_args()
    path = run_canary(args.bundle.resolve())
    print(json.dumps({"validation": str(path.relative_to(ROOT)), "sha256": closure.digest(path)}, indent=2))
