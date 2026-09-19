from pathlib import Path
import pytest
from gamma_enwiki9.evidence.source_closure import resolve_closure


def put(root, path, value=""):
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value)
    return p


def test_packages_relative_submodules_and_lib_are_closed(tmp_path):
    entry = put(tmp_path, "entry.py", "from package import child\nimport lib.codec\n")
    put(tmp_path, "package/__init__.py")
    put(tmp_path, "package/child.py", "from . import sibling\nfrom .deep.module import value\n")
    put(tmp_path, "package/sibling.py")
    put(tmp_path, "package/deep/__init__.py")
    put(tmp_path, "package/deep/module.py", "from ..sibling import *\nvalue = 1\n")
    put(tmp_path, "lib/codec.py", "import bz2\n")
    result = resolve_closure([entry], root=tmp_path, import_roots=[tmp_path])
    assert result.complete
    assert {r["path"] for r in result.sources} == {
        "entry.py", "package/__init__.py", "package/child.py", "package/sibling.py",
        "package/deep/__init__.py", "package/deep/module.py", "lib/codec.py"}


def test_schema_versions_are_explicit_not_swept(tmp_path):
    entry = put(tmp_path, "research_contracts.py", "import json\n")
    put(tmp_path, "contracts/v1/unrelated.json", "{}")
    schema = put(tmp_path, "contracts/v3/required.json", "{}")
    result = resolve_closure([entry], root=tmp_path, import_roots=[tmp_path], schemas=[schema])
    assert [r["path"] for r in result.schemas] == ["contracts/v3/required.json"]
    assert len(result.sources) == 1


def test_missing_local_and_dynamic_requirements_are_visible(tmp_path):
    entry = put(tmp_path, "entry.py", "import package.missing\nimport importlib\nimportlib.import_module('plugin')\n")
    put(tmp_path, "package/__init__.py")
    report = resolve_closure([entry], root=tmp_path, import_roots=[tmp_path])
    assert not report.complete
    assert report.unresolved_local_imports == ("entry.py: package.missing",)
    assert report.dynamic_loading_requirements == ("entry.py:3:importlib.import_module",)
    put(tmp_path, "package/missing.py")
    plugin = put(tmp_path, "plugin.py", "import json\n")
    asset = put(tmp_path, "runtime/table.bin", "asset")
    report = resolve_closure([entry], root=tmp_path, import_roots=[tmp_path],
        dynamic_dependencies={"entry.py:3:importlib.import_module": [plugin, asset]})
    assert report.complete
    assert "plugin.py" in {r["path"] for r in report.sources}
    assert report.non_source_dependencies[0]["path"] == "runtime/table.bin"


def test_missing_from_submodule_is_not_mistaken_for_attribute(tmp_path):
    entry = put(tmp_path, "entry.py", "from package import missing\n")
    put(tmp_path, "package/__init__.py")
    report = resolve_closure([entry], root=tmp_path, import_roots=[tmp_path])
    assert report.unresolved_local_imports == ("entry.py: package.missing",)


def test_source_escape_is_rejected(tmp_path):
    outside = put(tmp_path, "outside.py")
    root = tmp_path / "root"
    root.mkdir()
    (root / "entry.py").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        resolve_closure([root / "entry.py"], root=root, import_roots=[root])
