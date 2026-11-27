"""Load explicit spent inputs and independently recover named JavaScript ASTs."""

from collections import deque
from dataclasses import dataclass
import json
import subprocess

from patterns import A2, a2, to_wire
from independent_decode import a2 as reference


@dataclass(frozen=True)
class Document:
    row: dict
    normalized: bytes
    tree: tuple | None
    named_ast: dict | None

    @property
    def id(self):
        return self.row["id"]

    @property
    def lineage(self):
        return self.row["lineage"]


def normalize(rows, sources):
    items = [{"id": str(i), "source": source} for i, source in enumerate(sources)]
    result = subprocess.run(
        ["node", str(A2 / "js_normalize_ast.mjs"), "normalize"],
        input=json.dumps({"items": items}), text=True, capture_output=True, check=True,
    )
    documents = []
    for i, (row, target) in enumerate(zip(rows, json.loads(result.stdout)["results"], strict=True)):
        if target["id"] != str(i):
            raise ValueError("normalizer changed document order")
        ast = target["ir"] if target["supported"] else None
        tree = tuple(map(to_wire, a2.json_ast_to_ir(ast)[0])) if ast is not None else None
        documents.append(Document(row, target["normalized"].encode(), tree, ast))
    return documents


def load_documents(rows):
    paths = [A2.parent / row["rel_path"] for row in rows]
    return normalize(rows, [path.read_text(encoding="utf-8") for path in paths])


class _SymbolStream(reference.AstStreamDecoder):
    """Run A2's standalone scope-aware decoder on the expanded nodes' symbols."""

    def __init__(self):
        super().__init__(None, {}, {k: [] for k in ("bind", "free", "prop", "num", "str")}, 0, [], [])
        self.events = deque()

    def put(self, ctx, symbol):
        self.events.append((ctx, symbol))

    def sym(self, ctx):
        actual, symbol = self.events.popleft()
        # A tuple stores its AST group. Its parent supplies the precise role.
        if actual != ctx and actual != ctx.partition("_")[0]:
            raise ValueError(f"expected AST field {ctx}, received {actual}")
        return symbol


def named_ast(stmts):
    """Recover declaration/reference names solely from a decoded wire document."""
    stream = _SymbolStream()
    pools = a2.Pools([], [], [], [], [])

    def emit(tree):
        if tree[0] != "NODE":
            raise ValueError("unexpanded call in decoded AST")
        _, group, tag, atoms, children = tree
        node = a2.TNode(group, tag, group, atoms, children)
        a2.emit_tnode_local_only(stream, pools, node, emit)

    body = []
    for stmt in stmts:
        emit(stmt)
        body.append(stream.decode_stmt("STMT_TOP"))
        if stream.events:
            raise ValueError("AST fields remain after decoding statement")
    return {"type": "Program", "body": body}


def _render(decoded, expected=None):
    batch = []
    result = []
    for i, tree in enumerate(decoded):
        if isinstance(tree, bytes):
            ast = None
            result.append(tree)
        else:
            ast = named_ast(tree)
            batch.append((i, ast))
            result.append(None)
        if expected is not None and ast != expected[i].named_ast:
            raise ValueError(f"named AST differs for {expected[i].id}")
    for i, source in reference.unparse_asts_batch(batch).items():
        result[i] = source
    return result


def render_documents(decoded):
    return _render(decoded)


def verify_documents(documents, decoded):
    if len(decoded) != len(documents):
        raise ValueError("document count differs")
    sources = _render(decoded, documents)
    for doc, source in zip(documents, sources):
        if doc.normalized != source:
            raise ValueError(f"normalized bytes differ for {doc.id}")
    return sources
