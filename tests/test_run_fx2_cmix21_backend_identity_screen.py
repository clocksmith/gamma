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
