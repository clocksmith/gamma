"""Candidate kinds and entrypoints are checked before executing any candidate."""
from __future__ import annotations
import ast
import json
from pathlib import Path

from gamma_enwiki9.evidence.artifacts import fingerprint
from gamma_enwiki9.types import CandidateKind


def validate_candidate(root: Path, specification: dict) -> dict:
    kind = CandidateKind(specification["kind"])
    entry = specification["entrypoint"]
    if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
        raise ValueError("explicit candidate entrypoint required")
    records = specification.get("sources")
    if not isinstance(records, list) or not records:
        raise ValueError("explicit candidate source manifest required")
    paths = set()
    for record in records:
        actual = fingerprint(root / record["path"], root)
        if actual != record or record["path"] in paths:
            raise ValueError("candidate source identity differs or repeats")
        paths.add(record["path"])
    if entry["path"] not in paths:
        raise ValueError("entrypoint missing from candidate source manifest")
    if kind == CandidateKind.STANDALONE_CODEC:
        if entry.get("compress") != "compress" or entry.get("decompress") != "decompress":
            raise ValueError("standalone codec requires compress and decompress entrypoints")
        source = root / entry["path"]
        if source.suffix == ".py" and not {"compress", "decompress"}.issubset(declared_names(source)):
            raise ValueError("standalone codec entrypoints are not declared in source")
    elif kind == CandidateKind.EXPERIMENT_RECIPE:
        codec = specification.get("codec")
        if not isinstance(codec, dict) or not codec.get("candidate_id") or not codec.get("revision") or not entry.get("callable"):
            raise ValueError("experiment recipe must reference a codec and callable")
    elif kind == CandidateKind.ANALYSIS_ONLY:
        if not entry.get("callable"):
            raise ValueError("analysis entrypoint callable required")
    elif not specification.get("upstream") or not specification.get("transformations"):
        raise ValueError("external adapter requires upstream provenance and transformations")
    return specification


def declared_names(source: Path) -> set[str]:
    tree = ast.parse(source.read_bytes())
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.ImportFrom, ast.Import)):
            names.update(a.asname or a.name for a in node.names)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def codec_entrypoint(root: Path) -> Path:
    manifest = root / "candidate.json"
    if manifest.is_file():
        spec = validate_candidate(root, json.loads(manifest.read_bytes()))
        if spec["kind"] != CandidateKind.STANDALONE_CODEC.value:
            raise ValueError(f"candidate kind {spec['kind']} cannot run through the codec driver")
        return root / spec["entrypoint"]["path"]
    # Historical candidates have no new metadata written into measured sources.
    # Limit legacy loading to a statically declared codec interface; never execute
    # an experiment merely to discover that it lacks compress/decompress.
    source = root / "program.py"
    functions = declared_names(source)
    if not {"compress", "decompress"}.issubset(functions):
        raise ValueError("legacy candidate has no declared codec interface; supply an explicit candidate kind")
    return source


def scaffold_spec(root: Path, *, kind: str, entrypoint: str = "program.py", codec=None,
                  upstream=None, transformations=None) -> dict:
    entry = {"path": entrypoint}
    if kind == CandidateKind.STANDALONE_CODEC.value:
        entry.update(compress="compress", decompress="decompress")
    else:
        entry["callable"] = "main"
    value = {"schema": "gamma.enwiki9.candidate-entrypoint.v1", "kind": kind,
             "entrypoint": entry, "sources": [fingerprint(p, root) for p in sorted(root.rglob("*"))
                if p.is_file() and p.name not in {"meta.json", "candidate.json"}
                and not any(part.startswith(".") or part == "__pycache__" for part in p.relative_to(root).parts)]}
    if codec is not None:
        value["codec"] = codec
    if upstream is not None:
        value["upstream"] = upstream
        value["transformations"] = transformations
    return validate_candidate(root, value)
