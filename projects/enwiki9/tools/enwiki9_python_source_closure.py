#!/usr/bin/env python3
"""Compatibility CLI for explicit, declared-root Python dependency closure."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
try:
    from . import _enwiki9_bootstrap
except ImportError:
    import _enwiki9_bootstrap
from gamma_enwiki9.evidence.source_closure import resolve_closure

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def local_source_closure(entries, *, root=None, import_roots=None, schemas=(), assets=(),
                         dynamic_dependencies=None, external_modules=("jsonschema",)):
    root = ROOT if root is None else Path(root)
    report = resolve_closure(entries, root=root,
        import_roots=import_roots or (root, root / "tools", root / "src"),
        schemas=schemas, assets=assets, dynamic_dependencies=dynamic_dependencies,
        external_modules=external_modules, package_aliases={"projects.enwiki9": root})
    # Legacy list callers never represented completeness. New launchers consume
    # the structured report and require explicit declarations for every gap.
    return sorted(root / row["path"] for row in
                  (*report.sources, *report.schemas, *report.non_source_dependencies))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", nargs="+", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--import-root", action="append", type=Path)
    parser.add_argument("--schema", action="append", type=Path, default=[])
    parser.add_argument("--asset", action="append", type=Path, default=[])
    parser.add_argument("--external-module", action="append", default=[])
    parser.add_argument("--dynamic-dependencies", type=Path)
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    report = resolve_closure(args.entry, root=args.root,
        import_roots=args.import_root or (args.root, args.root / "tools", args.root / "src"),
        schemas=args.schema, assets=args.asset, external_modules=args.external_module,
        dynamic_dependencies=json.loads(args.dynamic_dependencies.read_text()) if args.dynamic_dependencies else {},
        package_aliases={"projects.enwiki9": args.root})
    rows = [{"path": r["path"], "sha256": "sha256:" + r["sha256"]}
            for r in (*report.sources, *report.schemas, *report.non_source_dependencies)]
    print(json.dumps(report.to_dict() if args.report else rows, indent=2))
    return int(args.require_complete and not report.complete)


if __name__ == "__main__":
    raise SystemExit(main())
