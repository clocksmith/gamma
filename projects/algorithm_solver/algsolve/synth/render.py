"""Render a composition into Python through AST substitution.

A composition is JSON:

    {
      "io": {"mode": "functional"}
            | {"mode": "stdin", "cases": "single" | "multi", "parse": <stmts>, "output": <expr>},
      "stages": [{"skeleton": <name>, "inputs": [<names in scope>], "holes": {...}, "output": <name>}, ...],
      "answer": <expr>            # functional mode: returned value over inputs and stage outputs
      "components": [<extra component names>]
    }

Functional mode binds the problem's method parameters as names. Stdin mode
provides ni() (next int), nf() (next float), nxt() (next token as str),
nl(k) (next k ints), and `lines` (all input lines) to the parse statements.
At most three stages. Every hole is checked against the declared grammar and
the composition's total node count is capped; violations raise GrammarError.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass

from . import components as comp
from .grammar import MAX_COMPOSITION_NODES, GrammarError, check_expr, check_identifier, check_stmts
from .skeletons import COMBINE_EXPR, SKELETON_COMPONENTS, SKELETONS

MAX_STAGES = 3

PREAMBLE = """
import sys
from math import gcd, lcm, comb, perm, isqrt, log2, ceil, floor, inf
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict, deque
from heapq import heappush, heappop, heapify
from itertools import accumulate, product, combinations, permutations, pairwise
from functools import cache
sys.setrecursionlimit(100000)
""".strip()


@dataclass
class Rendered:
    source: str
    nodes: int
    families: list[str]
    skeletons: list[str]
    components: list[str]


class _Substitute(ast.NodeTransformer):
    def __init__(self, exprs: dict[str, ast.expr], stmts: dict[str, list[ast.stmt]]) -> None:
        self.exprs = exprs
        self.stmts = stmts

    def visit_Expr(self, node: ast.Expr):
        if isinstance(node.value, ast.Name) and node.value.id.startswith("H_"):
            hole = node.value.id[2:]
            if hole in self.stmts:
                return self.stmts[hole]
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id.startswith("H_"):
            hole = node.id[2:]
            if hole in self.exprs:
                return ast.copy_location(self.exprs[hole], node)
            raise GrammarError(f"hole {hole!r} used as an expression but not provided as one")
        return node


def _parse_expr(text: str) -> ast.expr:
    return ast.parse(text.strip(), mode="eval").body


def _parse_stmts(text: str) -> list[ast.stmt]:
    return ast.parse(text.strip() or "pass").body


def _stage(index: int, stage: dict) -> tuple[ast.FunctionDef, int, str]:
    name = stage.get("skeleton")
    if name not in SKELETONS:
        raise GrammarError(f"unknown skeleton {name!r}")
    spec = SKELETONS[name]
    inputs = stage.get("inputs") or []
    for item in inputs:
        check_identifier(item)
    provided = dict(stage.get("holes") or {})
    unknown = set(provided) - set(spec["holes"])
    if unknown:
        raise GrammarError(f"skeleton {name} has no holes {sorted(unknown)}")
    template = spec["template"]
    exprs: dict[str, ast.expr] = {}
    stmts: dict[str, list[ast.stmt]] = {}
    nodes = 0
    for hole, hole_spec in spec["holes"].items():
        value = provided.get(hole, hole_spec.get("default"))
        if value is None:
            raise GrammarError(f"skeleton {name}: hole {hole!r} is required")
        value = str(value)
        if hole_spec["kind"] == "choice":
            if value not in hole_spec["options"]:
                raise GrammarError(f"skeleton {name}: {hole} must be one of {hole_spec['options']}")
            if hole == "combine":
                template = template.replace("COMBINE(vals)", COMBINE_EXPR[value])
            else:
                template = template.replace(f"H_{hole}", value)
        elif hole_spec["kind"] == "expr":
            nodes += check_expr(value).nodes
            exprs[hole] = _parse_expr(value)
        else:
            nodes += check_stmts(value).nodes
            stmts[hole] = _parse_stmts(value)
    if name == "memo":
        params = ast.literal_eval(str(provided.get("params")))
        if isinstance(params, str):
            params = (params,)
        if not params or not all(isinstance(p, str) and p.isidentifier() for p in params):
            raise GrammarError("memo params must be a tuple of identifier strings")
        stmts["bind_params"] = _parse_stmts(f"{', '.join(params)}, = state")
        exprs.pop("params", None)
    header = f"def stage_{index}({', '.join(inputs)}):\n"
    func = ast.parse(header + template).body[0]
    func = _Substitute(exprs, stmts).visit(func)
    ast.fix_missing_locations(func)
    return func, nodes, spec["family"]


def render(composition: dict | str, *, method: str | None = None, params: list[str] | None = None) -> Rendered:
    if isinstance(composition, str):
        composition = json.loads(composition)
    stages = composition.get("stages") or []
    if not 1 <= len(stages) <= MAX_STAGES:
        raise GrammarError(f"compositions have 1 to {MAX_STAGES} stages")
    io = composition.get("io") or {"mode": "functional"}
    functions, families, total = [], [], 0
    calls: list[ast.stmt] = []
    for k, stage in enumerate(stages):
        func, nodes, family = _stage(k, stage)
        functions.append(func)
        families.append(family)
        total += nodes
        output = stage.get("output") or f"out_{k}"
        check_identifier(output)
        calls.append(ast.parse(f"{output} = stage_{k}({', '.join(stage.get('inputs') or [])})").body[0])
    needed = []
    for stage in stages:
        needed += SKELETON_COMPONENTS.get(stage["skeleton"], [])
    needed += composition.get("components") or []
    needed += comp.referenced(json.dumps(composition))
    names = comp.resolve(list(dict.fromkeys(needed)))

    if io.get("mode", "functional") == "functional":
        if not method:
            raise GrammarError("functional rendering needs the method name")
        answer = composition.get("answer")
        if answer is None:
            raise GrammarError("functional compositions need an answer expression")
        total += check_expr(str(answer)).nodes
        body = calls + [ast.Return(value=_parse_expr(str(answer)))]
        method_def = ast.parse(f"def {method}(self, {', '.join(params or [])}):\n    pass").body[0]
        method_def.body = body
        entry = ast.ClassDef(name="Solution", bases=[], keywords=[], body=[method_def], decorator_list=[], type_params=[])
    elif io["mode"] == "stdin":
        parse_src, output_src = str(io.get("parse") or "pass"), io.get("output")
        if output_src is None:
            raise GrammarError("stdin compositions need an output expression")
        total += check_stmts(parse_src).nodes + check_expr(str(output_src)).nodes
        cases = io.get("cases", "single")
        if cases not in ("single", "multi"):
            raise GrammarError("io.cases must be single or multi")
        case_body = _parse_stmts(parse_src) + calls + ast.parse(f"_out.append(str({output_src}))").body
        loop = ast.parse("for _case in range(ni()):\n    pass").body[0]
        loop.body = case_body
        main = ast.parse(
            "def main():\n"
            "    raw = sys.stdin.read()\n"
            "    lines = raw.split('\\n')\n"
            "    _it = iter(raw.split())\n"
            "    nxt = lambda: next(_it)\n"
            "    ni = lambda: int(next(_it))\n"
            "    nf = lambda: float(next(_it))\n"
            "    nl = lambda k: [int(next(_it)) for _ in range(k)]\n"
            "    _out = []\n"
            "    pass\n"
            "    sys.stdout.write('\\n'.join(_out) + '\\n')\n"
        ).body[0]
        main.body[8] = loop if cases == "multi" else case_body  # type: ignore[assignment]
        if cases == "single":
            main.body = main.body[:8] + case_body + main.body[9:]
        entry = main
    else:
        raise GrammarError(f"unknown io mode {io.get('mode')!r}")

    if total > MAX_COMPOSITION_NODES:
        raise GrammarError(f"composition has {total} hole nodes (max {MAX_COMPOSITION_NODES})")
    module = ast.Module(body=functions + [entry], type_ignores=[])
    ast.fix_missing_locations(module)
    parts = [PREAMBLE] + [comp.COMPONENTS[n]["source"] for n in names] + [ast.unparse(module)]
    if io.get("mode", "functional") == "stdin":
        parts.append("main()")
    source = "\n\n".join(parts) + "\n"
    compile(source, "<composition>", "exec")
    return Rendered(source=source, nodes=total, families=families, skeletons=[s["skeleton"] for s in stages],
                    components=names)
