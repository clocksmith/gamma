"""Static Python closure under declared import roots, without importing code.

Completeness is relative to the declared roots, external modules and dynamic
requirements. It is not proof against arbitrary runtime asset access or exec.
"""
from __future__ import annotations

import ast
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Iterable

from .artifacts import fingerprint


@dataclass(frozen=True)
class ClosureReport:
    sources: tuple[dict, ...]
    non_source_dependencies: tuple[dict, ...]
    unresolved_local_imports: tuple[str, ...]
    dynamic_loading_requirements: tuple[str, ...]
    schemas: tuple[dict, ...]
    undeclared_external_imports: tuple[str, ...]
    complete: bool
    basis: str = "static imports plus explicit runtime declarations; no arbitrary-code completeness claim"

    def to_dict(self):
        return asdict(self)


def resolve_closure(entries: Iterable[Path], *, root: Path,
                    import_roots: Iterable[Path], schemas: Iterable[Path] = (),
                    assets: Iterable[Path] = (), external_modules: Iterable[str] = (),
                    dynamic_dependencies: dict[str, Iterable[Path]] | None = None,
                    package_aliases: dict[str, Path] | None = None) -> ClosureReport:
    root = root.resolve()
    roots = tuple(Path(p).resolve() for p in import_roots)
    aliases = {k: v.resolve() for k, v in (package_aliases or {}).items()}
    if not roots or any(not p.is_relative_to(root) for p in (*roots, *aliases.values())):
        raise ValueError("import roots and aliases must be inside the declared root")
    externals = set(external_modules) | set(sys.stdlib_module_names)
    declarations = dynamic_dependencies or {}
    source_set: set[Path] = set()
    source_records: dict[Path, dict] = {}
    unresolved, dynamic, external = set(), set(), set()
    pending = list(entries)

    def checked(path):
        path = Path(path)
        if not path.is_absolute():
            path = root / path
        fingerprint(path, root)  # Reject symlinks, escapes and non-files.
        return path

    def module_bases(module):
        bases = []
        for alias, base in aliases.items():
            if module == alias or module.startswith(alias + "."):
                tail = module[len(alias):].lstrip(".")
                bases.append(base.joinpath(*tail.split(".")) if tail else base)
        bases.extend(base.joinpath(*module.split(".")) for base in roots)
        return bases

    def module_paths(module):
        if not module:
            return []
        bases = module_bases(module)
        for base in bases:
            selected = base / "__init__.py" if base.is_dir() else base.with_suffix(".py")
            if selected.is_file():
                return [selected]
            # Namespace packages contain no initializer but their children resolve.
            if base.is_dir():
                return []
        return []

    def is_local(module):
        head = module.split(".")[0]
        return any(module == a or module.startswith(a + ".") for a in aliases) or any(
            (base / head).exists() or (base / (head + ".py")).exists() for base in roots)

    def resolve_import(module, source, *, required=True):
        found = module_paths(module)
        pending.extend(found)
        if not found and required:
            if is_local(module):
                # Importing a namespace itself is valid.
                if not any(base.is_dir() for base in module_bases(module)):
                    unresolved.add(f"{source.relative_to(root)}: {module}")
            elif module.split(".")[0] not in externals:
                external.add(module)
        return found

    def package_for(path):
        # Select the most specific import root; package initializers are sources too.
        matches = [base for base in roots if path.is_relative_to(base)]
        if not matches:
            raise ValueError(f"source is outside declared import roots: {path}")
        base = max(matches, key=lambda p: len(p.parts))
        return list(path.relative_to(base).parts[:-1])

    while pending:
        path = checked(pending.pop())
        if path in source_set:
            continue
        if path.suffix != ".py":
            raise ValueError(f"source dependency is not Python: {path}")
        package = package_for(path)
        source_set.add(path)
        # Preserve initialization along every local package chain.
        for parent in path.parents:
            if parent == root or parent in roots:
                break
            if (parent / "__init__.py").is_file():
                pending.append(parent / "__init__.py")
        reference = fingerprint(path, root)
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != reference["sha256"]:
            raise ValueError(f"source changed during closure analysis: {path}")
        source_records[path] = reference
        tree = ast.parse(raw, filename=str(path))
        names = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names[alias.asname or alias.name.split(".")[0]] = alias.name if alias.asname else alias.name.split(".")[0]
                    resolve_import(alias.name, path)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    package = list(path.parent.relative_to(root).parts)
                    if node.level > len(package):
                        unresolved.add(f"{path.relative_to(root)}: relative import beyond package")
                        continue
                    parts = package[:len(package) - node.level + 1]
                    module = ".".join(parts + ([node.module] if node.module else []))
                else:
                    module = node.module or ""
                resolve_import(module, path)
                for alias in node.names:
                    qualified = module + "." + alias.name
                    names[alias.asname or alias.name] = qualified
                    if alias.name != "*":
                        found = resolve_import(qualified, path, required=False)
                        # A from-import can name an attribute. Verify simple names
                        # statically where possible; unresolved stars remain explicit.
                        bases = module_paths(module)
                        if not found and is_local(module):
                            exports = set()
                            uncertain = False
                            for base in bases:
                                parsed = ast.parse(base.read_text(encoding="utf-8"))
                                for statement in parsed.body:
                                    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                                        exports.add(statement.name)
                                        uncertain |= statement.name == "__getattr__"
                                    elif isinstance(statement, ast.Assign):
                                        exports.update(t.id for t in statement.targets if isinstance(t, ast.Name))
                                    elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                                        exports.add(statement.target.id)
                                    elif isinstance(statement, (ast.Import, ast.ImportFrom)):
                                        exports.update(a.asname or a.name.split(".")[0] for a in statement.names)
                                    elif isinstance(statement, (ast.If, ast.Try)):
                                        uncertain = True
                            if alias.name not in exports and not uncertain:
                                unresolved.add(f"{path.relative_to(root)}: {qualified}")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            expression = ast.unparse(node.func)
            head, _, tail = expression.partition(".")
            qualified = names.get(head, head) + ("." + tail if tail else "")
            if qualified in {"__import__", "exec", "eval", "importlib.import_module",
                             "importlib.util.spec_from_file_location", "ctypes.CDLL", "ctypes.PyDLL"}:
                key = f"{path.relative_to(root).as_posix()}:{node.lineno}:{qualified}"
                if key not in declarations:
                    dynamic.add(key)
                else:
                    pending.extend(p for p in declarations[key] if Path(p).suffix == ".py")
    declared_assets = set(map(Path, assets))
    for paths in declarations.values():
        declared_assets.update(Path(p) for p in paths if Path(p).suffix != ".py")
    records = lambda paths: tuple(fingerprint(checked(p), root) for p in sorted(set(paths)))
    resolved_sources = records(source_set)
    if any(row != source_records[root / row["path"]] for row in resolved_sources):
        raise ValueError("source changed during closure analysis")
    return ClosureReport(resolved_sources, records(declared_assets), tuple(sorted(unresolved)),
                         tuple(sorted(dynamic)), records(schemas), tuple(sorted(external)),
                         not (unresolved or dynamic or external))
