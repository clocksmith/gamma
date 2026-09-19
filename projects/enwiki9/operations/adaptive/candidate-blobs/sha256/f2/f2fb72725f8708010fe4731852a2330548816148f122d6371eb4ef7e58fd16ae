#!/usr/bin/env python3
"""Generate source-linked tool discovery by reading source and frozen contracts.

No catalogued module is imported, compiled, or executed. Static declarations
describe a tool; they do not validate its behavior or authorize a launch.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from lib.artifacts import artifact_ref, atomic_write

SUFFIXES = {".py", ".sh", ".c", ".cpp", ".h", ".hpp", ".html", ".gdb"}
MAX_SOURCE_BYTES = 4 * 1024 * 1024
UNKNOWN = "unknown; inspect source and the selected experiment"
# Previous inventory descriptions for the five Python tools without docstrings.
FALLBACK_PURPOSES = {
    "run_with_rss_guard.py": "Wraps commands with RSS sampling and guard enforcement; writes live and final guard JSON.",
    "page_order_screen.py": "Screens page ordering rules.",
    "page_family_gate.py": "Screens page-family state.",
    "fx2_reorder_dictionary.py": "Reorder/dictionary experiments.",
    "sketch_probe.py": "Sketch-based signal probes.",
}


def tool_paths(root: Path) -> list[Path]:
    """Include supported source/template files, without traversing symlinks."""
    base = Path(root) / "tools"
    if not base.is_dir() or base.is_symlink():
        return []
    return sorted(path for path in base.rglob("*") if path.suffix in SUFFIXES
                  and (path.is_file() or path.is_symlink())
                  and "__pycache__" not in path.parts
                  and not any(parent.is_symlink() for parent in path.parents if parent != base))


def _literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return None


def _name(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _name(node.value) + "." + node.attr
    return ""


def _compact(value: str, limit: int = 480) -> str:
    return " ".join(value.split())[:limit]


def _python_metadata(source: str) -> dict:
    tree = ast.parse(source)
    doc = ast.get_docstring(tree) or ""
    metadata, resources, arguments, launches = {}, [], [], []
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                aliases[alias.asname or alias.name] = (node.module or "") + "." + alias.name
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = _literal(node.value)
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            if target.id == "TOOL_METADATA" and isinstance(value, dict):
                metadata = value
            elif re.search(r"(?:MEMORY|RSS|DISK|SCRATCH|CPU|TIMEOUT|WALL|SECONDS|LIMIT)", target.id):
                if isinstance(value, (str, int, float, list, tuple)) and len(str(value)) <= 200:
                    resources.append(f"{target.id}={value}")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called = _name(node.func)
        prefix, _, tail = called.partition(".")
        called = aliases.get(prefix, prefix) + ("." + tail if tail else "")
        if called in {"subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_call",
                      "subprocess.check_output", "os.system", "os.fork", "os.execv", "os.execve",
                      "multiprocessing.Process", "asyncio.create_subprocess_exec", "asyncio.create_subprocess_shell"}:
            launches.append(called)
        if not called.endswith(".add_argument"):
            continue
        flags = [arg.value for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
        if not flags:
            continue
        keywords = {kw.arg: _literal(kw.value) for kw in node.keywords if kw.arg}
        argument = {"flags": flags, "required": keywords.get("required") is True}
        for key in ("default", "help", "choices", "nargs"):
            value = keywords.get(key)
            if value is not None and len(str(value)) <= 300:
                argument[key] = value
        arguments.append(argument)
    inputs, outputs = [], []
    for argument in arguments:
        for flag in argument["flags"]:
            if flag in {"--input", "--input-file", "--input-dir", "--source", "--source-dir", "input"}:
                inputs.append("CLI option " + flag)
            elif flag in {"--output", "--output-file", "--output-dir", "--out", "--out-dir", "output"}:
                outputs.append("CLI option " + flag)
    return {"purpose": metadata.get("purpose") or doc,
            "inputs": metadata.get("inputs", inputs), "outputs": metadata.get("outputs", outputs),
            "resources": metadata.get("resources", resources), "arguments": arguments,
            "launch_calls": sorted(set(launches))}


def _contract_index(root: Path, allowed_paths: set[str] | None = None) -> dict:
    """Link declared runner/source dependencies; never open their input artifacts."""
    index, diagnostics = defaultdict(list), []
    for path in sorted((root / "operations/adaptive/experiments").glob("*.json")):
        if allowed_paths is not None and path.relative_to(root).as_posix() not in allowed_paths:
            continue
        try:
            if path.is_symlink() or path.stat().st_size > MAX_SOURCE_BYTES:
                raise ValueError("contract is a symlink or exceeds static discovery byte limit")
            contract = json.loads(path.read_text())
            if not isinstance(contract, dict):
                raise ValueError("expected a contract object")
        except (OSError, UnicodeError, ValueError) as exc:
            diagnostics.append({"path": path.relative_to(root).as_posix(), "reason": _compact(str(exc), 160)})
            continue
        inputs, outputs = contract.get("inputs", []), contract.get("outputs", [])
        if not isinstance(inputs, list) or not isinstance(outputs, list):
            diagnostics.append({"path": path.relative_to(root).as_posix(), "reason": "inputs and outputs must be arrays"})
            continue
        paths = {item["path"] for item in inputs if isinstance(item, dict) and isinstance(item.get("path"), str)}
        for source in sorted(item for item in paths if item.startswith("tools/") and ".." not in Path(item).parts):
            index[source].append({"id": str(contract.get("experimentId", path.stem)),
                                  "path": path.relative_to(root).as_posix(),
                                  "outputs": [item for item in outputs if isinstance(item, str)],
                                  "status": contract.get("status", "unknown")})
    return index, diagnostics


def build_catalogue(root: Path = ROOT, *, allowed_paths: set[str] | None = None) -> list[dict]:
    """Return deterministic browsing rows; no row grants scheduling authority."""
    root = Path(root).resolve()
    contracts, index_diagnostics = _contract_index(root, allowed_paths)
    rows = []
    for path in tool_paths(root):
        relative = path.relative_to(root).as_posix()
        if allowed_paths is not None and relative not in allowed_paths:
            continue
        row = {"id": relative, "name": path.name, "path": relative,
               "purpose": UNKNOWN, "inputs": [], "outputs": [], "resources": [],
               "launch_capability": "unknown; static inspection cannot prove absence of execution",
               "launch_authority": "none; use the existing lab workflow and bound experiment",
               "sources": [relative], "candidate_ids": [], "diagnostics": [], "arguments": []}
        try:
            if path.stat().st_size > MAX_SOURCE_BYTES:
                raise ValueError("source exceeds static discovery byte limit")
            row["artifact"] = artifact_ref(path, root)
            source = path.read_text()
            if path.suffix == ".py":
                metadata = _python_metadata(source)
                row["purpose"] = _compact(str(metadata["purpose"] or FALLBACK_PURPOSES.get(path.name, UNKNOWN)))
                for key in ("inputs", "outputs", "resources", "arguments"):
                    value = metadata.get(key)
                    row[key + "_count"] = len(value) if isinstance(value, list) else int(bool(value))
                    row[key] = value[:64] if isinstance(value, list) else [str(value)] if value else []
                if metadata["launch_calls"]:
                    row["launch_capability"] = "process-launch calls present: " + ", ".join(metadata["launch_calls"])
            else:
                line_marker = r"#" if path.suffix in {".sh", ".gdb"} else r"//"
                comments = re.match(r"\s*(?:#![^\n]*\n)?((?:(?:\s*" + line_marker + r")[^\n]*\n)+|\s*/\*[\s\S]*?\*/|\s*<!--[\s\S]*?-->)", source)
                if comments:
                    row["purpose"] = _compact(re.sub(r"(?:^|\n)\s*(?://|#|\*)\s?|/\*|\*/|<!--|-->", " ", comments[1])) or UNKNOWN
                row["launch_capability"] = {".sh": "shell script; execution effects unverified",
                                             ".html": "browser template; script effects unverified"}.get(path.suffix, "native or debugger source; build/execution effects unverified")
        except (OSError, UnicodeError, ValueError, SyntaxError, RecursionError) as exc:
            row["diagnostics"].append(f"static inspection failed: {type(exc).__name__}: {_compact(str(exc), 180)}")
        linked = contracts.get(relative, [])
        row["candidate_ids"] = sorted({contract["id"] for contract in linked})
        row["contract_count"] = len(linked)
        row["contract_link_meaning"] = "contract references this source path; source hash, ancestry and admission are not validated here"
        row["sources"].extend(contract["path"] for contract in linked[:12])
        row["contract_outputs"] = sorted({output for contract in linked for output in contract["outputs"]})[:12]
        row["inputs"] = row["inputs"] or ["unknown; CLI declarations and linked contracts below"]
        row["outputs"] = row["outputs"] or ["unknown; linked contract outputs describe experiments using this tool"]
        row["resources"] = row["resources"] or ["unknown; validate the selected job's explicit resource contract"]
        row["resource_authority"] = "source declarations only; not measured use, enforced limits, or admission permission"
        rows.append(row)
    if rows and index_diagnostics:
        # Collection-wide failures appear once, without multiplying them per tool.
        rows[0]["catalogue_diagnostics"] = index_diagnostics
    return rows


def build_durable_catalogue(root: Path = ROOT) -> list[dict]:
    """Keep published links within Git-indexed paths; fixtures need no Git repo.

    This read-only Git query selects paths, including newly staged additions.
    Metadata still comes from the working files being prepared for publication.
    Interactive build_catalogue deliberately includes local drafts instead.
    """
    root = Path(root).resolve()
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "-z", "--", "tools", "operations/adaptive/experiments"],
        capture_output=True, env={**os.environ, "LC_ALL": "C"}, timeout=15,
    )
    if completed.returncode:
        if b"not a git repository" in completed.stderr:
            return build_catalogue(root)
        raise RuntimeError("cannot determine published tool paths: " + completed.stderr.decode(errors="replace").strip())
    allowed = {os.fsdecode(item) for item in completed.stdout.split(b"\0") if item}
    return build_catalogue(root, allowed_paths=allowed)


def _cell(value: str) -> str:
    return value.replace("|", "&#124;").replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")


def render_markdown(rows: list[dict]) -> str:
    counts = ", ".join(f"{count} {suffix}" for suffix, count in sorted(Counter(Path(row["path"]).suffix for row in rows).items()))
    lines = ["# enwiki9 Tooling Inventory", "", "Generated from tool source and existing experiment contracts. This is a disposable discovery view.",
             "No catalogued tool is imported or executed. Listed capabilities and resource constants do not grant launch permission.", "",
             "This checked-in inventory includes Git-indexed tool and contract paths, including newly staged additions; non-Git fixtures use their filesystem.",
             "Interactive ledger discovery also includes working-tree drafts. Stage intended sources before regenerating this published inventory.",
             "Use `python3 tools/enwiki9_lab.py records --view tools --search QUERY` for bounded details, CLI arguments, resource declarations and source links.",
             "Regenerate with `python3 tools/enwiki9_tool_catalogue.py`; check drift with `python3 tools/enwiki9_tool_catalogue.py --check`.",
             "The source files and selected frozen contracts remain authoritative; unknown metadata is explicit.",
             "Reusable artifact helpers for new tools: [lib/artifacts.py](../lib/artifacts.py). Measured source versions remain unchanged.",
             "The LibNC initializer teacher launcher exits before the first forward, gradient, update, or coded symbol; its source-bound experiment defines that boundary.",
             "The delayed-status helper's `enwiki9_delayed_status_latest.log` pointer is operational history, not present-host occupancy proof.", "",
             f"Coverage: **{len(rows)} files** ({counts}).", "", "| Tool | Purpose | Referenced contracts |", "|---|---|---|"]
    for row in rows:
        contracts = row["contract_count"]
        link = row["sources"][1] if contracts else None
        count = f"[{contracts}](../{link})" if link else "none found"
        purpose = _cell(row["purpose"])
        if row["diagnostics"]:
            purpose += " Static inspection incomplete; see catalogue diagnostics."
        lines.append(f"| [`{row['path']}`](../{row['path']}) | {purpose} | {count} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated documentation has drifted; write nothing.")
    args = parser.parse_args(argv)
    document = ROOT / "docs/tooling_inventory.md"
    expected = render_markdown(build_durable_catalogue(ROOT))
    if args.check:
        if not document.exists() or document.read_text() != expected:
            print("Tool inventory is stale; run python3 tools/enwiki9_tool_catalogue.py", file=sys.stderr)
            return 1
    else:
        atomic_write(document, expected)
    print(f"Tool inventory {'verified' if args.check else 'generated'}: {document.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
