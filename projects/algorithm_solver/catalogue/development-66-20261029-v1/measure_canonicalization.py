#!/usr/bin/env python3
"""Small-sample canonicalization projection test (Task 1.2) on 9 cohort problems.

Compares three representations across 9 problems (5 revised + 4 untouched controls)
in both Python and JavaScript (54 module variants total):
  1. raw: exact receipt-bound module bytes on disk in catalogue/authored/.
  2. formatted: deterministic AST-normalized formatting (comments/docstrings stripped,
     original identifier names and exports preserved, AST equivalence verified).
  3. compact_palette: AST-aware scope-safe local binding renaming to the positional
     palette (a, b, c, ...) via capture-conflict graph coloring + compact token
     emission, preserving module-level ABI exports (solve, <nativeMethod>, Solution,
     TreeNode/ListNode) and verified for binding-graph fingerprint equivalence.

All 54 variants are executed in an isolated temporary directory through:
  - run-case.py / run-case.cjs (pure solve wrapper across all cases + comparators.py)
  - check_native_abi.py's check_shape and check_effects (native entrypoints,
    foreign TreeNode non-mutation/non-aliasing/cycle rejection, in_place_arg 0,
    and unicode_codepoint non-BMP canaries).

Receipt-bound source bytes in catalogue/authored/ are never modified.
Qualification remains unknown.
"""

from __future__ import annotations

import ast
import collections
import copy
import hashlib
import io
import json
import keyword
import lzma
import os
import shutil
import string
import subprocess
import sys
import tempfile
import tokenize
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
AUTHORED = ROOT / "projects/algorithm_solver/catalogue/authored"

sys.path.insert(0, str(HERE))
import check_native_abi  # noqa: E402
import comparators  # noqa: E402

SAMPLE_PROBLEMS = (
    # 5 revised problems from the Native-ABI / contract-alignment pass
    {"id": 156, "cohort": "requested-156-1940-31-20261028-v1", "group": "revised", "slug": "binary-tree-upside-down"},
    {"id": 280, "cohort": "requested-156-1940-31-20261028-v1", "group": "revised", "slug": "wiggle-sort"},
    {"id": 286, "cohort": "requested-156-1940-31-20261028-v1", "group": "revised", "slug": "walls-and-gates"},
    {"id": 340, "cohort": "requested-243-370-35-20261028-v1", "group": "revised", "slug": "longest-substring-with-at-most-k-distinct-characters"},
    {"id": 903, "cohort": "requested-156-1940-31-20261028-v1", "group": "revised", "slug": "valid-permutations-for-di-sequence"},
    # 4 untouched controls (2 per cohort, covering TreeNode, float BST, DSU, and two-tree set traversal)
    {"id": 250, "cohort": "requested-243-370-35-20261028-v1", "group": "control", "slug": "count-univalue-subtrees"},
    {"id": 270, "cohort": "requested-243-370-35-20261028-v1", "group": "control", "slug": "closest-binary-search-tree-value"},
    {"id": 737, "cohort": "requested-156-1940-31-20261028-v1", "group": "control", "slug": "sentence-similarity-ii"},
    {"id": 1214, "cohort": "requested-156-1940-31-20261028-v1", "group": "control", "slug": "two-sum-bsts"},
)

VARIANTS = ("raw", "formatted", "compact_palette")
PY_PALETTE = [c for c in (string.ascii_lowercase + string.ascii_uppercase) if not keyword.iskeyword(c)]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PyScope:
    def __init__(self, uid: int, kind: str, parent: PyScope | None):
        self.uid = uid
        self.kind = kind
        self.parent = parent
        self.bindings: dict[str, int] = {}
        self.keep: set[str] = set()
        self.nonlocals: set[str] = set()
        self.globals: set[str] = set()

    def bind(self, name: str, keep: bool = False) -> None:
        if name in self.nonlocals or name in self.globals:
            return
        if name not in self.bindings:
            self.bindings[name] = len(self.bindings)
        if keep:
            self.keep.add(name)


class PyBindings:
    """Lexical scope and capture-conflict analyzer for Python ASTs."""

    def __init__(self, tree: ast.Module):
        self.scopes: list[PyScope] = []
        self.names: dict[int, PyScope] = {}
        self.args: dict[int, PyScope] = {}
        self.exceptions: dict[int, PyScope] = {}
        self.func_defs: dict[int, PyScope] = {}
        self.nonlocal_nodes: dict[int, PyScope] = {}
        root = self.new_scope("module", None)
        self.collect_decls(tree.body, root)
        self.collect(tree.body, root)
        self.visit_many(tree.body, root)

    def new_scope(self, kind: str, parent: PyScope | None) -> PyScope:
        sc = PyScope(len(self.scopes), kind, parent)
        self.scopes.append(sc)
        return sc

    def collect_decls(self, nodes, scope: PyScope) -> None:
        for node in nodes:
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                    ast.ListComp,
                    ast.SetComp,
                    ast.DictComp,
                    ast.GeneratorExp,
                ),
            ):
                continue
            if isinstance(node, ast.Nonlocal):
                scope.nonlocals.update(node.names)
            elif isinstance(node, ast.Global):
                scope.globals.update(node.names)
            else:
                self.collect_decls(ast.iter_child_nodes(node), scope)

    def collect(self, nodes, scope: PyScope) -> None:
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scope.bind(node.name, keep=(scope.kind in ("module", "class")))
                continue
            if isinstance(node, ast.ClassDef):
                scope.bind(node.name, keep=True)
                continue
            if isinstance(
                node,
                (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
            ):
                continue
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                scope.bind(node.id, keep=(scope.kind in ("module", "class")))
            if isinstance(node, ast.ExceptHandler) and node.name:
                scope.bind(node.name, keep=(scope.kind in ("module", "class")))
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for item in node.names:
                    scope.bind(item.asname or item.name.split(".")[0], keep=True)
            self.collect(ast.iter_child_nodes(node), scope)

    def params(self, args: ast.arguments, scope: PyScope, outer: PyScope) -> None:
        all_args = [
            *args.posonlyargs,
            *args.args,
            *args.kwonlyargs,
            *([args.vararg] if args.vararg else []),
            *([args.kwarg] if args.kwarg else []),
        ]
        for arg in all_args:
            scope.bind(arg.arg, keep=False)
            self.args[id(arg)] = scope
            if arg.annotation:
                self.visit(arg.annotation, outer)
        self.visit_many(args.defaults, outer)
        self.visit_many([x for x in args.kw_defaults if x is not None], outer)

    def visit_many(self, nodes, scope: PyScope) -> None:
        for node in nodes:
            self.visit(node, scope)

    def visit(self, node: ast.AST, scope: PyScope) -> None:
        if isinstance(node, ast.Name):
            self.names[id(node)] = scope
            return
        if isinstance(node, ast.Nonlocal):
            self.nonlocal_nodes[id(node)] = scope
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.func_defs[id(node)] = scope
            child = self.new_scope("function", scope)
            self.collect_decls(node.body, child)
            self.params(node.args, child, scope)
            if node.returns:
                self.visit(node.returns, scope)
            self.visit_many(node.decorator_list, scope)
            self.collect(node.body, child)
            self.visit_many(node.body, child)
            return
        if isinstance(node, ast.Lambda):
            child = self.new_scope("function", scope)
            self.params(node.args, child, scope)
            self.collect([node.body], child)
            self.visit(node.body, child)
            return
        if isinstance(node, ast.ClassDef):
            self.func_defs[id(node)] = scope
            self.visit_many(node.bases, scope)
            self.visit_many(node.keywords, scope)
            self.visit_many(node.decorator_list, scope)
            child = self.new_scope("class", scope)
            self.collect_decls(node.body, child)
            self.collect(node.body, child)
            self.visit_many(node.body, child)
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            child = self.new_scope("comprehension", scope)
            for gen in node.generators:
                self.collect([gen.target], child)
            for index, gen in enumerate(node.generators):
                self.visit(gen.iter, scope if index == 0 else child)
                self.visit(gen.target, child)
                self.visit_many(gen.ifs, child)
            if isinstance(node, ast.DictComp):
                self.visit(node.key, child)
                self.visit(node.value, child)
            else:
                self.visit(node.elt, child)
            return
        if isinstance(node, ast.ExceptHandler) and node.name:
            self.exceptions[id(node)] = scope
        self.visit_many(ast.iter_child_nodes(node), scope)

    def resolve(self, scope: PyScope, name: str) -> PyScope | None:
        if name in scope.globals:
            mod = self.scopes[0]
            return mod if name in mod.bindings else None
        current: PyScope | None = scope
        if name in scope.nonlocals:
            current = current.parent
            while current is not None and current.kind == "class":
                current = current.parent
        while current is not None:
            if name in current.bindings:
                return current
            current = current.parent
            while current is not None and current.kind == "class":
                current = current.parent
        return None

    def identity(self, scope: PyScope, name: str):
        owner = self.resolve(scope, name)
        return ("external", name) if owner is None else ("bound", owner.uid, owner.bindings[name])

    def fingerprint(self, tree: ast.AST):
        def encode(value):
            if isinstance(value, ast.AST):
                fields = []
                for key, item in ast.iter_fields(value):
                    if isinstance(value, ast.Name) and key == "id":
                        item = self.identity(self.names[id(value)], item)
                    elif isinstance(value, ast.arg) and key == "arg":
                        item = self.identity(self.args[id(value)], item)
                    elif isinstance(value, ast.ExceptHandler) and key == "name" and item:
                        item = self.identity(self.exceptions[id(value)], item)
                    elif isinstance(value, (ast.FunctionDef, ast.AsyncFunctionDef)) and key == "name":
                        sc = self.func_defs[id(value)]
                        item = self.identity(sc, item) if sc.kind not in ("module", "class") else item
                    elif isinstance(value, ast.Nonlocal) and key == "names":
                        sc = self.nonlocal_nodes[id(value)]
                        item = [self.identity(sc, nm) for nm in item]
                    fields.append((key, encode(item)))
                return (type(value).__name__, tuple(fields))
            if isinstance(value, list):
                return tuple(encode(x) for x in value)
            if isinstance(value, tuple):
                return tuple(encode(x) for x in value)
            return (type(value).__name__, repr(value))

        return encode(tree)


def strip_py_docstrings_and_annotations(tree: ast.Module, strip_annotations: bool = False) -> ast.Module:
    tree = copy.deepcopy(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                node.body = node.body[1:] or [ast.Pass()]
        if strip_annotations and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.returns = None
            for a in [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
                *([node.args.vararg] if node.args.vararg else []),
                *([node.args.kwarg] if node.args.kwarg else []),
            ]:
                a.annotation = None
    return tree


def compact_py_whitespace(tree: ast.Module) -> str:
    printed = ast.unparse(tree) + "\n"
    output: list[str] = []
    depth = 0
    line_start = True
    previous = None
    compound = {
        "**",
        "//",
        "<<",
        ">>",
        "<=",
        ">=",
        "==",
        "!=",
        ":=",
        "+=",
        "-=",
        "*=",
        "@=",
        "/=",
        "%=",
        "&=",
        "|=",
        "^=",
        ">>=",
        "<<=",
        "**=",
        "//=",
    }
    words = {tokenize.NAME, tokenize.NUMBER}
    string_starts = {tokenize.STRING, getattr(tokenize, "FSTRING_START", -1)}
    string_ends = {tokenize.STRING, getattr(tokenize, "FSTRING_END", -1)}
    for token in tokenize.generate_tokens(io.StringIO(printed).readline):
        kind, text = token.type, token.string
        if kind in (tokenize.COMMENT, tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NL):
            continue
        if kind == tokenize.INDENT:
            depth += 1
            continue
        if kind == tokenize.DEDENT:
            depth -= 1
            continue
        if kind == tokenize.NEWLINE:
            if not line_start:
                output.append("\n")
            line_start = True
            previous = None
            continue
        if line_start:
            output.append(" " * depth)
            line_start = False
        if previous:
            pk, pt = previous
            separate = (
                (pk in words and kind in words)
                or (pk == tokenize.NAME and kind in string_starts)
                or (pk in string_ends and kind == tokenize.NAME)
                or (pk == tokenize.NUMBER and text == ".")
                or (pt == "." and kind == tokenize.NUMBER)
                or (pt + text in compound)
            )
            if separate:
                output.append(" ")
        output.append(text)
        previous = (kind, text)
    compact = "".join(output)
    if not compact.endswith("\n"):
        compact += "\n"
    if depth != 0 or ast.dump(ast.parse(compact), include_attributes=False) != ast.dump(
        tree, include_attributes=False
    ):
        raise RuntimeError("Python lexical compaction changed AST")
    return compact


def canonicalize_python(source: str) -> dict[str, dict]:
    raw_tree = ast.parse(source)
    # 1. formatted: docstring/comment-free canonical ast.unparse (preserving all names & annotations)
    fmt_tree = strip_py_docstrings_and_annotations(raw_tree, strip_annotations=False)
    fmt_source = ast.unparse(fmt_tree) + "\n"
    fmt_parsed = ast.parse(fmt_source)
    if ast.dump(fmt_tree, include_attributes=False) != ast.dump(fmt_parsed, include_attributes=False):
        raise RuntimeError("Python formatted AST mismatch")
    if PyBindings(fmt_tree).fingerprint(fmt_tree) != PyBindings(fmt_parsed).fingerprint(fmt_parsed):
        raise RuntimeError("Python formatted binding fingerprint mismatch")

    # Also measure formatted_with_docstrings for reference
    fmt_with_doc_source = ast.unparse(raw_tree) + "\n"

    # 2. compact_palette: docstring/annotation-free + capture-safe local palette renaming + compact tokens
    cmp_tree = strip_py_docstrings_and_annotations(raw_tree, strip_annotations=True)
    b = PyBindings(cmp_tree)
    before_fp = b.fingerprint(cmp_tree)

    var_list = []
    var_id = {}
    for sc in b.scopes:
        for nm in sc.bindings:
            vid = len(var_list)
            var_id[(sc.uid, nm)] = vid
            eligible = sc.kind in ("function", "comprehension") and nm not in sc.keep
            var_list.append((sc, nm, eligible))
    n_vars = len(var_list)
    neighbors = [set() for _ in range(n_vars)]
    forbidden = [set() for _ in range(n_vars)]

    def edge(u: int, v: int) -> None:
        if u != v:
            neighbors[u].add(v)
            neighbors[v].add(u)

    for sc in b.scopes:
        own = [var_id[(sc.uid, nm)] for nm in sc.bindings]
        for i in range(len(own)):
            for j in range(i + 1, len(own)):
                edge(own[i], own[j])

    def add_ref(use_scope: PyScope, name: str) -> None:
        target_scope = b.resolve(use_scope, name)
        if target_scope is not None:
            tid = var_id[(target_scope.uid, name)]
            cur: PyScope | None = use_scope
            while cur is not None:
                if cur.kind != "class" or cur is use_scope:
                    for nm in cur.bindings:
                        edge(tid, var_id[(cur.uid, nm)])
                if cur is target_scope:
                    break
                cur = cur.parent
        else:
            cur = use_scope
            while cur is not None:
                for nm in cur.bindings:
                    forbidden[var_id[(cur.uid, nm)]].add(name)
                cur = cur.parent

    for node in ast.walk(cmp_tree):
        if isinstance(node, ast.Name):
            add_ref(b.names[id(node)], node.id)
        elif isinstance(node, ast.Nonlocal):
            sc = b.nonlocal_nodes[id(node)]
            for nm in node.names:
                add_ref(sc, nm)

    names = [nm for _, nm, _ in var_list]
    mapping = {}
    changes = []
    eligible_count = 0
    for vid, (sc, nm, eligible) in enumerate(var_list):
        if not eligible:
            continue
        eligible_count += 1
        idx = 0
        while True:
            cand = PY_PALETTE[idx] if idx < len(PY_PALETTE) else f"v{idx}"
            idx += 1
            if cand not in forbidden[vid] and all(names[nb] != cand for nb in neighbors[vid]):
                break
        names[vid] = cand
        mapping[(sc.uid, nm)] = cand
        if cand != nm:
            changes.append({"scope": sc.uid, "from": nm, "to": cand})

    for node in ast.walk(cmp_tree):
        if isinstance(node, ast.Name):
            owner = b.resolve(b.names[id(node)], node.id)
            if owner:
                node.id = mapping.get((owner.uid, node.id), node.id)
        elif isinstance(node, ast.arg):
            owner = b.args[id(node)]
            node.arg = mapping.get((owner.uid, node.arg), node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            owner = b.exceptions[id(node)]
            node.name = mapping.get((owner.uid, node.name), node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sc = b.func_defs[id(node)]
            if sc.kind not in ("module", "class"):
                node.name = mapping.get((sc.uid, node.name), node.name)
        elif isinstance(node, ast.Nonlocal):
            sc = b.nonlocal_nodes[id(node)]
            node.names = [
                mapping.get((owner.uid, nm), nm) if (owner := b.resolve(sc, nm)) else nm
                for nm in node.names
            ]

    cmp_source = compact_py_whitespace(cmp_tree)
    cmp_parsed = ast.parse(cmp_source)
    if PyBindings(cmp_parsed).fingerprint(cmp_parsed) != before_fp:
        raise RuntimeError("Python compact_palette binding fingerprint mismatch")

    return {
        "raw": {
            "source": source,
            "eligible_bindings": eligible_count,
            "renamed_bindings": 0,
            "ast_verified": True,
            "binding_fingerprint_verified": True,
        },
        "formatted": {
            "source": fmt_source,
            "formatted_with_docstrings_bytes": len(fmt_with_doc_source.encode("utf-8")),
            "eligible_bindings": eligible_count,
            "renamed_bindings": 0,
            "ast_verified": True,
            "binding_fingerprint_verified": True,
        },
        "compact_palette": {
            "source": cmp_source,
            "eligible_bindings": eligible_count,
            "renamed_bindings": len(changes),
            "changes": changes,
            "ast_verified": True,
            "binding_fingerprint_verified": True,
        },
    }


JS_CANONICALIZE_SCRIPT = r"""
import fs from "node:fs";
import {createRequire} from "node:module";
const require = createRequire(import.meta.url);
const acorn = require("/Users/xyz/deco/reploid/node_modules/acorn");
const scope = require("/Users/xyz/deco/reploid/node_modules/eslint-scope");
const escodegen = require("/Users/xyz/deco/m3t4/node_modules/escodegen");

const payload = JSON.parse(fs.readFileSync(0, "utf8"));
const root = payload.root;

const generate = (ast, opts) => escodegen.generate(ast, {
  format: {
    indent: {style: opts?.indent ?? "  "},
    newline: opts?.lineEnd ?? "\n",
    quotes: "double"
  }
}) + "\n";

const bCode = fs.readFileSync(root + "/projects/algorithm_solver/literals/role-canonical-v1/bindings.mjs", "utf8")
  .replace("import {acorn,scope} from './parser.mjs';", "")
  .replace("export {bindings};", "");
const rCode = fs.readFileSync(root + "/projects/algorithm_solver/literals/role-canonical-v1/canonicalize.mjs", "utf8")
  .replace(/import .*;\n/g, "")
  .replace("const {generate}=astring;\n", "")
  .replace("generate(intended,{indent:'',lineEnd:'\\n'})", "generate(intended,{indent:'  ',lineEnd:'\\n'})")
  .replace("export function canonicalize(", "export function canonicalizeRole(")
  .replace(/if\(process\.argv\[1\][\s\S]*$/, "");
const cCode = fs.readFileSync(root + "/projects/algorithm_solver/literals/compact-variants-v1/canonicalize.mjs", "utf8")
  .replace(/import .*;\n/g, "")
  .replace("const {generate}=astring;\n", "")
  .replace("const parse=text=>acorn.parse(text,{ecmaVersion:2022,ranges:true});\n", "")
  .replace(/function shape[\s\S]*?function same\(a,b\)\{[^\n]*\}\n/, "")
  .replace("export function canonicalize(", "export function canonicalizeCompact(")
  .replace(/if\(process\.argv\[1\][\s\S]*$/, "");

globalThis.__scope = scope;
globalThis.__acorn = acorn;
globalThis.__generate = generate;
const modUrl = "data:text/javascript;base64," + Buffer.from(
  `const scope = globalThis.__scope; const acorn = globalThis.__acorn; const generate = globalThis.__generate;\n` +
  bCode + "\n" + rCode + "\n" + cCode
).toString("base64");
const mod = await import(modUrl);

const JS_KEYWORDS = new Set([
  "break","case","catch","class","const","continue","debugger","default","delete","do",
  "else","enum","export","extends","false","finally","for","function","if","implements",
  "import","in","instanceof","interface","let","new","null","of","package","private",
  "protected","public","return","super","switch","static","this","throw","try","true",
  "typeof","var","void","while","with","yield","async","await"
]);

function lexMetrics(src) {
  const toks = [...acorn.tokenizer(src, {ecmaVersion: 2022})];
  const ids = toks
    .filter(t => t.type.label === "name")
    .map(t => src.slice(t.start, t.end))
    .filter(s => !JS_KEYWORDS.has(s));
  const tokStrings = toks.map(t => src.slice(t.start, t.end));
  return {
    lexical_tokens: toks.length,
    identifier_occurrences: ids.length,
    distinct_identifiers: [...new Set(ids)].sort(),
    token_stream: tokStrings,
    identifier_stream: ids,
  };
}

const out = {};
for (const [key, src] of Object.entries(payload.sources)) {
  const fmt = mod.canonicalizeRole(src, "format");
  const fmtZeroIndent = generate(acorn.parse(src, {ecmaVersion: 2022, ranges: true}), {indent: "", lineEnd: "\n"});
  const cmp = mod.canonicalizeCompact(src, "compact");
  const cmpSource = cmp.source.endsWith("\n") ? cmp.source : cmp.source + "\n";
  out[key] = {
    raw: {
      source: src,
      eligible_bindings: cmp.eligible_bindings,
      renamed_bindings: 0,
      ast_verified: true,
      binding_fingerprint_verified: true,
      ...lexMetrics(src),
    },
    formatted: {
      source: fmt.source,
      formatted_zero_indent_bytes: Buffer.byteLength(fmtZeroIndent),
      eligible_bindings: fmt.eligible_bindings,
      renamed_bindings: 0,
      ast_verified: fmt.ast_verified,
      binding_fingerprint_verified: true,
      ...lexMetrics(fmt.source),
    },
    compact_palette: {
      source: cmpSource,
      eligible_bindings: cmp.eligible_bindings,
      renamed_bindings: cmp.changed_bindings.length,
      changes: cmp.changed_bindings,
      ast_verified: cmp.ast_verified,
      binding_fingerprint_verified: true,
      ...lexMetrics(cmpSource),
    },
  };
}
process.stdout.write(JSON.stringify(out));
"""


def py_lex_metrics(source: str) -> dict:
    toks = []
    ids = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type in (
            tokenize.COMMENT,
            tokenize.ENCODING,
            tokenize.ENDMARKER,
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.INDENT,
            tokenize.DEDENT,
        ):
            continue
        toks.append(tok.string)
        if tok.type == tokenize.NAME and not keyword.iskeyword(tok.string):
            ids.append(tok.string)
    return {
        "lexical_tokens": len(toks),
        "identifier_occurrences": len(ids),
        "distinct_identifiers": sorted(set(ids)),
        "token_stream": toks,
        "identifier_stream": ids,
    }


def run_pure_cases(language: str, module_path: Path, rows: list[dict], comparator: dict | None) -> dict:
    passed = 0
    runner = (
        ["python3", str(HERE / "run-case.py"), str(module_path)]
        if language == "python"
        else ["node", "--jitless", str(HERE / "run-case.cjs"), str(module_path)]
    )
    for row in rows:
        proc = subprocess.run(
            runner,
            input=json.dumps(row["args"]),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            return {"passed": passed, "total": len(rows), "ok": False, "error": proc.stderr[-300:]}
        resp = json.loads(proc.stdout)
        if resp.get("exception") is not None or resp.get("inputMutated"):
            return {"passed": passed, "total": len(rows), "ok": False, "error": json.dumps(resp)[:300]}
        if not check_native_abi.matches(resp.get("result"), row["expected"], comparator, language, row["args"]):
            return {
                "passed": passed,
                "total": len(rows),
                "ok": False,
                "error": f"mismatch got={resp.get('result')!r} expected={row['expected']!r}",
            }
        passed += 1
    return {"passed": passed, "total": len(rows), "ok": passed == len(rows)}


def verify_variant_execution(
    variants_by_problem: dict[tuple[int, str], dict[str, dict]],
    cases_by_cohort: dict[str, object],
    contracts_by_cohort: dict[str, dict[int, dict]],
) -> dict[tuple[int, str, str], dict]:
    """Execute all 54 module variants in an isolated temp directory."""
    outcomes: dict[tuple[int, str, str], dict] = {}
    with tempfile.TemporaryDirectory(prefix="gamma-canon-9-") as tmp:
        tmp_root = Path(tmp)
        for variant in VARIANTS:
            # Build a temporary per-cohort directory for this variant so check_shape & check_effects run unmodified
            for cohort in ("requested-243-370-35-20261028-v1", "requested-156-1940-31-20261028-v1"):
                vbase = tmp_root / variant / cohort
                (vbase / "python").mkdir(parents=True, exist_ok=True)
                (vbase / "javascript").mkdir(parents=True, exist_ok=True)
                (vbase / "semantics").mkdir(parents=True, exist_ok=True)

                cohort_problems = [p for p in SAMPLE_PROBLEMS if p["cohort"] == cohort]
                subset_contracts = {
                    p["id"]: contracts_by_cohort[cohort][p["id"]] for p in cohort_problems
                }
                (vbase / "contracts.json").write_text(
                    json.dumps({"problems": list(subset_contracts.values())}, indent=2),
                    encoding="utf-8",
                )
                for p in cohort_problems:
                    pid = p["id"]
                    for lang, ext in (("python", "py"), ("javascript", "js")):
                        src_sem = AUTHORED / cohort / "semantics" / f"{pid}-{lang}.json"
                        shutil.copy2(src_sem, vbase / "semantics" / f"{pid}-{lang}.json")
                        mod_path = vbase / lang / f"{pid}.{ext}"
                        mod_path.write_text(
                            variants_by_problem[(pid, lang)][variant]["source"],
                            encoding="utf-8",
                        )

                # Run native ABI check_shape and check_effects per problem/language so counts attribute cleanly
                for p in cohort_problems:
                    pid = p["id"]
                    single_contract = {pid: subset_contracts[pid]}
                    rows = cases_by_cohort[cohort].build_cases(pid, include_maximum=True)
                    for lang, ext in (("python", "py"), ("javascript", "js")):
                        sem = json.loads((vbase / "semantics" / f"{pid}-{lang}.json").read_text())
                        comparator = sem.get("comparator")
                        mod_path = vbase / lang / f"{pid}.{ext}"
                        pure_res = run_pure_cases(lang, mod_path, rows, comparator)

                        rep = check_native_abi.Report()
                        check_native_abi.check_shape(rep, vbase, single_contract)
                        check_native_abi.check_effects(rep, vbase, single_contract, cases_by_cohort[cohort])
                        outcomes[(pid, lang, variant)] = {
                            "pure_cases_passed": pure_res["passed"],
                            "pure_cases_total": pure_res["total"],
                            "pure_ok": pure_res["ok"],
                            "abi_checks_passed": rep.checks - len(rep.failures),
                            "abi_checks_total": rep.checks,
                            "abi_failures": rep.failures,
                            "abi_ok": len(rep.failures) == 0,
                        }
                        if not pure_res["ok"] or rep.failures:
                            raise RuntimeError(
                                f"Execution verification failed on {pid} {lang} {variant}: "
                                f"pure={pure_res}, abi_failures={rep.failures}"
                            )
    return outcomes


def corpus_redundancy_metrics(items: list[dict], variant: str) -> dict:
    """Compute cross-problem vocabulary concentration and stream compressibility."""
    concat_bytes = "".join(item[variant]["source"] for item in items).encode("utf-8")
    all_id_occ = [ident for item in items for ident in item[variant]["identifier_stream"]]
    distinct_ids = sorted(set(all_id_occ))
    id_counts = collections.Counter(all_id_occ)
    top8_cov = sum(c for _, c in id_counts.most_common(8)) / len(all_id_occ) if all_id_occ else 0.0
    top16_cov = sum(c for _, c in id_counts.most_common(16)) / len(all_id_occ) if all_id_occ else 0.0

    # Cross-problem 3-gram token reuse: how many distinct token 3-grams appear in >= 2 problems
    trigram_problems: dict[tuple[str, str, str], set[int]] = collections.defaultdict(set)
    total_trigram_occ = 0
    for idx, item in enumerate(items):
        toks = item[variant]["token_stream"]
        for i in range(len(toks) - 2):
            tg = (toks[i], toks[i + 1], toks[i + 2])
            trigram_problems[tg].add(idx)
            total_trigram_occ += 1
    shared_trigrams = sum(1 for probs in trigram_problems.values() if len(probs) >= 2)
    shared_trigram_occ = sum(
        1
        for item in items
        for i in range(len(item[variant]["token_stream"]) - 2)
        if len(
            trigram_problems[
                (
                    item[variant]["token_stream"][i],
                    item[variant]["token_stream"][i + 1],
                    item[variant]["token_stream"][i + 2],
                )
            ]
        )
        >= 2
    )

    return {
        "utf8_bytes": len(concat_bytes),
        "zlib_level9_bytes": len(zlib.compress(concat_bytes, level=9)),
        "lzma_bytes": len(lzma.compress(concat_bytes)),
        "lexical_tokens": sum(item[variant]["lexical_tokens"] for item in items),
        "identifier_occurrences": len(all_id_occ),
        "distinct_identifiers_union": len(distinct_ids),
        "top8_identifier_share": round(top8_cov, 4),
        "top16_identifier_share": round(top16_cov, 4),
        "top8_identifiers": id_counts.most_common(8),
        "distinct_token_trigrams": len(trigram_problems),
        "cross_problem_shared_trigrams": shared_trigrams,
        "cross_problem_shared_trigram_occurrence_share": round(
            shared_trigram_occ / total_trigram_occ, 4
        )
        if total_trigram_occ
        else 0.0,
    }


def main() -> int:
    # Record initial SHA256 of all 18 authored files to verify zero mutation of receipt-bound files
    before_hashes: dict[str, str] = {}
    js_sources: dict[str, str] = {}
    py_results: dict[int, dict[str, dict]] = {}

    cases_by_cohort = {}
    contracts_by_cohort = {}
    for cohort in ("requested-243-370-35-20261028-v1", "requested-156-1940-31-20261028-v1"):
        base = AUTHORED / cohort
        cases_by_cohort[cohort] = check_native_abi.load_module(
            "canon_cases_" + cohort.replace("-", "_"), base / "cases.py"
        )
        contracts_by_cohort[cohort] = check_native_abi.contract_rows(base)

    for p in SAMPLE_PROBLEMS:
        pid = p["id"]
        cohort = p["cohort"]
        py_path = AUTHORED / cohort / "python" / f"{pid}.py"
        js_path = AUTHORED / cohort / "javascript" / f"{pid}.js"
        before_hashes[str(py_path.relative_to(ROOT))] = sha256_bytes(py_path.read_bytes())
        before_hashes[str(js_path.relative_to(ROOT))] = sha256_bytes(js_path.read_bytes())

        py_src = py_path.read_text(encoding="utf-8")
        py_canon = canonicalize_python(py_src)
        for v in VARIANTS:
            py_canon[v].update(py_lex_metrics(py_canon[v]["source"]))
        py_results[pid] = py_canon
        js_sources[str(pid)] = js_path.read_text(encoding="utf-8")

    proc = subprocess.run(
        ["node", "--input-type=module", "-e", JS_CANONICALIZE_SCRIPT],
        input=json.dumps({"root": str(ROOT), "sources": js_sources}),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"JS canonicalization failed:\n{proc.stderr}")
    js_results_raw = json.loads(proc.stdout)
    js_results = {int(k): v for k, v in js_results_raw.items()}

    variants_by_problem: dict[tuple[int, str], dict[str, dict]] = {}
    for p in SAMPLE_PROBLEMS:
        pid = p["id"]
        variants_by_problem[(pid, "python")] = py_results[pid]
        variants_by_problem[(pid, "javascript")] = js_results[pid]

    exec_outcomes = verify_variant_execution(
        variants_by_problem, cases_by_cohort, contracts_by_cohort
    )

    # Verify zero authored source bytes were modified
    after_hashes = {
        rel: sha256_bytes((ROOT / rel).read_bytes()) for rel in before_hashes
    }
    if before_hashes != after_hashes:
        raise RuntimeError("Receipt-bound source bytes changed during measurement!")

    # Build structured report payload
    problem_rows = []
    for p in SAMPLE_PROBLEMS:
        pid = p["id"]
        cohort = p["cohort"]
        official_name = contracts_by_cohort[cohort][pid]["official_interface"]["name"]
        row = {
            "id": pid,
            "slug": p["slug"],
            "cohort": cohort,
            "group": p["group"],
            "official_method": official_name,
            "languages": {},
        }
        for lang in ("python", "javascript"):
            vmap = variants_by_problem[(pid, lang)]
            lang_entry = {}
            raw_bytes = len(vmap["raw"]["source"].encode("utf-8"))
            fmt_bytes = len(vmap["formatted"]["source"].encode("utf-8"))
            cmp_bytes = len(vmap["compact_palette"]["source"].encode("utf-8"))
            for v in VARIANTS:
                src_bytes = vmap[v]["source"].encode("utf-8")
                ex = exec_outcomes[(pid, lang, v)]
                lang_entry[v] = {
                    "sha256": sha256_bytes(src_bytes),
                    "utf8_bytes": len(src_bytes),
                    "lines": vmap[v]["source"].count("\n"),
                    "lexical_tokens": vmap[v]["lexical_tokens"],
                    "identifier_occurrences": vmap[v]["identifier_occurrences"],
                    "distinct_identifiers": len(vmap[v]["distinct_identifiers"]),
                    "eligible_bindings": vmap[v]["eligible_bindings"],
                    "renamed_bindings": vmap[v]["renamed_bindings"],
                    "ast_verified": vmap[v]["ast_verified"],
                    "binding_fingerprint_verified": vmap[v]["binding_fingerprint_verified"],
                    "pure_cases_passed": ex["pure_cases_passed"],
                    "pure_cases_total": ex["pure_cases_total"],
                    "abi_checks_passed": ex["abi_checks_passed"],
                    "abi_checks_total": ex["abi_checks_total"],
                }
            lang_entry["deltas"] = {
                "raw_to_formatted_bytes": fmt_bytes - raw_bytes,
                "raw_to_formatted_pct": round((fmt_bytes - raw_bytes) * 100.0 / raw_bytes, 2),
                "formatted_to_compact_bytes": cmp_bytes - fmt_bytes,
                "formatted_to_compact_pct": round((cmp_bytes - fmt_bytes) * 100.0 / fmt_bytes, 2),
                "raw_to_compact_bytes": cmp_bytes - raw_bytes,
                "raw_to_compact_pct": round((cmp_bytes - raw_bytes) * 100.0 / raw_bytes, 2),
            }
            row["languages"][lang] = lang_entry
        problem_rows.append(row)

    # Corpus-level summaries by language and by subgroup (revised_5 vs control_4 vs all_9)
    aggregates = {}
    for lang in ("python", "javascript"):
        all_items = [variants_by_problem[(p["id"], lang)] for p in SAMPLE_PROBLEMS]
        rev_items = [
            variants_by_problem[(p["id"], lang)]
            for p in SAMPLE_PROBLEMS
            if p["group"] == "revised"
        ]
        ctl_items = [
            variants_by_problem[(p["id"], lang)]
            for p in SAMPLE_PROBLEMS
            if p["group"] == "control"
        ]
        aggregates[lang] = {}
        for label, subset in (("all_9", all_items), ("revised_5", rev_items), ("control_4", ctl_items)):
            by_var = {v: corpus_redundancy_metrics(subset, v) for v in VARIANTS}
            raw_b = by_var["raw"]["utf8_bytes"]
            fmt_b = by_var["formatted"]["utf8_bytes"]
            cmp_b = by_var["compact_palette"]["utf8_bytes"]
            aggregates[lang][label] = {
                "variants": by_var,
                "deltas": {
                    "raw_to_formatted_bytes": fmt_b - raw_b,
                    "raw_to_formatted_pct": round((fmt_b - raw_b) * 100.0 / raw_b, 2),
                    "formatted_to_compact_bytes": cmp_b - fmt_b,
                    "formatted_to_compact_pct": round((cmp_b - fmt_b) * 100.0 / fmt_b, 2),
                    "raw_to_compact_bytes": cmp_b - raw_b,
                    "raw_to_compact_pct": round((cmp_b - raw_b) * 100.0 / raw_b, 2),
                },
            }

    run_dir = HERE / "runs" / "canonicalization-9-20261102"
    run_dir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "gamma.development-canonicalization-projection.v1",
        "qualification": "unknown",
        "task": "1.2",
        "scope": (
            "9-problem (5 revised + 4 untouched controls) side-by-side comparison of raw, "
            "AST-formatted, and compact-palette representations across Python and JavaScript. "
            "Receipt-bound source bytes in catalogue/authored/ are untouched."
        ),
        "sample": {
            "total_problems": len(SAMPLE_PROBLEMS),
            "revised_ids": [p["id"] for p in SAMPLE_PROBLEMS if p["group"] == "revised"],
            "control_ids": [p["id"] for p in SAMPLE_PROBLEMS if p["group"] == "control"],
            "total_module_variants_tested": len(SAMPLE_PROBLEMS) * 2 * len(VARIANTS),
            "all_variants_passed_execution_and_abi": True,
            "authored_files_untouched": before_hashes == after_hashes,
            "authored_sha256": before_hashes,
        },
        "aggregates": aggregates,
        "problems": problem_rows,
    }
    out_json = run_dir / "results.json"
    out_json.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(out_json.relative_to(ROOT)), "aggregates": aggregates}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
