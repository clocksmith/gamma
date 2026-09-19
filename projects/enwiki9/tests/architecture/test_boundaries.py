"""Enforce import directions and one maintained source per migrated component."""
import ast
from pathlib import Path
import json

from gamma_enwiki9.reporting import projection

PROJECT = Path(__file__).resolve().parents[2]
PACKAGE = PROJECT / "src/gamma_enwiki9"


def imports(path):
    for node in ast.walk(ast.parse(path.read_bytes())):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            yield node.module or ""


def test_services_do_not_import_the_lab_or_recipes():
    for component in ("execution", "evidence", "packaging", "reporting"):
        for path in (PACKAGE / component).glob("*.py"):
            for dependency in imports(path):
                assert "enwiki9_lab" not in dependency, (path, dependency)
                assert "gamma_enwiki9.research" not in dependency, (path, dependency)
                assert "gamma_enwiki9.adapters" not in dependency, (path, dependency)
                if component == "evidence":
                    assert not any(x in dependency for x in ("experiment_driver", "gamma_enwiki9.execution", "gamma_enwiki9.reporting")), (path, dependency)


def test_pure_codec_has_no_operational_or_observer_imports():
    assert set(imports(PROJECT / "lib/coders/raw_reverse_bz2.py")) <= {"bz2", "hashlib", "struct"}


def test_record_projection_is_deterministic_and_does_not_observe_host(tmp_path):
    (tmp_path / "objective.json").write_text(json.dumps({"score": {"targetBytes": 90000000}, "corpus": {"bytes": 1000000000}}))
    build = lambda: projection.build(tmp_path, catalogue_builder=lambda root: [], objective_path="objective.json")
    assert build() == build()
    assert build()["generated_at"] is None and build()["host"] is None


def test_legacy_candidate_snapshots_have_explicit_maintenance_roles():
    roles = json.loads((PROJECT / "docs/architecture/source_roles.json").read_bytes())
    assert roles["canonical_namespace"] == "gamma_enwiki9"
    assert all(r["role"] in {"maintained", "compatibility_entrypoint", "frozen_snapshot"} for r in roles["files"])
    paths = [r["path"] for r in roles["files"]]
    assert len(paths) == len(set(paths))
    for row in roles["files"]:
        assert (PROJECT / row["path"]).exists()
