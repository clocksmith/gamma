from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

import pytest


PROJECT = Path(__file__).resolve().parents[1]
TOOL = (
    PROJECT
    / "tools/endpoint428_horizon_retained_parent_trace_output_closure_q0_v2.py"
)
TERMINAL_TESTS = PROJECT / "tests/test_endpoint428_horizon_terminal_route_v1.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


closure = load_module("_horizon_output_closure_q0_v2_test", TOOL)
terminal_fixture = load_module("_horizon_terminal_fixture_for_closure", TERMINAL_TESTS)


def copy_project_file(root: Path, relative: str) -> None:
    source = PROJECT / relative
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_snapshot(root: Path) -> dict[str, str]:
    result = root / closure.SOURCE_RESULT_ROOT
    return {path.name: sha256(path) for path in sorted(result.iterdir())}


def build_fixture(root: Path, scientific_branch: str) -> tuple[Path, str, bytes]:
    reflected_branch = (
        terminal_fixture.router.BRANCH_REPRICE
        if scientific_branch == "EXACT_REPRICE_Q0_V2"
        else terminal_fixture.router.BRANCH_RETIRE
    )
    paths = terminal_fixture.build_terminal_fixture(root, branch=reflected_branch)
    for name in sorted(closure.UNDECLARED_V1_NAMES):
        (paths["result"] / name).write_bytes(f"synthetic-{name}\n".encode())

    dependencies = {
        closure.ROUTER_PATH,
        closure.ROUTER_SCHEMA_PATH,
        closure.RECEIPT_SCHEMA_PATH,
        closure.TOOL_PATH,
        *terminal_fixture.router.SCHEMA_PATHS.values(),
    }
    for relative in sorted(dependencies):
        copy_project_file(root, relative)

    synthetic_router = closure._load_router(root)
    route = synthetic_router.route(root)
    assert route["branch"] == "CORRECTION_RETRY_ONLY"
    assert route["output_closure"]["failure_class"] == "undeclared-extras"
    assert set(route["output_closure"]["extras"]) == closure.UNDECLARED_V1_NAMES
    expected_promotion = scientific_branch == "EXACT_REPRICE_Q0_V2"
    assert route["consistency"]["promotion_predicates_pass"] is expected_promotion

    receipt_path = root / "operations/evidence/synthetic-horizon-terminal-route.json"
    write_json(receipt_path, route)
    decision_bytes = paths["decision"].read_bytes()
    return receipt_path, sha256(receipt_path), decision_bytes


@pytest.mark.parametrize(
    ("scientific_branch", "verdict", "promotion"),
    [
        (
            "EXACT_REPRICE_Q0_V2",
            "authorize_one_native_horizon_pkd_finite_coder",
            True,
        ),
        (
            "RETIRE_PHYSICAL_HORIZON",
            "retire_endpoint428_physical_horizon_a",
            False,
        ),
    ],
)
def test_closes_exact_namespace_without_changing_science(
    tmp_path: Path, scientific_branch: str, verdict: str, promotion: bool
) -> None:
    route_path, route_sha, decision_bytes = build_fixture(tmp_path, scientific_branch)
    source_before = source_snapshot(tmp_path)
    receipt = closure.salvage(
        project_root=tmp_path,
        terminal_route_receipt=route_path,
        terminal_route_sha256=route_sha,
        execution_mode="synthetic",
    )
    output = tmp_path / closure.RESULT_ROOT
    assert {path.name for path in output.iterdir()} == closure.OUTPUT_NAMES
    assert (output / closure.PRESERVED_DECISION_NAME).read_bytes() == decision_bytes
    assert source_snapshot(tmp_path) == source_before
    assert receipt["routing"]["recomputed_scientific_branch"] == scientific_branch
    assert receipt["decision_preservation"]["source_verdict"] == verdict
    assert receipt["decision_preservation"]["source_promotion_authorized"] is promotion
    assert receipt["decision_preservation"]["scientific_values_modified"] is False
    assert receipt["authority"] == {
        "archive_authority": False,
        "score_credit_bytes": 0,
        "verified_full_1g_score_bytes": None,
        "hutter_result_authority": False,
        "corpus_accessed": False,
        "cmix_invoked": False,
        "analyzer_invoked": False,
        "source_result_mutated": False,
    }


@pytest.mark.parametrize("mutation", ["missing", "additional"])
def test_rejects_source_name_set_drift(tmp_path: Path, mutation: str) -> None:
    route_path, route_sha, _decision = build_fixture(
        tmp_path, "EXACT_REPRICE_Q0_V2"
    )
    result = tmp_path / closure.SOURCE_RESULT_ROOT
    if mutation == "missing":
        (result / "materialize.log").unlink()
    else:
        (result / "undeclared-second-extra.log").write_bytes(b"drift")
    with pytest.raises(closure.ClosureError):
        closure.salvage(
            project_root=tmp_path,
            terminal_route_receipt=route_path,
            terminal_route_sha256=route_sha,
            execution_mode="synthetic",
        )
    assert not (tmp_path / closure.RESULT_ROOT).exists()


@pytest.mark.parametrize("mutation", ["symlink", "directory"])
def test_rejects_nonregular_source_artifact(tmp_path: Path, mutation: str) -> None:
    route_path, route_sha, _decision = build_fixture(
        tmp_path, "RETIRE_PHYSICAL_HORIZON"
    )
    result = tmp_path / closure.SOURCE_RESULT_ROOT
    target = result / "materialize.log"
    target.unlink()
    if mutation == "symlink":
        target.symlink_to(result / "build.json")
    else:
        target.mkdir()
    with pytest.raises(closure.ClosureError):
        closure.salvage(
            project_root=tmp_path,
            terminal_route_receipt=route_path,
            terminal_route_sha256=route_sha,
            execution_mode="synthetic",
        )
    assert not (tmp_path / closure.RESULT_ROOT).exists()


def test_rejects_source_path_replacement_during_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    route_path, _route_sha, _decision = build_fixture(
        tmp_path, "EXACT_REPRICE_Q0_V2"
    )
    router = closure._load_router(tmp_path)
    route = json.loads(route_path.read_text())
    target = tmp_path / closure.SOURCE_RESULT_ROOT / "analysis-a.json"
    original = router.ProjectReader.artifact_snapshot
    replaced = False

    def replace_prior_path(reader: Any, relative: str) -> Any:
        nonlocal replaced
        result = original(reader, relative)
        if relative.endswith("/analysis-b.json") and not replaced:
            replacement = target.with_name("replacement.json")
            replacement.write_bytes(b"{}\n")
            replacement.replace(target)
            replaced = True
        return result

    monkeypatch.setattr(
        router.ProjectReader, "artifact_snapshot", replace_prior_path
    )
    with pytest.raises(router.RouteError, match="pathname changed after hashing"):
        closure._bind_source_namespace(tmp_path, router, route)


def test_rejects_forged_correction_receipt_even_when_rehashed(tmp_path: Path) -> None:
    route_path, _route_sha, _decision = build_fixture(
        tmp_path, "EXACT_REPRICE_Q0_V2"
    )
    value = json.loads(route_path.read_text())
    value["branch_reason"] = "forged correction"
    write_json(route_path, value)
    with pytest.raises(closure.ClosureError, match="differs from pinned router recomputation"):
        closure.salvage(
            project_root=tmp_path,
            terminal_route_receipt=route_path,
            terminal_route_sha256=sha256(route_path),
            execution_mode="synthetic",
        )
    assert not (tmp_path / closure.RESULT_ROOT).exists()


def test_no_clobber_successor_root(tmp_path: Path) -> None:
    route_path, route_sha, _decision = build_fixture(
        tmp_path, "RETIRE_PHYSICAL_HORIZON"
    )
    output = tmp_path / closure.RESULT_ROOT
    output.mkdir(parents=True)
    sentinel = output / "sentinel"
    sentinel.write_bytes(b"preserve")
    with pytest.raises(closure.ClosureError, match="already exists"):
        closure.salvage(
            project_root=tmp_path,
            terminal_route_receipt=route_path,
            terminal_route_sha256=route_sha,
            execution_mode="synthetic",
        )
    assert sentinel.read_bytes() == b"preserve"


def test_tool_has_no_process_launch_surface() -> None:
    source = TOOL.read_text()
    assert "import subprocess" not in source
    assert "Popen(" not in source
    assert "subprocess.run(" not in source
    assert "os.system(" not in source


def test_canonical_contract_validator_rehashes_complete_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    route_path, route_sha, _decision = build_fixture(
        tmp_path, "EXACT_REPRICE_Q0_V2"
    )
    closure.salvage(
        project_root=tmp_path,
        terminal_route_receipt=route_path,
        terminal_route_sha256=route_sha,
        execution_mode="synthetic",
    )
    receipt_path = tmp_path / closure.RESULT_ROOT / closure.RECEIPT_NAME
    contracts = terminal_fixture.research_contracts
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    validation = contracts.validate_artifact(receipt_path, verify_files=True)
    assert validation["valid"] is True
    assert validation["filesVerified"] is True
    assert validation["scoreCreditBytes"] == 0
