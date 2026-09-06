#!/usr/bin/env python3
"""Use the measured SHA observer with the existing sixteen-phase MIDAS driver.

This adapter changes build authentication only. The sealed v1 driver still owns
execution, comparisons, divergence diagnostics and artifact publication.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import midas_open_observed_gate_v1 as original
from tools import midas_open_boundary_observer_sha_v1 as observer

SELF = "tools/midas_open_observed_sha_gate_v1.py"
UNIT = "operations/evidence/20260906_midas_open_boundary_observer_sha_unit.json"
base, parent = original.base, original.parent
require = base.require


def validate_unit(unit, inputs):
    """Require the actual six-test successor receipt and its source ancestry."""
    require(unit["id"] == "midas_open_boundary_observer_sha_unit_20260906" and
            unit["corpus_executed"] is False and unit["objective_credit_bytes"] == 0,
            "SHA observer unit identity differs")
    validation = unit["validation"]
    require(validation["returncode"] == 0 and validation["tests_passed"] == 6 and
            validation["inherited_observer_tests_passed"] == 5 and
            validation["digest_vectors"] == 138, "SHA observer unit did not pass")
    for field in ("additional_sha_test_passed", "hardware_branch_exercised",
                  "scalar_and_hashlib_parity", "original_observer_bytes_equal",
                  "all_compiler_dependencies_rehashed", "source_bindings_unchanged"):
        require(validation[field] is True, "missing SHA observer evidence: " + field)
    require(unit["resources"]["guard_pass"] is True and
            unit["resources"]["cleanup_complete"] is True, "unit guard is incomplete")
    refs = [*unit["source_bindings"], *(unit[k] for k in
            ("predecessor_unit", "upstream_provenance", "build_manifest", "binary"))]
    for row in refs:
        require(row["path"] in inputs and inputs[row["path"]]["sha256"].removeprefix("sha256:") ==
                row["sha256"].removeprefix("sha256:"), "unit authority is not bound: " + row["path"])


def authenticate(candidate, validate=False):
    require(re.fullmatch(r"[a-z0-9_]+", candidate) is not None, "invalid candidate")
    path = "operations/adaptive/experiments/" + candidate + ".json"
    data = base.bounded_read(ROOT / path, 8 * 1024**2)
    reference = {"path": path, "sha256": "sha256:" + base.digest(data)}
    if not validate:
        require(json.loads(os.environ["GAMMA_ENWIKI9_EXPERIMENT_JSON"]) == reference, "unbound invocation")
    contract = json.loads(data)
    require(contract["experimentId"] == candidate and contract["status"] == "frozen" and
            contract["registrationTiming"] == "prospective" and contract["objectiveCreditBytes"] == 0,
            "contract identity differs")
    inputs = base.contract_inputs(contract)
    for row in inputs.values():
        base.reference_bytes(ROOT, row)
    plans = [row for row in inputs.values() if row["id"] == "observed-gate-plan"]
    require(len(plans) == 1 and all(p in inputs for p in (SELF, original.SELF, UNIT)),
            "adapter, driver, plan or unit authority missing")
    plan = json.loads(base.reference_bytes(ROOT, plans[0]))
    original.validate_plan(plan, candidate)
    require(contract["population"]["scopeBytes"] == plan["population"]["bytes"] and
            contract["population"]["scopeSymbols"] == 8 * plan["population"]["bytes"], "population coordinates differ")
    require(plan["population"]["path"] in inputs, "unbound population")
    base.reference_bytes(ROOT, plan["population"])
    unit = json.loads(base.reference_bytes(ROOT, inputs[UNIT]))
    validate_unit(unit, inputs)
    manifests = {}
    for name, refs in plan["builds"].items():
        require(set(refs) == {"manifest", "binary"}, "build reference fields differ")
        for row in refs.values():
            require(row["path"] in inputs, "build file is not an input")
            base.reference_bytes(ROOT, row)
        manifest = json.loads(base.reference_bytes(ROOT, refs["manifest"]))
        interface = parent if name == "parent" else types.SimpleNamespace(
            SOURCES=observer.SOURCES, FLAGS=parent.FLAGS, file_record=parent.file_record)
        base.verify_build_sources(interface, manifest, inputs)
        binary = base.reference_bytes(ROOT, refs["binary"])
        require(manifest["binary"] == {"bytes": len(binary), "sha256": base.digest(binary)},
                "binary does not match manifest")
        if name == "observer":
            require(manifest["binary"] == {k: unit["binary"][k] for k in ("bytes", "sha256")},
                    "observer binary lacks SHA unit authority")
        manifests[name] = manifest
    for row in plan["runtime_files"]:
        require(Path(row["path"]).is_absolute() and parent.file_record(Path(row["path"])) == row, "runtime changed")
    return contract, plan, manifests


def configured_driver():
    # A private module keeps the sealed driver's globals intact for other users.
    spec = importlib.util.spec_from_file_location("midas_sha_gate_driver", ROOT / original.SELF)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    driver.authenticate = authenticate
    return driver


def main():
    return configured_driver().main()


if __name__ == "__main__":
    raise SystemExit(main())
