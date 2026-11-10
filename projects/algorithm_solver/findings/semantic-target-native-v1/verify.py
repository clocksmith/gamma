"""Retain real-sandbox target-builder controls using the existing authored fixture.

No model, corpus, reserved payload, training or injected judge is used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

LANE = Path(__file__).resolve().parents[2]
ROOT = LANE.parents[1]
sys.path.insert(0, str(LANE))
sys.path.insert(0, str(LANE / "tests"))

from algsolve.judge import sandbox
from test_semantic_target_pipeline import TargetBuilderTests


def run(output):
    if sys.platform != "linux":
        raise RuntimeError("Native qualification requires the unchanged Linux sandbox")
    sandbox.check_available()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    for name in ("correct-length", "wrong-constant"):
        fixture = TargetBuilderTests()
        fixture.setUp()
        try:
            if name == "wrong-constant":
                fixture.proposal["program"]["return"] = {"literal": 1}
            summary = fixture.build(judge=None, teacher_identity="authored-length-control-v1")
            candidate = fixture.receipt()["proposals"][0]
            expected = 1 if name == "correct-length" else 0
            if summary["training_eligible_pairs"] != expected:
                raise AssertionError(f"Unexpected target qualification: {fixture.receipt()}")
            if not candidate["verdicts"]["public"]["passed"]:
                raise AssertionError("Both controls must pass the public example")
            if candidate["verdicts"]["independent"]["passed"] != bool(expected):
                raise AssertionError("Independent tests did not distinguish the controls")
            if expected and not candidate["verdicts"]["declared_bound_probe"]["passed"]:
                raise AssertionError("Correct control must pass the declared-bound probe")
            if not expected and "declared_bound_probe" in candidate["verdicts"]:
                raise AssertionError("Qualification continued after independent failure")
            if fixture.events != ["payload", "teacher", "tests"]:
                raise AssertionError("Unexpected adapter access or injected judge")
            results[name] = {"counts": summary["counts"],
                             "emitted_pairs": summary["emitted_pairs"],
                             "candidate_reason": candidate["reason"],
                             "verdicts": candidate["verdicts"], "adapter_events": fixture.events}
        finally:
            # Preserve failed attempts as well as successful ones.
            shutil.copytree(fixture.root, output / name)
            fixture.doCleanups()
    sources = [Path(__file__), LANE / "tests/test_semantic_target_pipeline.py"]
    receipt = {
        "schema": "gamma.semantic-target-native-controls.v1",
        "evidence_class": "authored integration controls through real sandbox",
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": platform.python_version(), "platform": platform.platform(),
        "sources_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "results": results, "judge_injected": False, "model_run": False,
        "training": False, "protected_payloads_loaded": False,
        "corpus_qualification": False,
        "artifacts_sha256": {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sorted(output.rglob("*")) if p.is_file()},
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"correct_qualified": True, "wrong_rejected": True, "receipt": str(output / "receipt.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
