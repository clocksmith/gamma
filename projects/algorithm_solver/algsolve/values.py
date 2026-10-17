"""Turn dataset test expressions into plain data without executing them.

LeetCodeDataset stores tests as Python asserts and statements show examples as
`x = [1,2], k = 3`. Both are parsed with `ast` and evaluated by a small
whitelist: literals, containers, unary minus, + - * // ** on evaluated values
(bounded size), and the dataset helpers list_node([...]) / tree_node([...]),
which become the typed markers the sandbox harness understands. Anything else
raises Unsupported and the caller drops that test (and counts it).
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any

MAX_ELEMENTS = 2_000_000


class Unsupported(ValueError):
    pass


def _size(value: Any) -> int:
    if isinstance(value, (list, tuple, str)):
        return len(value)
    return 1


def evaluate(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, str, bool)) or node.value is None:
            return node.value
        raise Unsupported(f"constant {type(node.value).__name__}")
    if isinstance(node, ast.List):
        return [evaluate(e) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return [evaluate(e) for e in node.elts]
    if isinstance(node, ast.Dict):
        if any(k is None for k in node.keys):
            raise Unsupported("dict unpacking")
        return {"__dict__": [[evaluate(k), evaluate(v)] for k, v in zip(node.keys, node.values)]}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = evaluate(node.operand)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise Unsupported("unary on non-number")
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.BinOp):
        left, right = evaluate(node.left), evaluate(node.right)
        return _binop(node.op, left, right)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
        name = node.func.id
        if name in ("list_node", "tree_node") and len(node.args) == 1:
            inner = evaluate(node.args[0])
            if not isinstance(inner, list):
                raise Unsupported(f"{name} of non-list")
            return {f"__{name}__": inner}
        if name == "float" and len(node.args) == 1:
            value = evaluate(node.args[0])
            if value in ("inf", "-inf"):
                return {"__float__": value}
            return float(value)
    if isinstance(node, ast.Name) and node.id in ("inf", "None", "True", "False"):
        return {"inf": {"__float__": "inf"}, "None": None, "True": True, "False": False}[node.id]
    raise Unsupported(type(node).__name__)


def _binop(op: ast.operator, left: Any, right: Any) -> Any:
    numbers = (int, float)
    if isinstance(op, ast.Pow):
        if isinstance(left, int) and isinstance(right, int) and 0 <= right <= 64 and abs(left) <= 10**6:
            return left**right
        raise Unsupported("pow")
    if isinstance(op, ast.Mult):
        if isinstance(left, (list, str)) and isinstance(right, int):
            left, right = left, right
        elif isinstance(right, (list, str)) and isinstance(left, int):
            left, right = right, left
        elif isinstance(left, numbers) and isinstance(right, numbers):
            return left * right
        else:
            raise Unsupported("mult types")
        if right < 0 or _size(left) * right > MAX_ELEMENTS:
            raise Unsupported("repetition too large")
        return left * right
    if isinstance(op, ast.Add):
        if type(left) is type(right) and isinstance(left, (list, str)):
            if _size(left) + _size(right) > MAX_ELEMENTS:
                raise Unsupported("concatenation too large")
            return left + right
        if isinstance(left, numbers) and isinstance(right, numbers):
            return left + right
        raise Unsupported("add types")
    if isinstance(op, ast.Sub) and isinstance(left, numbers) and isinstance(right, numbers):
        return left - right
    if isinstance(op, ast.FloorDiv) and isinstance(left, int) and isinstance(right, int) and right:
        return left // right
    raise Unsupported(type(op).__name__)


def parse_value(text: str) -> Any:
    try:
        return evaluate(ast.parse(text.strip(), mode="eval").body)
    except SyntaxError as exc:
        raise Unsupported(f"syntax: {exc.msg}") from None


def parse_call_arguments(text: str) -> tuple[list[Any], dict[str, Any]]:
    """Parse `a = 1, b = [2]` (statement examples) into args/kwargs."""
    try:
        call = ast.parse(f"f({text.strip()})", mode="eval").body
    except SyntaxError as exc:
        raise Unsupported(f"syntax: {exc.msg}") from None
    assert isinstance(call, ast.Call)
    return [evaluate(a) for a in call.args], {k.arg: evaluate(k.value) for k in call.keywords if k.arg}


def canonical_tree(items: list[Any]) -> list[Any]:
    """Rebuild a LeetCode level-order list the way the harness serializes it."""
    if not items or items[0] is None:
        return []
    nodes = [{"val": items[0], "left": None, "right": None}]
    root, queue, i = nodes[0], [nodes[0]], 1
    while queue and i < len(items):
        node = queue.pop(0)
        for side in ("left", "right"):
            if i < len(items) and items[i] is not None:
                child = {"val": items[i], "left": None, "right": None}
                node[side] = child
                queue.append(child)
            i += 1
    out, queue = [], [root]
    while queue:
        node = queue.pop(0)
        if node is None:
            out.append(None)
            continue
        out.append(node["val"])
        queue.extend((node["left"], node["right"]))
    while out and out[-1] is None:
        out.pop()
    return out


def canonicalize(value: Any) -> Any:
    """Normalize expected values to the harness's serialization."""
    if isinstance(value, dict):
        if set(value) == {"__tree_node__"}:
            tree = canonical_tree(value["__tree_node__"])
            return {"__tree_node__": tree} if tree else None
        if set(value) == {"__list_node__"}:
            items = [canonicalize(v) for v in value["__list_node__"]]
            return {"__list_node__": items} if items else None
        if set(value) == {"__float__"}:
            return value
        if set(value) == {"__dict__"}:
            pairs = [[canonicalize(k), canonicalize(x)] for k, x in value["__dict__"]]
            return {"__dict__": sorted(pairs, key=lambda kv: json.dumps(kv[0], sort_keys=True))}
        return {k: canonicalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    return value


# --- starter-code signatures -------------------------------------------------

def _stub_tree(starter_code: str) -> ast.Module:
    """Parse starter code whose method bodies are empty."""
    try:
        return ast.parse(starter_code.rstrip())
    except SyntaxError:
        pass
    filled = re.sub(r"^(\s*def [^\n]*:)[ \t]*$", r"\1 pass", starter_code.rstrip(), flags=re.M)
    try:
        return ast.parse(filled)
    except SyntaxError as exc:
        raise Unsupported(f"starter code does not parse: {exc.msg}") from None


def _find_method(starter_code: str, method: str) -> ast.FunctionDef:
    for node in ast.walk(_stub_tree(starter_code)):
        if isinstance(node, ast.FunctionDef) and node.name == method:
            return node
    raise Unsupported(f"method {method} not found in starter code")


def signature(starter_code: str, method: str) -> list[tuple[str, str]]:
    """Return [(param, annotation_text)] for Solution.method in starter code."""
    node = _find_method(starter_code, method)
    return [(p.arg, ast.unparse(p.annotation) if p.annotation else "") for p in node.args.args[1:]]


def return_annotation(starter_code: str, method: str) -> str:
    try:
        node = _find_method(starter_code, method)
    except Unsupported:
        return ""
    return ast.unparse(node.returns) if node.returns else ""


def wrap_for_annotation(value: Any, annotation: str) -> Any:
    """Statement examples show linked lists/trees as plain lists."""
    annotation = annotation.replace(" ", "")
    if not isinstance(value, list):
        return value
    for prefix in ("List[", "list["):
        if annotation.startswith(prefix) and annotation.endswith("]"):
            inner = annotation[len(prefix):-1]
            if "ListNode" in inner or "TreeNode" in inner:
                return [wrap_for_annotation(v, inner) for v in value]
            return value
    if "ListNode" in annotation:
        return {"__list_node__": value}
    if "TreeNode" in annotation:
        return {"__tree_node__": value}
    return value


def order_arguments(params: list[tuple[str, str]], args: list[Any], kwargs: dict[str, Any]) -> list[Any]:
    """Map positional + keyword arguments onto the declared parameter order."""
    names = [name for name, _ in params]
    if len(args) > len(names):
        raise Unsupported("too many positional arguments")
    ordered = list(args)
    for name in names[len(args):]:
        if name not in kwargs:
            raise Unsupported(f"missing argument {name}")
        ordered.append(kwargs[name])
    extra = set(kwargs) - set(names[len(args):])
    if extra:
        raise Unsupported(f"unknown arguments {sorted(extra)}")
    return ordered
