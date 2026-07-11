"""Guardrails for Gamma's repository-root ownership contract."""

from __future__ import annotations

import inspect
from pathlib import Path

from src.benchmarks.mind_meld_benchmark import MindMeldBenchmark


REPO_ROOT = Path(__file__).resolve().parent.parent
MOVED_ROOT_UTILITIES = {
    "analyze_existing.py",
    "extract_attention.py",
    "extract_probabilities.py",
    "generate_data.py",
    "generate_texture_pack.py",
    "generate_tree_data.py",
}


def test_specialized_files_stay_out_of_repository_root() -> None:
    root_files = {path.name for path in REPO_ROOT.iterdir() if path.is_file()}
    assert root_files.isdisjoint(MOVED_ROOT_UTILITIES)
    assert not list(REPO_ROOT.glob("requirements-*.txt"))


def test_requirement_includes_resolve_relative_to_manifest() -> None:
    manifests = [
        REPO_ROOT / "requirements.txt",
        *sorted((REPO_ROOT / "requirements").glob("*.txt")),
    ]
    missing: list[str] = []

    for manifest in manifests:
        for raw_line in manifest.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line.startswith("-r "):
                continue
            include = line.removeprefix("-r ").strip()
            if not (manifest.parent / include).is_file():
                missing.append(f"{manifest.relative_to(REPO_ROOT)} -> {include}")

    assert not missing, f"Missing requirement includes: {missing}"


def test_benchmark_report_defaults_to_ignored_reports_directory() -> None:
    signature = inspect.signature(MindMeldBenchmark.generate_report)
    assert (
        signature.parameters["output_path"].default == "reports/benchmark_report.html"
    )


def test_benchmark_report_creates_output_directory(tmp_path: Path) -> None:
    benchmark = MindMeldBenchmark(verbose=False)
    benchmark.results.append(object())
    benchmark._build_html_report = lambda: "<html>report</html>"
    output_path = tmp_path / "nested" / "benchmark.html"

    benchmark.generate_report(str(output_path))

    assert output_path.read_text(encoding="utf-8") == "<html>report</html>"
