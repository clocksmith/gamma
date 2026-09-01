from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from unittest import mock


PROJECT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT / "tools/wiki_fiber_fossil_endpoint428_opening1m_q0_v8.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("_fiber_v8_runner_test", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_cgroup_report(module, binding):
    events = {"low": 0, "high": 0, "max": 0, "oom": 0, "oom_kill": 0}
    return {
        "delegated_parent": {
            "path": str(module.DELEGATED_CGROUP_PARENT),
            "inode": module.DELEGATED_CGROUP_PARENT_INODE,
            "uid": module.DELEGATED_CGROUP_PARENT_UID,
            "gid": module.DELEGATED_CGROUP_PARENT_GID,
        },
        "owned_path": binding["path"],
        "owned_name": Path(binding["path"]).name,
        "owned_inode": binding["inode"],
        "owned_token_bits": 128,
        "memory_max_bytes": module.HARD_MEMORY_LIMIT_BYTES,
        "memory_swap_max_bytes": 0,
        "joined_before_exec": True,
        "memory_peak_bytes": 16 << 20,
        "memory_events_before": events,
        "memory_events_after": events,
        "memory_events_delta": {key: 0 for key in events},
        "child_exit": {"returncode": 0, "exited": True, "success": True},
        "cleanup": {
            "empty_before_remove": True,
            "same_inode_before_remove": True,
            "removed": True,
            "no_residue": True,
        },
        "authoritative_envelope_complete": True,
    }


def populate_provisional_result(module, root: Path):
    token = "0" * 32
    name = f"{module.OWNED_CGROUP_PREFIX}123-{token}.scope"
    binding = {
        "path": str(module.DELEGATED_CGROUP_PARENT / name),
        "inode": 12345,
        "delegated_parent": str(module.DELEGATED_CGROUP_PARENT),
        "memory_max_bytes": module.HARD_MEMORY_LIMIT_BYTES,
        "cleanup_pending": True,
    }
    provisional = {
        "candidate_id": module.CANDIDATE_ID,
        "provisional_only": True,
        "authoritative": False,
        "outer_finalization_required": True,
        "measurements": {
            "hardMemoryEnvelopePass": False,
            "activeHorizonAccessDeniedPass": True,
            "ownedCgroupLifecyclePass": False,
        },
        "execution_envelope": {"owned_cgroup": binding},
        "scientific_promotion_pass_provisional": True,
    }
    probe = {
        "candidate_id": module.CANDIDATE_ID,
        "denied_before_corpus": True,
        "active_horizon_artifact_accessed": False,
        "corpus_accessed": False,
        "cgroup": binding,
    }
    pre_final = module.DECLARED_OUTPUT_NAMES - {
        module.FINAL_RECEIPT, module.FINAL_DECISION
    }
    for name_to_create in pre_final:
        (root / name_to_create).write_bytes(b"synthetic\n")
    (root / module.PROVISIONAL_RECEIPT).write_text(json.dumps(provisional))
    (root / module.HORIZON_PROBE).write_text(json.dumps(probe))
    return valid_cgroup_report(module, binding)


def authority_pass_files(root: Path):
    matches = []
    for path in root.iterdir():
        if not path.is_file() or path.suffix != ".json":
            continue
        try:
            value = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if value.get("authoritative") is True and value.get("status") == "passed":
            matches.append(path.name)
    return matches


def result_root(temporary: str) -> Path:
    root = Path(temporary) / "canonical-result"
    root.mkdir()
    return root


def test_exact_128_bit_token_name():
    module = load_runner()
    with mock.patch.object(module.secrets, "token_hex", return_value="ab" * 16) as call:
        name = module.new_owned_cgroup_name()
    call.assert_called_once_with(16)
    assert module.valid_owned_cgroup_name(name)
    assert not module.valid_owned_cgroup_name(name.replace("ab" * 16, "ab" * 8))


def test_outer_finalizer_is_authoritative_and_manifest_exact():
    module = load_runner()
    with tempfile.TemporaryDirectory(prefix="fiber-v8-finalizer-") as temporary:
        root = result_root(temporary)
        cgroup = populate_provisional_result(module, root)
        stages = []

        def observe(stage):
            stages.append(stage)
            if stage == "before_publish":
                assert not (root / module.FINAL_RECEIPT).exists()
                assert not (root / module.FINAL_DECISION).exists()
            elif stage == "after_receipt_publish":
                receipt = json.loads((root / module.FINAL_RECEIPT).read_text())
                assert receipt["authoritative"] is False
                assert receipt["authority_requires_terminal_decision"] is True
                assert not (root / module.FINAL_DECISION).exists()

        with mock.patch.object(module, "RESULT", root):
            module.finalize_authoritative_result(cgroup, observe)
        assert {path.name for path in root.iterdir()} == module.DECLARED_OUTPUT_NAMES
        receipt = json.loads((root / module.FINAL_RECEIPT).read_text())
        decision = json.loads((root / module.FINAL_DECISION).read_text())
        assert stages == ["before_publish", "after_receipt_publish", "after_decision_publish"]
        assert receipt["authoritative"] is False
        assert receipt["provisional_only"] is False
        assert "authoritativeOuterFinalizationPass" not in receipt["measurements"]
        assert "completeOutputManifestPass" not in receipt["measurements"]
        assert receipt["authoritative_cgroup"]["cleanup"]["no_residue"] is True
        assert decision["authoritative"] is True
        assert decision["sole_authority"] is True
        assert decision["measurements"]["authoritativeOuterFinalizationPass"] is True
        assert decision["measurements"]["completeOutputManifestPass"] is True
        manifest = decision["complete_output_manifest"]
        assert manifest["declared_artifact_count"] == len(module.DECLARED_OUTPUT_NAMES)
        assert manifest["bound_artifact_count"] == len(module.DECLARED_OUTPUT_NAMES) - 1
        assert len(manifest["entries"]) == len(module.DECLARED_OUTPUT_NAMES) - 1
        assert all(set(row) == {"path", "bytes", "sha256"} for row in manifest["entries"])
        assert len({row["path"] for row in manifest["entries"]}) == len(manifest["entries"])
        assert manifest["decision_self_exclusion"]["path"].endswith("/decision.json")
        receipt_entry = next(
            row for row in manifest["entries"] if row["path"].endswith("/receipt.json")
        )
        assert receipt_entry["bytes"] == (root / module.FINAL_RECEIPT).stat().st_size
        assert receipt_entry["sha256"] == module.sha256(root / module.FINAL_RECEIPT)
        assert not list(root.parent.glob(f".{module.CANDIDATE_ID}.*.tmp"))


def test_outer_finalizer_rejects_extra_output():
    module = load_runner()
    with tempfile.TemporaryDirectory(prefix="fiber-v8-extra-") as temporary:
        root = result_root(temporary)
        cgroup = populate_provisional_result(module, root)
        (root / "undeclared.bin").write_bytes(b"no")
        with mock.patch.object(module, "RESULT", root):
            try:
                module.finalize_authoritative_result(cgroup)
            except RuntimeError as error:
                assert "exact output manifest mismatch" in str(error)
            else:
                raise AssertionError("undeclared output was accepted")
        assert not (root / module.FINAL_RECEIPT).exists()
        assert not (root / module.FINAL_DECISION).exists()


def assert_terminal_failure_rolls_back(mutation):
    module = load_runner()
    with tempfile.TemporaryDirectory(prefix="fiber-v8-rollback-") as temporary:
        root = result_root(temporary)
        cgroup = populate_provisional_result(module, root)

        def inject(stage):
            if stage == "after_decision_publish":
                mutation(module, root)

        with mock.patch.object(module, "RESULT", root):
            try:
                module.finalize_authoritative_result(cgroup, inject)
            except RuntimeError:
                pass
            else:
                raise AssertionError("terminal manifest failure was accepted")
        assert not (root / module.FINAL_RECEIPT).exists()
        assert not (root / module.FINAL_DECISION).exists()
        assert authority_pass_files(root) == []
        assert not list(root.parent.glob(f".{module.CANDIDATE_ID}.*.tmp"))


def test_terminal_extra_file_failure_rolls_back_authority():
    assert_terminal_failure_rolls_back(
        lambda _module, root: (root / "injected-extra.bin").write_bytes(b"extra")
    )


def test_terminal_nonregular_failure_rolls_back_authority():
    def inject(module, root):
        target = root / "payload-P.bin"
        target.unlink()
        target.mkdir()

    assert_terminal_failure_rolls_back(inject)


def test_terminal_hash_drift_failure_rolls_back_authority():
    assert_terminal_failure_rolls_back(
        lambda _module, root: (root / "payload-P.bin").write_bytes(b"drift")
    )


def test_guarded_probe_records_actual_denial_before_corpus():
    module = load_runner()
    with tempfile.TemporaryDirectory(prefix="fiber-v8-probe-") as temporary:
        root = result_root(temporary)
        binding = {"synthetic": True}
        with mock.patch.object(module, "RESULT", root), mock.patch.object(
            module, "owned_cgroup_binding", return_value=binding
        ):
            module.install_horizon_access_guard()
            probe = module.perform_guarded_horizon_probe()
        assert probe["denied_before_corpus"] is True
        assert probe["active_horizon_artifact_accessed"] is False
        assert probe["corpus_accessed"] is False
        assert probe["cgroup"] == binding
        assert (root / module.HORIZON_PROBE).is_file()


if __name__ == "__main__":
    test_exact_128_bit_token_name()
    test_outer_finalizer_is_authoritative_and_manifest_exact()
    test_outer_finalizer_rejects_extra_output()
    test_terminal_extra_file_failure_rolls_back_authority()
    test_terminal_nonregular_failure_rolls_back_authority()
    test_terminal_hash_drift_failure_rolls_back_authority()
    test_guarded_probe_records_actual_denial_before_corpus()
