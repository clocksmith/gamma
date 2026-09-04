from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = (
    PROJECT_ROOT / "tools/nncp_libnc_profile_initial_fixture_65536_q0.py"
)
V2_TOOL_PATH = (
    PROJECT_ROOT / "tools/nncp_libnc_profile_initial_fixture_65536_q0_v2.py"
)
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location("nncp_initial_fixture_q0", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_self_test_exercises_patch_and_container_contract() -> None:
    completed = subprocess.run(
        [sys.executable, str(TOOL_PATH), "--self-test"],
        cwd=PROJECT_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout
    assert completed.stdout == "NNCP_PROFILE_INITIAL_FIXTURE_SELFTEST_OK\n"

    corrected = subprocess.run(
        [sys.executable, str(V2_TOOL_PATH), "--self-test"],
        cwd=PROJECT_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert corrected.returncode == 0, corrected.stdout
    assert corrected.stdout == completed.stdout


def test_capture_is_pre_forward_and_activation_free() -> None:
    source = (
        "static FILE *teacher_trace_file;\n"
        "    s->model_class->model_reset(s);\n    \n    /* normal batches */"
    )
    patched = MODULE.patch_teacher(source)
    call = patched.index("gamma_capture_initial_fixture(s")
    assert call < patched.index("/* normal batches */", call)
    assert "train_h" not in MODULE.CAPTURE_HELPER
    assert "model_eval_gradient" not in MODULE.CAPTURE_HELPER
    assert "model_update" not in MODULE.CAPTURE_HELPER


def test_frozen_geometry_matches_integrated_population() -> None:
    assert MODULE.SYMBOLS == 65_536
    assert MODULE.SYMBOL_BYTES == 131_072
    assert MODULE.STREAMS == 32
    assert MODULE.STATES == 64
    assert MODULE.STREAM_STRIDE == 2_048
    assert MODULE.PARAMETERS == 246
    assert MODULE.OPTIMIZER_TENSORS == 491
    assert MODULE.STATE_TENSORS == 22
    assert len(MODULE.expected_parameter_layout()) == MODULE.PARAMETERS


def test_tool_is_declared_as_teacher_launcher() -> None:
    inventory = (PROJECT_ROOT / "docs/tooling_inventory.md").read_text()
    assert TOOL_PATH.name in inventory
    assert V2_TOOL_PATH.name in inventory
    assert "exits before the first forward" in inventory
