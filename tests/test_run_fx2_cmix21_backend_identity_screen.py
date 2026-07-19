import importlib.util
import pathlib
import tempfile


MODULE_PATH = (
    pathlib.Path(__file__).parents[1]
    / "projects"
    / "enwiki9"
    / "tools"
    / "run_fx2_cmix21_backend_identity_screen.py"
)
SPEC = importlib.util.spec_from_file_location("backend_identity_screen", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_summarize_runs_reports_identity_and_runtime_reduction() -> None:
    runs = []
    for role, elapsed in (
        ("reference", 10.0),
        ("candidate", 8.0),
        ("candidate", 9.0),
        ("reference", 11.0),
    ):
        runs.append(
            {
                "role": role,
                "clean_guard": True,
                "archive": {"bytes": 7, "sha256": "same"},
                "guard_result": {"elapsed_s": elapsed},
            }
        )
    result = MODULE.summarize_runs(runs)
    assert result["all_guards_clean"]
    assert result["archive_identity"]
    assert result["role_archive_determinism"] == {
        "reference": True,
        "candidate": True,
    }
    assert result["role_archive_bytes"] == {"reference": 7, "candidate": 7}
    assert result["reference_median_elapsed_s"] == 10.5
    assert result["candidate_median_elapsed_s"] == 8.5
    assert result["candidate_runtime_reduction_fraction"] == (
        1.0 - 8.5 / 10.5
    )


def test_artifact_hashes_content() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "artifact"
        path.write_bytes(b"abc")
        result = MODULE.artifact(path)
    assert result["bytes"] == 3
    assert result["sha256"] == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_build_backend_command_applies_requested_cpu_affinity() -> None:
    command = MODULE.build_backend_command(
        binary=pathlib.Path("backend"),
        dictionary=pathlib.Path("english.dic"),
        input_path=pathlib.Path("input.bin"),
        archive=pathlib.Path("archive.bin"),
        cpu_list="0,1,2,3",
    )
    assert command[:3] == ["taskset", "--cpu-list", "0,1,2,3"]
    assert command[4] == "-c"


def test_build_backend_command_is_unchanged_without_affinity() -> None:
    command = MODULE.build_backend_command(
        binary=pathlib.Path("backend"),
        dictionary=pathlib.Path("english.dic"),
        input_path=pathlib.Path("input.bin"),
        archive=pathlib.Path("archive.bin"),
        cpu_list=None,
    )
    assert command[1] == "-c"
    assert "taskset" not in command


def test_pareto_evaluation_credits_deterministic_smaller_archive() -> None:
    metrics = {
        "role_archive_determinism": {"reference": True, "candidate": True},
        "role_archive_bytes": {"reference": 44_958, "candidate": 44_931},
        "candidate_runtime_reduction_fraction": -0.043,
    }
    result = MODULE.evaluate_pareto_candidate(
        metrics,
        scope_bytes=250_000,
        baseline_counted_forecast_bytes=109_408_345,
        calibration_factor=66.955334,
        target_score_bytes=109_500_000,
        minimum_runtime_reduction_fraction=0.0,
    )
    assert result["candidate_archive_savings_bytes"] == 27
    assert result["candidate_provisional_counted_forecast_bytes"] == 109_336_034
    assert result["target_margin_bytes"] == 163_966
    assert result["score_projection_pass"]
    assert not result["runtime_screen_pass"]
    assert result["verdict"] == "score_projection_passed_runtime_screen_failed"
    assert not result["larger_prize_gate_authorized"]


def test_pareto_evaluation_rejects_same_role_nondeterminism() -> None:
    metrics = {
        "role_archive_determinism": {"reference": True, "candidate": False},
        "role_archive_bytes": {"reference": 44_958, "candidate": None},
        "candidate_runtime_reduction_fraction": 0.2,
    }
    result = MODULE.evaluate_pareto_candidate(
        metrics,
        scope_bytes=250_000,
        baseline_counted_forecast_bytes=109_408_345,
        calibration_factor=66.955334,
        target_score_bytes=109_500_000,
        minimum_runtime_reduction_fraction=0.0,
    )
    assert result["verdict"] == "reject_nondeterministic_role_archive"
    assert not result["larger_prize_gate_authorized"]


def test_pareto_evaluation_distinguishes_target_margin_from_score_gain() -> None:
    metrics = {
        "role_archive_determinism": {"reference": True, "candidate": True},
        "role_archive_bytes": {"reference": 44_958, "candidate": 44_979},
        "candidate_runtime_reduction_fraction": 0.061,
    }
    result = MODULE.evaluate_pareto_candidate(
        metrics,
        scope_bytes=250_000,
        baseline_counted_forecast_bytes=109_408_345,
        calibration_factor=66.955334,
        target_score_bytes=109_500_000,
        minimum_runtime_reduction_fraction=0.10,
    )
    assert result["candidate_archive_delta_bytes"] == 21
    assert result["score_projection_pass"]
    assert not result["runtime_screen_pass"]
    assert result["verdict"] == "target_projection_passed_runtime_threshold_missed"
