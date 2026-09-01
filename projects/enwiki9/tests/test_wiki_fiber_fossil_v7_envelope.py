from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from unittest import mock


PROJECT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT / "tools/wiki_fiber_fossil_endpoint428_opening1m_q0_v7.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("_fiber_v7_runner_test", RUNNER)
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


def test_exact_128_bit_token_name():
    module = load_runner()
    with mock.patch.object(module.secrets, "token_hex", return_value="ab" * 16) as call:
        name = module.new_owned_cgroup_name()
    call.assert_called_once_with(16)
    assert module.valid_owned_cgroup_name(name)
    assert not module.valid_owned_cgroup_name(name.replace("ab" * 16, "ab" * 8))


def test_outer_finalizer_is_authoritative_and_manifest_exact():
    module = load_runner()
    with tempfile.TemporaryDirectory(prefix="fiber-v7-finalizer-") as temporary:
        root = Path(temporary)
        cgroup = populate_provisional_result(module, root)
        with mock.patch.object(module, "RESULT", root):
            module.finalize_authoritative_result(cgroup)
        assert {path.name for path in root.iterdir()} == module.DECLARED_OUTPUT_NAMES
        receipt = json.loads((root / module.FINAL_RECEIPT).read_text())
        decision = json.loads((root / module.FINAL_DECISION).read_text())
        assert receipt["authoritative"] is True
        assert receipt["provisional_only"] is False
        assert receipt["measurements"]["authoritativeOuterFinalizationPass"] is True
        assert receipt["measurements"]["completeOutputManifestPass"] is True
        assert receipt["authoritative_cgroup"]["cleanup"]["no_residue"] is True
        assert decision["authoritative"] is True
        assert decision["no_extra_files_pass"] is True


def test_outer_finalizer_rejects_extra_output():
    module = load_runner()
    with tempfile.TemporaryDirectory(prefix="fiber-v7-extra-") as temporary:
        root = Path(temporary)
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


def test_guarded_probe_records_actual_denial_before_corpus():
    module = load_runner()
    with tempfile.TemporaryDirectory(prefix="fiber-v7-probe-") as temporary:
        root = Path(temporary)
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
    test_guarded_probe_records_actual_denial_before_corpus()
