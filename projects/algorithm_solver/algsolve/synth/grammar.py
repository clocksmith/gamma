"""The declared composition grammar: what a hole may contain.

A composition fills typed holes in skeletons. Holes hold either an
expression or a short block of simple statements, both validated against an
AST whitelist with size caps. No function or class definitions, no imports,
no while loops, no attribute access except whitelisted methods, and at most
one generator per comprehension. These bounds are what "outside the declared
grammar" means: a problem whose solution needs more than this (a new
primitive, a new control structure, an unbounded recurrence) is outside it.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

MAX_EXPR_NODES = 60
MAX_STMTS = 6
MAX_STMT_NODES = 80
MAX_COMPOSITION_NODES = 320

ALLOWED_CALLS = frozenset({
    "min", "max", "abs", "len", "sum", "sorted", "reversed", "range", "enumerate", "zip", "any", "all",
    "int", "str", "list", "tuple", "set", "dict", "bool", "ord", "chr", "pow", "divmod", "map", "filter",
    "gcd", "lcm", "comb", "perm", "isqrt", "log2", "ceil", "floor", "bisect_left", "bisect_right",
    "Counter", "defaultdict", "deque", "heappush", "heappop", "accumulate", "product", "combinations",
    "permutations", "pairwise", "isinstance", "f", "ni", "nf", "nxt", "nl", "float", "round", "bin",
})
ALLOWED_METHODS = frozenset({
    "append", "appendleft", "pop", "popleft", "add", "discard", "remove", "get", "items", "keys", "values",
    "count", "index", "split", "strip", "join", "lower", "upper", "isdigit", "isalpha", "startswith",
    "endswith", "find", "replace", "most_common", "update", "extend", "sort", "copy", "setdefault",
    "bit_count",
})
_EXPR_NODES = (
    ast.Expression, ast.Name, ast.Load, ast.Store, ast.Constant, ast.BinOp, ast.UnaryOp, ast.BoolOp,
    ast.Compare, ast.IfExp, ast.Subscript, ast.Slice, ast.Tuple, ast.List, ast.Set, ast.Dict, ast.Call,
    ast.keyword, ast.Attribute, ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp,
    ast.comprehension, ast.Starred, ast.Lambda, ast.arguments, ast.arg,
    ast.operator, ast.unaryop, ast.boolop, ast.cmpop, ast.expr_context,
)
_STMT_NODES = _EXPR_NODES + (ast.Module, ast.Assign, ast.AugAssign, ast.Expr, ast.If, ast.Pass, ast.For, ast.Break,
                             ast.Continue)


class GrammarError(ValueError):
    pass


@dataclass(frozen=True)
class HoleCheck:
    kind: str
    nodes: int


def _count(tree: ast.AST) -> int:
    return sum(1 for node in ast.walk(tree) if not isinstance(node, (ast.Load, ast.Store, ast.expr_context,
                                                                       ast.operator, ast.unaryop, ast.boolop,
                                                                       ast.cmpop)))


def _check_nodes(tree: ast.AST, allowed: tuple, *, for_depth: int = 0) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise GrammarError(f"construct not in grammar: {type(node).__name__}")
        if isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)) and len(node.generators) > 1:
            raise GrammarError("comprehensions may use one generator")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id not in ALLOWED_CALLS and not func.id.startswith("c_"):
                    raise GrammarError(f"call not in grammar: {func.id}")
            elif isinstance(func, ast.Attribute):
                if func.attr not in ALLOWED_METHODS and not func.attr.startswith("c_"):
                    raise GrammarError(f"method not in grammar: .{func.attr}")
            else:
                raise GrammarError("only named calls are in the grammar")
        if isinstance(node, ast.Attribute) and not isinstance(getattr(node, "ctx", None), ast.Load):
            raise GrammarError("attribute assignment is not in the grammar")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise GrammarError("dunder attributes are not in the grammar")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise GrammarError("dunder names are not in the grammar")
        if isinstance(node, ast.Lambda) and _count(node) > 25:
            raise GrammarError("lambda too large")


def check_expr(source: str) -> HoleCheck:
    try:
        tree = ast.parse(source.strip(), mode="eval")
    except SyntaxError as exc:
        raise GrammarError(f"expression does not parse: {exc.msg}") from None
    _check_nodes(tree, _EXPR_NODES)
    nodes = _count(tree)
    if nodes > MAX_EXPR_NODES:
        raise GrammarError(f"expression has {nodes} nodes (max {MAX_EXPR_NODES})")
    return HoleCheck("expr", nodes)


def check_stmts(source: str) -> HoleCheck:
    try:
        tree = ast.parse(source.strip() or "pass", mode="exec")
    except SyntaxError as exc:
        raise GrammarError(f"statements do not parse: {exc.msg}") from None
    _check_nodes(tree, _STMT_NODES)
    flat = [n for n in ast.walk(tree) if isinstance(n, ast.stmt)]
    if len(flat) > MAX_STMTS:
        raise GrammarError(f"{len(flat)} statements (max {MAX_STMTS})")
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            inner = [n for n in ast.walk(node) if isinstance(n, ast.For) and n is not node]
            if inner:
                raise GrammarError("nested for loops are not in the grammar")
    nodes = _count(tree)
    if nodes > MAX_STMT_NODES:
        raise GrammarError(f"statements have {nodes} nodes (max {MAX_STMT_NODES})")
    return HoleCheck("stmts", nodes)


def check_identifier(name: str) -> HoleCheck:
    if not name.isidentifier() or name.startswith("__"):
        raise GrammarError(f"not a plain identifier: {name!r}")
    return HoleCheck("name", 1)
