#!/usr/bin/env python3
"""Core AST IR, 32-bit exact integer arithmetic coder, exact 8-cyclic-register-shift
enumeration (no FFT/NTT), and unified depth-1 / recursive frame learner for BITS A2.

Shared across Arms 2 (max_depth=0), 3 (max_depth=1), and 4 (max_depth=3).
Arm 1 (Flat BITS) uses the exact same AC32 arithmetic coder and varint primitives.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import math
from typing import Any

# ---------------------------------------------------------------------------
# Varint & UTF-8 Primitives
# ---------------------------------------------------------------------------

def encode_varint(n: int) -> bytes:
    if n < 0:
        raise ValueError(f"negative varint: {n}")
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def decode_varint(buf: bytes | memoryview, pos: int) -> tuple[int, int]:
    val = 0
    shift = 0
    n = len(buf)
    while True:
        if pos >= n:
            raise ValueError("varint truncated")
        b = buf[pos]
        pos += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val, pos
        shift += 7
        if shift > 63:
            raise ValueError("varint overflow")


def encode_ustr(s: str) -> bytes:
    b = s.encode("utf-8")
    return encode_varint(len(b)) + b


def decode_ustr(buf: bytes | memoryview, pos: int) -> tuple[str, int]:
    ln, pos = decode_varint(buf, pos)
    if pos + ln > len(buf):
        raise ValueError("ustr truncated")
    return bytes(buf[pos:pos + ln]).decode("utf-8"), pos + ln


# ---------------------------------------------------------------------------
# Exact 32-bit Integer Arithmetic Coder (AC32)
# ---------------------------------------------------------------------------

AC_FULL = 1 << 32
AC_HALF = 1 << 31
AC_QUARTER = 1 << 30
AC_THREE_Q = 3 << 30
AC_MASK = AC_FULL - 1
AC_MAX_TOTAL = 16384


def quantize_weights(counts: list[int], max_total: int = AC_MAX_TOTAL) -> list[int]:
    """Deterministically quantize nonnegative counts into positive integer weights
    summing to <= max_total. Every symbol gets weight >= 1."""
    k = len(counts)
    if k == 0:
        return []
    if k > max_total:
        raise ValueError(f"alphabet size {k} exceeds max_total {max_total}")
    # Floor every count at 1 for smooth positive support
    floored = [max(1, int(c)) for c in counts]
    s = sum(floored)
    if s <= max_total:
        return floored
    budget = max_total - k
    weights = [1] * k
    if budget <= 0:
        return weights
    excess = [c - 1 for c in floored]
    sum_ex = sum(excess)
    if sum_ex == 0:
        return weights
    rem_items = []
    used = 0
    for i, ex in enumerate(excess):
        exact = ex * budget
        q, r = divmod(exact, sum_ex)
        weights[i] += q
        used += q
        rem_items.append((-r, i))
    left = budget - used
    if left > 0:
        rem_items.sort()
        for _, i in rem_items[:left]:
            weights[i] += 1
    assert sum(weights) <= max_total and min(weights) >= 1
    return weights


def build_cum(weights: list[int]) -> list[int]:
    cum = [0] * (len(weights) + 1)
    acc = 0
    for i, w in enumerate(weights):
        if w < 1:
            raise ValueError("non-positive arithmetic weight")
        acc += w
        cum[i + 1] = acc
    if acc > AC_MAX_TOTAL:
        raise ValueError(f"weight total {acc} exceeds {AC_MAX_TOTAL}")
    return cum


def serialize_table(weights: list[int]) -> bytes:
    out = bytearray()
    for w in weights:
        if w < 1:
            raise ValueError("weight < 1")
        out += encode_varint(w - 1)
    return bytes(out)


class BitSink:
    __slots__ = ("out", "cur", "nbits", "total_bits")

    def __init__(self) -> None:
        self.out = bytearray()
        self.cur = 0
        self.nbits = 0
        self.total_bits = 0

    def put_bit(self, b: int) -> None:
        self.cur = (self.cur << 1) | (b & 1)
        self.nbits += 1
        self.total_bits += 1
        if self.nbits == 8:
            self.out.append(self.cur)
            self.cur = 0
            self.nbits = 0

    def finish(self) -> bytes:
        if self.nbits:
            self.out.append((self.cur << (8 - self.nbits)) & 0xFF)
            self.cur = 0
            self.nbits = 0
        return bytes(self.out)


class ArithmeticEncoder:
    __slots__ = ("low", "high", "pending", "sink", "sym_count")

    def __init__(self) -> None:
        self.low = 0
        self.high = AC_MASK
        self.pending = 0
        self.sink = BitSink()
        self.sym_count = 0

    def _emit(self, bit: int) -> None:
        sink = self.sink
        sink.put_bit(bit)
        inv = bit ^ 1
        p = self.pending
        while p > 0:
            sink.put_bit(inv)
            p -= 1
        self.pending = 0

    def encode(self, cum: list[int], sym: int) -> None:
        total = cum[-1]
        rng = self.high - self.low + 1
        self.high = self.low + (rng * cum[sym + 1]) // total - 1
        self.low = self.low + (rng * cum[sym]) // total
        self.sym_count += 1
        while True:
            if self.high < AC_HALF:
                self._emit(0)
                self.low = (self.low << 1) & AC_MASK
                self.high = ((self.high << 1) | 1) & AC_MASK
            elif self.low >= AC_HALF:
                self._emit(1)
                self.low = ((self.low - AC_HALF) << 1) & AC_MASK
                self.high = (((self.high - AC_HALF) << 1) | 1) & AC_MASK
            elif self.low >= AC_QUARTER and self.high < AC_THREE_Q:
                self.pending += 1
                self.low = ((self.low - AC_QUARTER) << 1) & AC_MASK
                self.high = (((self.high - AC_QUARTER) << 1) | 1) & AC_MASK
            else:
                break

    def encode_uniform(self, sym: int, n: int) -> None:
        if n <= 1:
            return
        rng = self.high - self.low + 1
        self.high = self.low + (rng * (sym + 1)) // n - 1
        self.low = self.low + (rng * sym) // n
        self.sym_count += 1
        while True:
            if self.high < AC_HALF:
                self._emit(0)
                self.low = (self.low << 1) & AC_MASK
                self.high = ((self.high << 1) | 1) & AC_MASK
            elif self.low >= AC_HALF:
                self._emit(1)
                self.low = ((self.low - AC_HALF) << 1) & AC_MASK
                self.high = (((self.high - AC_HALF) << 1) | 1) & AC_MASK
            elif self.low >= AC_QUARTER and self.high < AC_THREE_Q:
                self.pending += 1
                self.low = ((self.low - AC_QUARTER) << 1) & AC_MASK
                self.high = (((self.high - AC_QUARTER) << 1) | 1) & AC_MASK
            else:
                break

    def finish(self) -> bytes:
        self.pending += 1
        if self.low < AC_QUARTER:
            self._emit(0)
        else:
            self._emit(1)
        return self.sink.finish()


# ---------------------------------------------------------------------------
# AST Grammar Constants & Context Definitions (MUST match FORMAT.md!)
# ---------------------------------------------------------------------------

EXPR_TAGS = [
    "Reg8", "RegFar", "FreeId", "NumLit", "StrLit", "BoolFalse", "BoolTrue",
    "NullLit", "This", "Super", "BigIntLit", "RegexLit", "Binary", "Logical",
    "Assign", "Unary", "Update", "Cond", "MemberProp", "MemberComp", "Call",
    "New", "ArrayExpr", "ObjectExpr", "ArrowFunc", "FuncExpr", "ClassExpr",
    "Sequence", "Spread", "Template", "TaggedTemplate", "Await", "Yield",
    "MetaProp", "PatInAssign",
]
EXPR_TAG_ID = {t: i for i, t in enumerate(EXPR_TAGS)}
NUM_BASE_EXPR = len(EXPR_TAGS)  # 35

STMT_TAGS = [
    "ExprStmt", "VarDecl", "Block", "If", "Return", "For", "ForOf", "ForIn",
    "While", "DoWhile", "FuncDecl", "ClassDecl", "Break", "Continue", "Throw",
    "Switch", "Try", "Empty", "Labeled", "With", "Debugger", "ImportDecl",
    "ExportNamed", "ExportDefault", "ExportAll",
]
STMT_TAG_ID = {t: i for i, t in enumerate(STMT_TAGS)}
NUM_BASE_STMT = len(STMT_TAGS)  # 25

PAT_TAGS = ["BindCanon", "BindNamed", "ArrayPat", "ObjectPat", "AssignPat", "RestPat"]
PAT_TAG_ID = {t: i for i, t in enumerate(PAT_TAGS)}

VAR_KINDS = ["var", "let", "const"]
VAR_KIND_ID = {v: i for i, v in enumerate(VAR_KINDS)}

BIN_OPS = [
    "+", "-", "*", "/", "%", "<", "<=", ">", ">=", "===", "!==", "==", "!=",
    "&", "|", "^", "<<", ">>", ">>>", "**", "in", "instanceof",
]
BIN_OP_ID = {v: i for i, v in enumerate(BIN_OPS)}

LOG_OPS = ["&&", "||", "??"]
LOG_OP_ID = {v: i for i, v in enumerate(LOG_OPS)}

UN_OPS = ["!", "-", "+", "~", "typeof", "void", "delete"]
UN_OP_ID = {v: i for i, v in enumerate(UN_OPS)}

UPD_OPS = [("++", False), ("++", True), ("--", False), ("--", True)]
UPD_OP_ID = {v: i for i, v in enumerate(UPD_OPS)}

ASN_OPS = [
    "=", "+=", "-=", "*=", "/=", "%=", "**=", "<<=", ">>=", ">>>=",
    "&=", "|=", "^=", "&&=", "||=", "??=",
]
ASN_OP_ID = {v: i for i, v in enumerate(ASN_OPS)}

EXPR_CONTEXTS = [
    "EXPR_STMT", "EXPR_TEST", "EXPR_INIT", "EXPR_ARG", "EXPR_CALLEE",
    "EXPR_LHS", "EXPR_OBJ", "EXPR_PROP_IDX", "EXPR_BIN_L", "EXPR_BIN_R",
    "EXPR_OTHER",
]
STMT_CONTEXTS = ["STMT_TOP", "STMT_BLOCK", "STMT_BRANCH"]

# Exact order of base context tables serialized in A2F1 CodecKind=1 headers!
AUX_CONTEXT_SIZES: list[tuple[str, int]] = [
    ("PAT_DECL", len(PAT_TAGS)),
    ("PAT_PARAM", len(PAT_TAGS)),
    ("REG_SLOT", 8),
    ("VAR_KIND", len(VAR_KINDS)),
    ("BIN_OP", len(BIN_OPS)),
    ("LOG_OP", len(LOG_OPS)),
    ("UN_OP", len(UN_OPS)),
    ("UPD_OP", len(UPD_OPS)),
    ("ASN_OP", len(ASN_OPS)),
    ("LIST_LEN_STMT", 17),
    ("LIST_LEN_ARGS", 9),
    ("LIST_LEN_DECL", 4),
    ("OPT_ELSE", 2),
    ("OPT_INIT", 2),
    ("OPT_RET_ARG", 2),
    ("OPT_CHAIN", 2),
    ("OPT_FLAG", 2),
    ("FOR_INIT_KIND", 3),
    ("OBJ_PROP_KIND", 5),
    ("ARROW_FLAGS", 4),
    ("FUNC_FLAGS", 4),
    ("CLASS_MEM_KIND", 4),
    ("EXPORT_DEF_KIND", 3),
    ("IMPORT_SPEC_KIND", 3),
    ("META_KIND", 2),
    ("INT_ESC_NIBBLE", 17),
]


# ---------------------------------------------------------------------------
# Scope-Register Stack & JSON AST -> Relative-Register IR Conversion
# ---------------------------------------------------------------------------

class ScopeEnv:
    """Deterministic preorder lexical scope & relative-register stack."""
    __slots__ = ("scope_stack", "func_stack", "next_sid", "env", "canon_counter")

    def __init__(self) -> None:
        self.scope_stack = [0]
        self.func_stack = [0]
        self.next_sid = 1
        self.env: list[tuple[str, int]] = []
        self.canon_counter = 0

    def enter_scope(self, is_func: bool) -> None:
        sid = self.next_sid
        self.next_sid += 1
        self.scope_stack.append(sid)
        if is_func:
            self.func_stack.append(sid)
        if len(self.scope_stack) == 2:
            self.canon_counter = 0

    def exit_scope(self, is_func: bool) -> None:
        sid = self.scope_stack.pop()
        if is_func:
            self.func_stack.pop()
        self.env = [pair for pair in self.env if pair[1] != sid]

    def bind(self, name: str, kind: str) -> None:
        owner = self.func_stack[-1] if kind in ("var", "func") else self.scope_stack[-1]
        if kind == "var":
            for nm, ow in self.env:
                if nm == name and ow == owner:
                    return
        self.env.append((name, owner))

    def bind_canon_check(self, name: str, kind: str) -> bool:
        expected = f"v{self.canon_counter}"
        if name == expected:
            self.canon_counter += 1
            self.bind(name, kind)
            return True
        self.bind(name, kind)
        return False

    def lookup(self, name: str) -> int | None:
        n = len(self.env)
        for rel in range(n):
            if self.env[n - 1 - rel][0] == name:
                return rel
        return None


# ---------------------------------------------------------------------------
# Compact Uniform Node Representation for Fast Tree DP & Frame Templates
# ---------------------------------------------------------------------------
# Every EXPR/STMT/PAT node is represented as an immutable Node object with:
#   group: "EXPR" | "STMT" | "PAT"
#   tag: string tag (from EXPR_TAGS / STMT_TAGS / PAT_TAGS)
#   atoms: tuple of non-child scalar metadata (ints/strs/bools/tuples)
#   children: tuple of (child_ctx, child_node) for child EXPR/STMT/PAT nodes
#   extra: optional structured payload for rare compound nodes (ObjectExpr,
#          ClassDecl, ClassExpr, Switch, Try, Template, ImportDecl, ExportNamed,
#          ExportDefault, ObjectPat, ArrayPat, ArrayExpr, FuncDecl, FuncExpr,
#          ArrowFunc, VarDecl, For, ForIn, ForOf).
#
# To keep frame templates 100% clean, fast, and exact:
#   A "frame-eligible" node is ANY EXPR or STMT node whose children are direct
#   (ctx, child_node) pairs (plus simple scalar atoms). That covers ALL major JS
#   expressions & statements: Reg8, RegFar, FreeId, NumLit, StrLit, Bool, Null,
#   This, Binary, Logical, Assign, Unary, Update, Cond, MemberProp, MemberComp,
#   Call, New, Spread, Await, ExprStmt, VarDecl (1-decl!), Block (1..4 stmts),
#   If, Return, For, ForOf, ForIn, While, DoWhile, Throw, Break, Continue, Empty!
#   Complex nodes (ClassDecl, Switch, Try, ObjectExpr, Template, ESM, multi-decl
#   VarDecl, etc.) are STILL 100% context-coded in Arms 2/3/4 AND their child
#   expressions/statements ARE frame-eligible!

SIMPLE_EXPR_TAGS = frozenset([
    "Reg8", "RegFar", "FreeId", "NumLit", "StrLit", "BoolFalse", "BoolTrue",
    "NullLit", "This", "Super", "Binary", "Logical", "Assign", "Unary", "Update",
    "Cond", "MemberProp", "MemberComp", "Call", "New", "Spread", "Await",
    "ArrayExpr", "Sequence",
])

SIMPLE_STMT_TAGS = frozenset([
    "ExprStmt", "VarDecl", "Block", "If", "Return", "For", "ForOf", "ForIn",
    "While", "DoWhile", "Throw", "Break", "Continue", "Empty",
])


@dataclass(frozen=True)
class TNode:
    """Canonical annotated AST node with exact relative register IDs."""
    group: str          # "EXPR" | "STMT" | "PAT" | "AUX"
    tag: str
    ctx: str            # syntactic context this node was entered under
    atoms: tuple = ()   # exact scalar fields
    children: tuple = ()  # tuple of TNode
    frameable: bool = False
    raw_ast: Any = field(default=None, compare=False, hash=False)
    node_id: int = field(default=0, compare=False, hash=False)


def json_ast_to_ir(ast: dict) -> tuple[list[TNode], int]:
    """Convert raw JS AST JSON (from js_normalize_ast.mjs) to canonical TNode list
    with exact preorder relative register resolution."""
    env = ScopeEnv()
    nid = [0]

    def mk(group: str, tag: str, ctx: str, atoms: tuple = (), children: tuple = (),
           frameable: bool = False, raw: Any = None) -> TNode:
        i = nid[0]
        nid[0] += 1
        return TNode(group=group, tag=tag, ctx=ctx, atoms=atoms, children=children,
                     frameable=frameable, raw_ast=raw, node_id=i)

    def conv_pat(p: dict, ctx: str, kind: str) -> TNode:
        t = p["type"]
        if t == "BindId":
            is_canon = env.bind_canon_check(p["name"], kind)
            if is_canon:
                return mk("PAT", "BindCanon", ctx, (), (), False, p)
            return mk("PAT", "BindNamed", ctx, (p["name"],), (), False, p)
        if t == "ArrayPat":
            ch = []
            flags = []
            for el in p["elems"]:
                if el is None:
                    flags.append(0)
                else:
                    flags.append(1)
                    ch.append(conv_pat(el, ctx, kind))
            return mk("PAT", "ArrayPat", ctx, (tuple(flags),), tuple(ch), False, p)
        if t == "ObjectPat":
            specs = []
            ch = []
            for prop in p["props"]:
                if prop["type"] == "RestPat":
                    specs.append(("rest",))
                    ch.append(conv_pat(prop["arg"], ctx, kind))
                else:
                    if prop["computed"]:
                        specs.append(("comp",))
                        ch.append(conv_expr(prop["key"], "EXPR_OTHER"))
                    else:
                        k = prop["key"]
                        specs.append(("key", k["type"], k.get("name") if k["type"] == "Id" else k.get("value", k.get("raw"))))
                    ch.append(conv_pat(prop["value"], ctx, kind))
            return mk("PAT", "ObjectPat", ctx, (tuple(specs),), tuple(ch), False, p)
        if t == "AssignPat":
            l = conv_pat(p["left"], ctx, kind)
            r = conv_expr(p["right"], "EXPR_INIT")
            return mk("PAT", "AssignPat", ctx, (), (l, r), False, p)
        if t == "RestPat":
            a = conv_pat(p["arg"], ctx, kind)
            return mk("PAT", "RestPat", ctx, (), (a,), False, p)
        # Assignment target expression pattern (e.g. MemberProp / Id in destructuring Assign)
        return conv_expr(p, "EXPR_LHS")

    def conv_assign_target_pat(p: dict) -> TNode:
        """Destructuring target on LHS of `=` (references existing vars, does NOT bind).
        All children are converted via conv_expr(..., 'EXPR_LHS') so nested patterns
        uniformly wrap through PatInAssign for unambiguous one-pass decoding."""
        t = p["type"]
        if t == "ArrayPat":
            flags = []
            ch = []
            for el in p["elems"]:
                if el is None:
                    flags.append(0)
                else:
                    flags.append(1)
                    ch.append(conv_expr(el, "EXPR_LHS"))
            return mk("AUX", "AssignArrayPat", "EXPR_LHS", (tuple(flags),), tuple(ch), False, p)
        if t == "ObjectPat":
            specs = []
            ch = []
            for prop in p["props"]:
                if prop["type"] == "RestPat":
                    specs.append(("rest",))
                    ch.append(conv_expr(prop["arg"], "EXPR_LHS"))
                else:
                    if prop["computed"]:
                        specs.append(("comp",))
                        ch.append(conv_expr(prop["key"], "EXPR_OTHER"))
                    else:
                        k = prop["key"]
                        specs.append(("key", k["type"], k.get("name") if k["type"] == "Id" else k.get("value", k.get("raw"))))
                    ch.append(conv_expr(prop["value"], "EXPR_LHS"))
            return mk("AUX", "AssignObjectPat", "EXPR_LHS", (tuple(specs),), tuple(ch), False, p)
        if t == "AssignPat":
            l = conv_expr(p["left"], "EXPR_LHS")
            r = conv_expr(p["right"], "EXPR_INIT")
            return mk("AUX", "AssignDefaultPat", "EXPR_LHS", (), (l, r), False, p)
        if t == "RestPat":
            return mk("AUX", "AssignRestPat", "EXPR_LHS", (), (conv_expr(p["arg"], "EXPR_LHS"),), False, p)
        return conv_expr(p, "EXPR_LHS")

    def conv_class_members(members: list[dict]) -> tuple[tuple, tuple]:
        specs = []
        ch = []
        for m in members:
            mkind = m["kind"]  # method | get | set | field
            k_info = ("comp",) if m["computed"] else (
                "key", m["key"]["type"],
                m["key"].get("name") if m["key"]["type"] == "Id" else m["key"].get("value", m["key"].get("raw")),
            )
            if m["computed"]:
                ch.append(conv_expr(m["key"], "EXPR_OTHER"))
            has_val = m["value"] is not None
            if has_val:
                ch.append(conv_expr(m["value"], "EXPR_INIT" if mkind == "field" else "EXPR_OTHER"))
            specs.append((mkind, bool(m["isStatic"]), bool(m["isAsync"]), bool(m["isGen"]), k_info, has_val))
        return tuple(specs), tuple(ch)

    def conv_expr(e: dict, ctx: str) -> TNode:
        t = e["type"]
        if t == "Id":
            rel = env.lookup(e["name"])
            if rel is not None:
                if rel < 8:
                    return mk("EXPR", "Reg8", ctx, (rel,), (), True, e)
                return mk("EXPR", "RegFar", ctx, (rel,), (), True, e)
            return mk("EXPR", "FreeId", ctx, (e["name"],), (), True, e)
        if t == "NumLit":
            return mk("EXPR", "NumLit", ctx, (e["raw"],), (), True, e)
        if t == "StrLit":
            return mk("EXPR", "StrLit", ctx, (e["value"],), (), True, e)
        if t == "BoolLit":
            return mk("EXPR", "BoolTrue" if e["value"] else "BoolFalse", ctx, (), (), True, e)
        if t == "NullLit":
            return mk("EXPR", "NullLit", ctx, (), (), True, e)
        if t == "This":
            return mk("EXPR", "This", ctx, (), (), True, e)
        if t == "Super":
            return mk("EXPR", "Super", ctx, (), (), True, e)
        if t == "BigIntLit":
            return mk("EXPR", "BigIntLit", ctx, (e["raw"],), (), False, e)
        if t == "RegexLit":
            return mk("EXPR", "RegexLit", ctx, (e["pattern"], e["flags"]), (), False, e)
        if t == "Binary":
            l = conv_expr(e["left"], "EXPR_BIN_L")
            r = conv_expr(e["right"], "EXPR_BIN_R")
            return mk("EXPR", "Binary", ctx, (e["op"],), (l, r), True, e)
        if t == "Logical":
            l = conv_expr(e["left"], "EXPR_BIN_L")
            r = conv_expr(e["right"], "EXPR_BIN_R")
            return mk("EXPR", "Logical", ctx, (e["op"],), (l, r), True, e)
        if t == "Assign":
            l = conv_expr(e["left"], "EXPR_LHS")
            r = conv_expr(e["right"], "EXPR_INIT")
            return mk("EXPR", "Assign", ctx, (e["op"],), (l, r), True, e)
        if t == "Unary":
            a = conv_expr(e["arg"], "EXPR_OTHER")
            return mk("EXPR", "Unary", ctx, (e["op"],), (a,), True, e)
        if t == "Update":
            a = conv_expr(e["arg"], "EXPR_LHS")
            return mk("EXPR", "Update", ctx, (e["op"], bool(e["prefix"])), (a,), True, e)
        if t == "Cond":
            te = conv_expr(e["test"], "EXPR_TEST")
            co = conv_expr(e["cons"], "EXPR_OTHER")
            al = conv_expr(e["alt"], "EXPR_OTHER")
            return mk("EXPR", "Cond", ctx, (), (te, co, al), True, e)
        if t == "MemberProp":
            o = conv_expr(e["obj"], "EXPR_OBJ")
            return mk("EXPR", "MemberProp", ctx, (bool(e["optional"]), e["prop"]), (o,), True, e)
        if t == "MemberComp":
            o = conv_expr(e["obj"], "EXPR_OBJ")
            p = conv_expr(e["prop"], "EXPR_PROP_IDX")
            return mk("EXPR", "MemberComp", ctx, (bool(e["optional"]),), (o, p), True, e)
        if t == "Call":
            c = conv_expr(e["callee"], "EXPR_CALLEE")
            args = tuple(conv_expr(a, "EXPR_ARG") for a in e["args"])
            return mk("EXPR", "Call", ctx, (bool(e["optional"]), len(args)), (c,) + args, True, e)
        if t == "New":
            c = conv_expr(e["callee"], "EXPR_CALLEE")
            args = tuple(conv_expr(a, "EXPR_ARG") for a in e["args"])
            return mk("EXPR", "New", ctx, (len(args),), (c,) + args, True, e)
        if t == "ArrayExpr":
            flags = []
            ch = []
            for el in e["elems"]:
                if el is None:
                    flags.append(0)
                else:
                    flags.append(1)
                    ch.append(conv_expr(el, "EXPR_OTHER"))
            is_simple = all(flags) and len(ch) <= 4
            return mk("EXPR", "ArrayExpr", ctx, (tuple(flags),), tuple(ch), is_simple, e)
        if t == "ObjectExpr":
            specs = []
            ch = []
            for p in e["props"]:
                if p["type"] == "Spread":
                    specs.append(("spread",))
                    ch.append(conv_expr(p["arg"], "EXPR_ARG"))
                else:
                    pkind = "method" if p["method"] else p["kind"]  # init | method | get | set
                    if p["computed"]:
                        specs.append((pkind, "comp"))
                        ch.append(conv_expr(p["key"], "EXPR_OTHER"))
                    else:
                        k = p["key"]
                        specs.append((pkind, "key", k["type"], k.get("name") if k["type"] == "Id" else k.get("value", k.get("raw"))))
                    ch.append(conv_expr(p["value"], "EXPR_OTHER"))
            return mk("EXPR", "ObjectExpr", ctx, (tuple(specs),), tuple(ch), False, e)
        if t == "ArrowFunc":
            env.enter_scope(True)
            params = tuple(conv_pat(p, "PAT_PARAM", "param") for p in e["params"])
            if e["exprBody"]:
                body = (conv_expr(e["body"], "EXPR_OTHER"),)
            else:
                body = tuple(conv_stmt(s, "STMT_BLOCK") for s in e["body"]["body"])
            env.exit_scope(True)
            return mk("EXPR", "ArrowFunc", ctx, (bool(e["isAsync"]), bool(e["exprBody"]), len(params), len(body)),
                      params + body, False, e)
        if t == "FuncExpr":
            env.enter_scope(True)
            has_id = e["id"] is not None
            if has_id:
                env.bind(e["id"], "func")
            params = tuple(conv_pat(p, "PAT_PARAM", "param") for p in e["params"])
            body = tuple(conv_stmt(s, "STMT_BLOCK") for s in e["body"]["body"])
            env.exit_scope(True)
            return mk("EXPR", "FuncExpr", ctx,
                      (bool(e["isAsync"]), bool(e["isGen"]), e["id"], len(params), len(body)),
                      params + body, False, e)
        if t == "ClassExpr":
            env.enter_scope(False)
            if e["id"]:
                env.bind(e["id"], "let")
            ch = []
            has_super = e["superClass"] is not None
            if has_super:
                ch.append(conv_expr(e["superClass"], "EXPR_OTHER"))
            mspecs, mch = conv_class_members(e["members"])
            ch.extend(mch)
            env.exit_scope(False)
            return mk("EXPR", "ClassExpr", ctx, (e["id"], has_super, mspecs), tuple(ch), False, e)
        if t == "Sequence":
            ch = tuple(conv_expr(x, "EXPR_OTHER") for x in e["exprs"])
            return mk("EXPR", "Sequence", ctx, (len(ch),), ch, len(ch) <= 3, e)
        if t == "Spread":
            return mk("EXPR", "Spread", ctx, (), (conv_expr(e["arg"], "EXPR_ARG"),), True, e)
        if t == "Template":
            ch = tuple(conv_expr(x, "EXPR_OTHER") for x in e["exprs"])
            return mk("EXPR", "Template", ctx, (tuple(e["quasis"]),), ch, False, e)
        if t == "TaggedTemplate":
            tag = conv_expr(e["tag"], "EXPR_CALLEE")
            q = conv_expr(e["quasi"], "EXPR_OTHER")
            return mk("EXPR", "TaggedTemplate", ctx, (), (tag, q), False, e)
        if t == "Await":
            return mk("EXPR", "Await", ctx, (), (conv_expr(e["arg"], "EXPR_OTHER"),), True, e)
        if t == "Yield":
            ch = (conv_expr(e["arg"], "EXPR_OTHER"),) if e["arg"] is not None else ()
            return mk("EXPR", "Yield", ctx, (bool(e["delegate"]), e["arg"] is not None), ch, False, e)
        if t == "MetaProp":
            return mk("EXPR", "MetaProp", ctx, (e["meta"], e["prop"]), (), False, e)
        if t in ("ArrayPat", "ObjectPat", "AssignPat", "RestPat"):
            return mk("EXPR", "PatInAssign", ctx, (), (conv_assign_target_pat(e),), False, e)
        raise ValueError(f"Unknown expr AST type: {t}")

    def conv_stmt(s: dict, ctx: str) -> TNode:
        t = s["type"]
        if t == "ExprStmt":
            ex = conv_expr(s["expr"], "EXPR_STMT")
            return mk("STMT", "ExprStmt", ctx, (), (ex,), True, s)
        if t == "VarDecl":
            kind = s["kind"]
            inits_mask = []
            ch = []
            for d in s["decls"]:
                ch.append(conv_pat(d["id"], "PAT_DECL", kind))
                if d["init"] is not None:
                    inits_mask.append(1)
                    ch.append(conv_expr(d["init"], "EXPR_INIT"))
                else:
                    inits_mask.append(0)
            # Frameable if single BindCanon declarator! (So `let _ = <H>;` / `const _ = <H>;` / `let _ = 0;` are frames!)
            is_simple = (len(s["decls"]) == 1 and ch[0].tag == "BindCanon")
            if is_simple:
                # Store BindCanon in atoms and only EXPR init (if any) in children so holes/frames stay strictly EXPR/STMT!
                init_ch = (ch[1],) if inits_mask[0] else ()
                return mk("STMT", "VarDecl", ctx, (kind, tuple(inits_mask), True), init_ch, True, s)
            return mk("STMT", "VarDecl", ctx, (kind, tuple(inits_mask), False), tuple(ch), False, s)
        if t == "Block":
            env.enter_scope(False)
            ch = tuple(conv_stmt(x, "STMT_BLOCK") for x in s["body"])
            env.exit_scope(False)
            return mk("STMT", "Block", ctx, (len(ch),), ch, len(ch) <= 3, s)
        if t == "If":
            te = conv_expr(s["test"], "EXPR_TEST")
            co = conv_stmt(s["cons"], "STMT_BRANCH")
            if s["alt"] is not None:
                al = conv_stmt(s["alt"], "STMT_BRANCH")
                return mk("STMT", "If", ctx, (True,), (te, co, al), True, s)
            return mk("STMT", "If", ctx, (False,), (te, co), True, s)
        if t == "Return":
            if s["arg"] is not None:
                a = conv_expr(s["arg"], "EXPR_ARG")
                return mk("STMT", "Return", ctx, (True,), (a,), True, s)
            return mk("STMT", "Return", ctx, (False,), (), True, s)
        if t == "For":
            env.enter_scope(False)
            ch = []
            if s["init"] is None:
                ik = 0
            elif s["init"]["type"] == "VarDecl":
                ik = 1
                ch.append(conv_stmt(s["init"], "STMT_BLOCK"))
            else:
                ik = 2
                ch.append(conv_expr(s["init"], "EXPR_STMT"))
            ht = s["test"] is not None
            if ht:
                ch.append(conv_expr(s["test"], "EXPR_TEST"))
            hu = s["update"] is not None
            if hu:
                ch.append(conv_expr(s["update"], "EXPR_STMT"))
            b = conv_stmt(s["body"], "STMT_BRANCH")
            ch.append(b)
            env.exit_scope(False)
            return mk("STMT", "For", ctx, (ik, ht, hu), tuple(ch), True, s)
        if t == "ForOf":
            env.enter_scope(False)
            ld = s["left"]["type"] == "VarDecl"
            l = conv_stmt(s["left"], "STMT_BLOCK") if ld else conv_expr(s["left"], "EXPR_LHS")
            r = conv_expr(s["right"], "EXPR_OTHER")
            b = conv_stmt(s["body"], "STMT_BRANCH")
            env.exit_scope(False)
            return mk("STMT", "ForOf", ctx, (bool(s["isAwait"]), ld), (l, r, b), True, s)
        if t == "ForIn":
            env.enter_scope(False)
            ld = s["left"]["type"] == "VarDecl"
            l = conv_stmt(s["left"], "STMT_BLOCK") if ld else conv_expr(s["left"], "EXPR_LHS")
            r = conv_expr(s["right"], "EXPR_OTHER")
            b = conv_stmt(s["body"], "STMT_BRANCH")
            env.exit_scope(False)
            return mk("STMT", "ForIn", ctx, (ld,), (l, r, b), True, s)
        if t == "While":
            te = conv_expr(s["test"], "EXPR_TEST")
            b = conv_stmt(s["body"], "STMT_BRANCH")
            return mk("STMT", "While", ctx, (), (te, b), True, s)
        if t == "DoWhile":
            b = conv_stmt(s["body"], "STMT_BRANCH")
            te = conv_expr(s["test"], "EXPR_TEST")
            return mk("STMT", "DoWhile", ctx, (), (b, te), True, s)
        if t == "FuncDecl":
            if s["id"]:
                env.bind(s["id"], "func")
            env.enter_scope(True)
            params = tuple(conv_pat(p, "PAT_PARAM", "param") for p in s["params"])
            body = tuple(conv_stmt(x, "STMT_BLOCK") for x in s["body"]["body"])
            env.exit_scope(True)
            return mk("STMT", "FuncDecl", ctx,
                      (bool(s["isAsync"]), bool(s["isGen"]), s["id"], len(params), len(body)),
                      params + body, False, s)
        if t == "ClassDecl":
            if s["id"]:
                env.bind(s["id"], "let")
            ch = []
            has_super = s["superClass"] is not None
            if has_super:
                ch.append(conv_expr(s["superClass"], "EXPR_OTHER"))
            mspecs, mch = conv_class_members(s["members"])
            ch.extend(mch)
            return mk("STMT", "ClassDecl", ctx, (s["id"], has_super, mspecs), tuple(ch), False, s)
        if t == "Break":
            return mk("STMT", "Break", ctx, (s["label"],), (), True, s)
        if t == "Continue":
            return mk("STMT", "Continue", ctx, (s["label"],), (), True, s)
        if t == "Throw":
            return mk("STMT", "Throw", ctx, (), (conv_expr(s["arg"], "EXPR_ARG"),), True, s)
        if t == "Switch":
            d = conv_expr(s["disc"], "EXPR_OTHER")
            env.enter_scope(False)
            cspecs = []
            ch = [d]
            for c in s["cases"]:
                ht = c["test"] is not None
                if ht:
                    ch.append(conv_expr(c["test"], "EXPR_OTHER"))
                for cs in c["cons"]:
                    ch.append(conv_stmt(cs, "STMT_BLOCK"))
                cspecs.append((ht, len(c["cons"])))
            env.exit_scope(False)
            return mk("STMT", "Switch", ctx, (tuple(cspecs),), tuple(ch), False, s)
        if t == "Try":
            b = conv_stmt(s["block"], "STMT_BLOCK")
            ch = [b]
            hh = s["handler"] is not None
            hp = False
            hlen = 0
            if hh:
                env.enter_scope(False)
                hp = s["handler"]["param"] is not None
                if hp:
                    ch.append(conv_pat(s["handler"]["param"], "PAT_DECL", "catch"))
                hbody = s["handler"]["body"]["body"]
                hlen = len(hbody)
                for hs in hbody:
                    ch.append(conv_stmt(hs, "STMT_BLOCK"))
                env.exit_scope(False)
            hf = s["finalizer"] is not None
            if hf:
                ch.append(conv_stmt(s["finalizer"], "STMT_BLOCK"))
            return mk("STMT", "Try", ctx, (hh, hp, hlen, hf), tuple(ch), False, s)
        if t == "Empty":
            return mk("STMT", "Empty", ctx, (), (), True, s)
        if t == "Labeled":
            return mk("STMT", "Labeled", ctx, (s["label"],), (conv_stmt(s["body"], "STMT_BLOCK"),), False, s)
        if t == "With":
            o = conv_expr(s["object"], "EXPR_OTHER")
            b = conv_stmt(s["body"], "STMT_BRANCH")
            return mk("STMT", "With", ctx, (), (o, b), False, s)
        if t == "Debugger":
            return mk("STMT", "Debugger", ctx, (), (), False, s)
        if t == "ImportDecl":
            specs = []
            for sp in s["specifiers"]:
                env.bind(sp["local"], "let")
                specs.append((sp["kind"], sp.get("imported", ""), sp["local"]))
            return mk("STMT", "ImportDecl", ctx, (tuple(specs), s["source"]), (), False, s)
        if t == "ExportNamed":
            if s["declaration"] is not None:
                d = conv_stmt(s["declaration"], "STMT_TOP")
                return mk("STMT", "ExportNamed", ctx, (True, (), None), (d,), False, s)
            specs = tuple((sp["local"], sp["exported"]) for sp in s["specifiers"])
            return mk("STMT", "ExportNamed", ctx, (False, specs, s["source"]), (), False, s)
        if t == "ExportDefault":
            d = s["declaration"]
            if d["type"] in ("FuncDecl", "ClassDecl"):
                return mk("STMT", "ExportDefault", ctx, (d["type"],), (conv_stmt(d, "STMT_TOP"),), False, s)
            return mk("STMT", "ExportDefault", ctx, ("Expr",), (conv_expr(d, "EXPR_OTHER"),), False, s)
        if t == "ExportAll":
            return mk("STMT", "ExportAll", ctx, (s["exported"], s["source"]), (), False, s)
        raise ValueError(f"Unknown stmt AST type: {t}")

    stmts = [conv_stmt(s, "STMT_TOP") for s in ast["body"]]
    return stmts, nid[0]


# ---------------------------------------------------------------------------
# Frame Template Representation & Exact 8-Cyclic-Register-Shift Enumeration
# ---------------------------------------------------------------------------
# A Template tree node (`Tpl`) is one of:
#   ("HOLE", group, ctx)                        -- filled from caller/args
#   ("CALL", frame_id, group, sub_shift, args)  -- nested sub-frame call (depth >= 2 only)
#   ("NODE", group, tag, atoms, children)       -- concrete AST node

def tpl_has_regs(tpl: tuple, frames_by_id: dict[tuple[str, int], Any]) -> bool:
    kind = tpl[0]
    if kind == "HOLE":
        return False
    if kind == "CALL":
        _, fid, grp, _, args = tpl
        if frames_by_id[(grp, fid)].has_regs:
            return True
        return any(tpl_has_regs(a, frames_by_id) for a in args)
    # NODE
    _, _, tag, _, children = tpl
    if tag == "Reg8":
        return True
    return any(tpl_has_regs(c, frames_by_id) for c in children)


def tpl_shift_exact(tpl: tuple, delta: int, frames_by_id: dict[tuple[str, int], Any]) -> tuple:
    """Apply exact cyclic register shift +delta (mod 8) to all Reg8 & register-bearing
    sub-frame calls. Explicitly Z/8Z group action (NO FFT/NTT)."""
    delta &= 7
    if delta == 0:
        return tpl
    kind = tpl[0]
    if kind == "HOLE":
        return tpl
    if kind == "CALL":
        _, fid, grp, sub_s, args = tpl
        sub_frame = frames_by_id[(grp, fid)]
        new_sub_s = (sub_s + delta) & 7 if sub_frame.has_regs else 0
        new_args = tuple(tpl_shift_exact(a, delta, frames_by_id) for a in args)
        return ("CALL", fid, grp, new_sub_s, new_args)
    _, grp, tag, atoms, children = tpl
    if tag == "Reg8":
        return ("NODE", grp, tag, ((atoms[0] + delta) & 7,), ())
    new_ch = tuple(tpl_shift_exact(c, delta, frames_by_id) for c in children)
    return ("NODE", grp, tag, atoms, new_ch)


def tpl_canonicalize_shift_exact(tpl: tuple, frames_by_id: dict[tuple[str, int], Any]) -> tuple[tuple, int, int]:
    """Enumerate ALL 8 cyclic register shifts s in 0..7 EXACTLY (no FFT/NTT) and return
    (canonical_template, winning_shift, shift_evals).
    Guarantees: tpl_shift_exact(canonical_template, winning_shift) == tpl."""
    if not tpl_has_regs(tpl, frames_by_id):
        return tpl, 0, 1
    best_tpl = None
    best_key = None
    best_s = 0
    for s in range(8):
        cand = tpl_shift_exact(tpl, (-s) & 7, frames_by_id)
        key = repr(cand)
        if best_key is None or key < best_key:
            best_key = key
            best_tpl = cand
            best_s = s
    return best_tpl, best_s, 8


def tpl_expand_to_flat(tpl: tuple, frames_by_id: dict[tuple[str, int], Any], shift: int = 0) -> tuple:
    """Expand a possibly recursive template into its equivalent flat base-AST template
    (with HOLEs preserved) for fast matching and equivalence checks."""
    kind = tpl[0]
    if kind == "HOLE":
        return tpl
    if kind == "CALL":
        _, fid, grp, sub_s, args = tpl
        sub_frame = frames_by_id[(grp, fid)]
        eff_shift = (shift + sub_s) & 7 if sub_frame.has_regs else 0
        expanded_args = [tpl_expand_to_flat(a, frames_by_id, shift) for a in args]
        arg_idx = [0]

        def subst(node: tuple) -> tuple:
            if node[0] == "HOLE":
                i = arg_idx[0]
                arg_idx[0] += 1
                return expanded_args[i]
            if node[0] == "CALL":
                return subst(tpl_expand_to_flat(node, frames_by_id, 0))
            _, g, t, at, ch = node
            if t == "Reg8":
                return ("NODE", g, t, ((at[0] + eff_shift) & 7,), ())
            return ("NODE", g, t, at, tuple(subst(c) for c in ch))

        return subst(sub_frame.flat_tpl)
    _, grp, tag, atoms, children = tpl
    if tag == "Reg8":
        return ("NODE", grp, tag, ((atoms[0] + shift) & 7,), ())
    return ("NODE", grp, tag, atoms, tuple(tpl_expand_to_flat(c, frames_by_id, shift) for c in children))


def tpl_collect_holes(tpl: tuple, frames_by_id: dict[tuple[str, int], Any]) -> list[tuple[str, str]]:
    """Return ordered list of (group, ctx) for every HOLE in template."""
    out: list[tuple[str, str]] = []

    def walk(x: tuple) -> None:
        if x[0] == "HOLE":
            out.append((x[1], x[2]))
        elif x[0] == "CALL":
            for a in x[4]:
                walk(a)
        else:
            for c in x[4]:
                walk(c)

    walk(tpl)
    return out


def tpl_node_count(flat_tpl: tuple) -> int:
    if flat_tpl[0] == "HOLE":
        return 0
    return 1 + sum(tpl_node_count(c) for c in flat_tpl[4])


def tpl_def_depth(tpl: tuple, frames_by_id: dict[tuple[str, int], Any]) -> int:
    kind = tpl[0]
    if kind == "HOLE":
        return 0
    if kind == "CALL":
        _, fid, grp, _, args = tpl
        d = 1 + frames_by_id[(grp, fid)].def_depth
        for a in args:
            da = tpl_def_depth(a, frames_by_id)
            if da > d:
                d = da
        return d
    mx = 1
    for c in tpl[4]:
        dc = tpl_def_depth(c, frames_by_id)
        if dc > mx:
            mx = dc
    return mx


def tpl_uses_nested_call(tpl: tuple) -> bool:
    if tpl[0] == "CALL":
        return True
    if tpl[0] == "NODE":
        return any(tpl_uses_nested_call(c) for c in tpl[4])
    return False


def tpl_direct_deps(tpl: tuple) -> set[tuple[str, int]]:
    deps: set[tuple[str, int]] = set()

    def walk(x: tuple) -> None:
        if x[0] == "CALL":
            deps.add((x[2], x[1]))
            for a in x[4]:
                walk(a)
        elif x[0] == "NODE":
            for c in x[4]:
                walk(c)

    walk(tpl)
    return deps


@dataclass
class FrameDef:
    group: str          # "EXPR" | "STMT"
    fid: int            # 0..F_E-1 or 0..F_S-1
    order_idx: int      # global topological order 0..F-1
    tpl: tuple          # actual stored template (may contain CALL when max_depth >= 2)
    flat_tpl: tuple     # expanded flat base-AST template for fast matching
    has_regs: bool
    def_depth: int      # 1 for depth-1, 2..D_max for recursive
    holes: list[tuple[str, str]]  # [(group, ctx), ...]
    root_tag: str
    base_node_count: int


# ---------------------------------------------------------------------------
# Context Model & Exact Symbol Emission Helpers
# ---------------------------------------------------------------------------

class Pools:
    def __init__(self, prop_pool: list[str], free_id_pool: list[str], bind_name_pool: list[str],
                 num_pool: list[str], str_pool: list[str]) -> None:
        self.prop_pool = prop_pool
        self.free_id_pool = free_id_pool
        self.bind_name_pool = bind_name_pool
        self.num_pool = num_pool
        self.str_pool = str_pool
        self.prop_idx = {s: i for i, s in enumerate(prop_pool)}
        self.free_id_idx = {s: i for i, s in enumerate(free_id_pool)}
        self.bind_name_idx = {s: i for i, s in enumerate(bind_name_pool)}
        self.num_idx = {s: i for i, s in enumerate(num_pool)}
        self.str_idx = {s: i for i, s in enumerate(str_pool)}

    def serialize(self) -> bytes:
        out = bytearray()
        for lst in (self.prop_pool, self.free_id_pool, self.bind_name_pool, self.num_pool, self.str_pool):
            out += encode_varint(len(lst))
            for s in lst:
                out += encode_ustr(s)
        return bytes(out)


def build_pools(train_irs: list[list[TNode]], max_pool: int = 256) -> Pools:
    """Build deterministic shared literal & identifier pools from training ASTs only."""
    c_prop: Counter[str] = Counter()
    c_free: Counter[str] = Counter()
    c_bind: Counter[str] = Counter()
    c_num: Counter[str] = Counter()
    c_str: Counter[str] = Counter()

    def walk(node: TNode) -> None:
        t = node.tag
        a = node.atoms
        if t == "FreeId":
            c_free[a[0]] += 1
        elif t == "NumLit":
            c_num[a[0]] += 1
        elif t == "StrLit":
            c_str[a[0]] += 1
        elif t == "MemberProp":
            c_prop[a[1]] += 1
        elif t == "MetaProp":
            c_prop[a[1]] += 1
        elif t == "BindNamed":
            c_bind[a[0]] += 1
        elif t in ("FuncDecl", "FuncExpr"):
            if a[2] is not None:
                c_bind[a[2]] += 1
        elif t in ("ClassDecl", "ClassExpr"):
            if a[0] is not None:
                c_bind[a[0]] += 1
            for spec in a[2]:
                k_info = spec[4]
                if k_info[0] == "key" and k_info[1] == "Id":
                    c_prop[k_info[2]] += 1
        elif t in ("Break", "Continue", "Labeled"):
            if a[0] is not None:
                c_bind[a[0]] += 1
        elif t == "ObjectExpr":
            for spec in a[0]:
                if spec[0] != "spread" and spec[1] == "key" and spec[2] == "Id":
                    c_prop[spec[3]] += 1
        elif t == "ImportDecl":
            c_str[a[1]] += 1
            for _, imp, loc in a[0]:
                if imp:
                    c_bind[imp] += 1
                c_bind[loc] += 1
        elif t == "ExportNamed":
            if not a[0]:
                for loc, exp in a[1]:
                    c_bind[loc] += 1
                    c_bind[exp] += 1
                if a[2] is not None:
                    c_str[a[2]] += 1
        elif t == "ExportAll":
            if a[0] is not None:
                c_bind[a[0]] += 1
            c_str[a[1]] += 1
        for ch in node.children:
            walk(ch)

    for stmts in train_irs:
        for s in stmts:
            walk(s)

    def top_profitable(counter: Counter[str], cap: int) -> list[str]:
        # Include strings occurring >= 4 times (clearly profitable vs inline bytes) sorted deterministically
        items = [s for s, cnt in counter.items() if cnt >= 4 and len(s.encode("utf-8")) <= 64]
        items.sort(key=lambda s: (-counter[s], s))
        return items[:cap]

    return Pools(
        prop_pool=top_profitable(c_prop, max_pool),
        free_id_pool=top_profitable(c_free, max_pool),
        bind_name_pool=top_profitable(c_bind, max_pool),
        num_pool=top_profitable(c_num, max_pool),
        str_pool=top_profitable(c_str, max_pool),
    )


def all_base_context_specs(pools: Pools, has_frames: bool) -> list[tuple[str, int]]:
    specs: list[tuple[str, int]] = [("FILE_MODE", 2)]
    expr_sz = NUM_BASE_EXPR + (1 if has_frames else 0)
    stmt_sz = NUM_BASE_STMT + (1 if has_frames else 0)
    for c in EXPR_CONTEXTS:
        specs.append((c, expr_sz))
    for c in STMT_CONTEXTS:
        specs.append((c, stmt_sz))
    specs.extend(AUX_CONTEXT_SIZES)
    specs.append(("PROP_NAME", len(pools.prop_pool) + 1))
    specs.append(("FREE_ID", len(pools.free_id_pool) + 1))
    specs.append(("BIND_NAME", len(pools.bind_name_pool) + 1))
    specs.append(("NUM_LIT", len(pools.num_pool) + 1))
    specs.append(("STR_LIT", len(pools.str_pool) + 1))
    specs.append(("INLINE_BYTE", 256))
    return specs


# ---------------------------------------------------------------------------
# Exact Symbol Emitter (Used for Counting, Costing, and Arithmetic Encoding!)
# ---------------------------------------------------------------------------

class SymbolSink:
    """Protocol for either counting symbols, measuring exact -log2 bits, or AC32 encoding."""
    def put(self, ctx: str, sym: int) -> None:
        raise NotImplementedError

    def put_uniform(self, sym: int, n: int) -> None:
        raise NotImplementedError


class CountSink(SymbolSink):
    def __init__(self, specs: list[tuple[str, int]]) -> None:
        self.counts = {ctx: [0] * sz for ctx, sz in specs}

    def put(self, ctx: str, sym: int) -> None:
        self.counts[ctx][sym] += 1

    def put_uniform(self, sym: int, n: int) -> None:
        pass


class BitCostSink(SymbolSink):
    __slots__ = ("costs", "bits", "switch_bits", "frame_id_bits", "shift_bits")

    def __init__(self, costs: dict[str, list[float]]) -> None:
        self.costs = costs
        self.bits = 0.0
        self.switch_bits = 0.0
        self.frame_id_bits = 0.0
        self.shift_bits = 0.0

    def put(self, ctx: str, sym: int) -> None:
        b = self.costs[ctx][sym]
        self.bits += b
        if ctx in ("EXPR_FRAME_ID", "STMT_FRAME_ID"):
            self.frame_id_bits += b
        elif ctx == "REG_SHIFT":
            self.shift_bits += b
        elif ctx in EXPR_CONTEXTS and sym == NUM_BASE_EXPR:
            self.switch_bits += b
        elif ctx in STMT_CONTEXTS and sym == NUM_BASE_STMT:
            self.switch_bits += b

    def put_uniform(self, sym: int, n: int) -> None:
        if n > 1:
            self.bits += math.log2(n)


class AC32Sink(SymbolSink):
    __slots__ = ("enc", "cums")

    def __init__(self, enc: ArithmeticEncoder, cums: dict[str, list[int]]) -> None:
        self.enc = enc
        self.cums = cums

    def put(self, ctx: str, sym: int) -> None:
        self.enc.encode(self.cums[ctx], sym)

    def put_uniform(self, sym: int, n: int) -> None:
        self.enc.encode_uniform(sym, n)


def emit_uint(sink: SymbolSink, val: int) -> None:
    """Encode arbitrary nonnegative integer in base-16 nibbles (0..15, 16=STOP)."""
    if val < 0:
        raise ValueError("negative uint")
    if val == 0:
        sink.put("INT_ESC_NIBBLE", 16)
        return
    nibbles = []
    v = val
    while v > 0:
        nibbles.append(v & 15)
        v >>= 4
    for nb in reversed(nibbles):
        sink.put("INT_ESC_NIBBLE", nb)
    sink.put("INT_ESC_NIBBLE", 16)


def emit_list_len(sink: SymbolSink, ctx: str, limit: int, val: int) -> None:
    if val < limit:
        sink.put(ctx, val)
    else:
        sink.put(ctx, limit)
        emit_uint(sink, val - limit)


def emit_inline_str(sink: SymbolSink, s: str) -> None:
    b = s.encode("utf-8")
    emit_uint(sink, len(b))
    for byte in b:
        sink.put("INLINE_BYTE", byte)


def emit_pooled(sink: SymbolSink, ctx: str, idx_map: dict[str, int], s: str) -> None:
    idx = idx_map.get(s)
    if idx is not None:
        sink.put(ctx, idx)
    else:
        sink.put(ctx, len(idx_map))
        emit_inline_str(sink, s)


def emit_key_spec(sink: SymbolSink, pools: Pools, k_info: tuple) -> None:
    # k_info = ("key", key_type, val) where key_type in ("Id", "StrLit", "NumLit", "BigIntLit")
    kt = k_info[1]
    val = k_info[2]
    if kt == "Id":
        sink.put("OBJ_PROP_KIND", 0)
        emit_pooled(sink, "PROP_NAME", pools.prop_idx, val)
    elif kt == "StrLit":
        sink.put("OBJ_PROP_KIND", 1)
        emit_pooled(sink, "STR_LIT", pools.str_idx, val)
    elif kt == "NumLit":
        sink.put("OBJ_PROP_KIND", 2)
        emit_pooled(sink, "NUM_LIT", pools.num_idx, val)
    else:
        sink.put("OBJ_PROP_KIND", 3)
        emit_inline_str(sink, val)


def emit_tnode_local_only(sink: SymbolSink, pools: Pools, node: TNode, emit_child_fn) -> None:
    """Emit a single TNode's tag, scalar fields, and invoke emit_child_fn(child) for children.
    Guarantees 100% identical emission order between Arm 2, Arm 3, Arm 4, and independent_decode.py!"""
    g = node.group
    t = node.tag
    a = node.atoms
    ch = node.children

    if g == "PAT":
        sink.put(node.ctx, PAT_TAG_ID[t])
        if t == "BindCanon":
            return
        if t == "BindNamed":
            emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, a[0])
            return
        if t == "ArrayPat":
            flags = a[0]
            emit_list_len(sink, "LIST_LEN_ARGS", 8, len(flags))
            ci = 0
            for f in flags:
                sink.put("OPT_FLAG", f)
                if f:
                    emit_child_fn(ch[ci])
                    ci += 1
            return
        if t == "ObjectPat":
            specs = a[0]
            emit_list_len(sink, "LIST_LEN_ARGS", 8, len(specs))
            ci = 0
            for sp in specs:
                if sp[0] == "rest":
                    sink.put("OPT_FLAG", 1)
                    emit_child_fn(ch[ci])
                    ci += 1
                else:
                    sink.put("OPT_FLAG", 0)
                    if sp[0] == "comp":
                        sink.put("OBJ_PROP_KIND", 4)
                        emit_child_fn(ch[ci])
                        ci += 1
                    else:
                        emit_key_spec(sink, pools, sp)
                    emit_child_fn(ch[ci])
                    ci += 1
            return
        if t == "AssignPat":
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
            return
        if t == "RestPat":
            emit_child_fn(ch[0])
            return
        raise ValueError(f"Unknown PAT tag {t}")

    if g == "AUX":
        # Destructuring target patterns inside PatInAssign
        if t == "AssignArrayPat":
            sink.put("PAT_DECL", PAT_TAG_ID["ArrayPat"])
            flags = a[0]
            emit_list_len(sink, "LIST_LEN_ARGS", 8, len(flags))
            ci = 0
            for f in flags:
                sink.put("OPT_FLAG", f)
                if f:
                    emit_child_fn(ch[ci])
                    ci += 1
            return
        if t == "AssignObjectPat":
            sink.put("PAT_DECL", PAT_TAG_ID["ObjectPat"])
            specs = a[0]
            emit_list_len(sink, "LIST_LEN_ARGS", 8, len(specs))
            ci = 0
            for sp in specs:
                if sp[0] == "rest":
                    sink.put("OPT_FLAG", 1)
                    emit_child_fn(ch[ci])
                    ci += 1
                else:
                    sink.put("OPT_FLAG", 0)
                    if sp[0] == "comp":
                        sink.put("OBJ_PROP_KIND", 4)
                        emit_child_fn(ch[ci])
                        ci += 1
                    else:
                        emit_key_spec(sink, pools, sp)
                    emit_child_fn(ch[ci])
                    ci += 1
            return
        if t == "AssignDefaultPat":
            sink.put("PAT_DECL", PAT_TAG_ID["AssignPat"])
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
            return
        if t == "AssignRestPat":
            sink.put("PAT_DECL", PAT_TAG_ID["RestPat"])
            emit_child_fn(ch[0])
            return
        raise ValueError(f"Unknown AUX tag {t}")

    if g == "EXPR":
        sink.put(node.ctx, EXPR_TAG_ID[t])
        if t == "Reg8":
            sink.put("REG_SLOT", a[0])
        elif t == "RegFar":
            emit_uint(sink, a[0] - 8)
        elif t == "FreeId":
            emit_pooled(sink, "FREE_ID", pools.free_id_idx, a[0])
        elif t == "NumLit":
            emit_pooled(sink, "NUM_LIT", pools.num_idx, a[0])
        elif t == "StrLit":
            emit_pooled(sink, "STR_LIT", pools.str_idx, a[0])
        elif t in ("BoolFalse", "BoolTrue", "NullLit", "This", "Super"):
            pass
        elif t == "BigIntLit":
            emit_inline_str(sink, a[0])
        elif t == "RegexLit":
            emit_inline_str(sink, a[0])
            emit_inline_str(sink, a[1])
        elif t == "Binary":
            sink.put("BIN_OP", BIN_OP_ID[a[0]])
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
        elif t == "Logical":
            sink.put("LOG_OP", LOG_OP_ID[a[0]])
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
        elif t == "Assign":
            sink.put("ASN_OP", ASN_OP_ID[a[0]])
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
        elif t == "Unary":
            sink.put("UN_OP", UN_OP_ID[a[0]])
            emit_child_fn(ch[0])
        elif t == "Update":
            sink.put("UPD_OP", UPD_OP_ID[(a[0], a[1])])
            emit_child_fn(ch[0])
        elif t == "Cond":
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
            emit_child_fn(ch[2])
        elif t == "MemberProp":
            sink.put("OPT_CHAIN", 1 if a[0] else 0)
            emit_child_fn(ch[0])
            emit_pooled(sink, "PROP_NAME", pools.prop_idx, a[1])
        elif t == "MemberComp":
            sink.put("OPT_CHAIN", 1 if a[0] else 0)
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
        elif t == "Call":
            sink.put("OPT_CHAIN", 1 if a[0] else 0)
            emit_child_fn(ch[0])
            emit_list_len(sink, "LIST_LEN_ARGS", 8, a[1])
            for c in ch[1:]:
                emit_child_fn(c)
        elif t == "New":
            emit_child_fn(ch[0])
            emit_list_len(sink, "LIST_LEN_ARGS", 8, a[0])
            for c in ch[1:]:
                emit_child_fn(c)
        elif t == "ArrayExpr":
            flags = a[0]
            emit_list_len(sink, "LIST_LEN_ARGS", 8, len(flags))
            ci = 0
            for f in flags:
                sink.put("OPT_FLAG", f)
                if f:
                    emit_child_fn(ch[ci])
                    ci += 1
        elif t == "ObjectExpr":
            specs = a[0]
            emit_list_len(sink, "LIST_LEN_ARGS", 8, len(specs))
            ci = 0
            kind_map = {"init": 0, "method": 1, "get": 2, "set": 3, "spread": 4}
            for sp in specs:
                sink.put("OBJ_PROP_KIND", kind_map[sp[0]])
                if sp[0] == "spread":
                    emit_child_fn(ch[ci])
                    ci += 1
                else:
                    if sp[1] == "comp":
                        sink.put("OBJ_PROP_KIND", 4)
                        emit_child_fn(ch[ci])
                        ci += 1
                    else:
                        emit_key_spec(sink, pools, ("key", sp[2], sp[3]))
                    emit_child_fn(ch[ci])
                    ci += 1
        elif t == "ArrowFunc":
            is_async, expr_body, nparams, nbody = a
            sink.put("ARROW_FLAGS", (2 if is_async else 0) + (1 if expr_body else 0))
            emit_list_len(sink, "LIST_LEN_ARGS", 8, nparams)
            for c in ch[:nparams]:
                emit_child_fn(c)
            if expr_body:
                emit_child_fn(ch[nparams])
            else:
                emit_list_len(sink, "LIST_LEN_STMT", 16, nbody)
                for c in ch[nparams:]:
                    emit_child_fn(c)
        elif t == "FuncExpr":
            is_async, is_gen, fid, nparams, nbody = a
            sink.put("FUNC_FLAGS", (2 if is_async else 0) + (1 if is_gen else 0))
            sink.put("OPT_FLAG", 1 if fid is not None else 0)
            if fid is not None:
                emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, fid)
            emit_list_len(sink, "LIST_LEN_ARGS", 8, nparams)
            for c in ch[:nparams]:
                emit_child_fn(c)
            emit_list_len(sink, "LIST_LEN_STMT", 16, nbody)
            for c in ch[nparams:]:
                emit_child_fn(c)
        elif t == "ClassExpr":
            cid, has_super, mspecs = a
            sink.put("OPT_FLAG", 1 if cid is not None else 0)
            if cid is not None:
                emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, cid)
            sink.put("OPT_FLAG", 1 if has_super else 0)
            ci = 0
            if has_super:
                emit_child_fn(ch[ci])
                ci += 1
            emit_class_members(sink, pools, mspecs, ch, ci, emit_child_fn)
        elif t == "Sequence":
            emit_list_len(sink, "LIST_LEN_ARGS", 8, a[0])
            for c in ch:
                emit_child_fn(c)
        elif t == "Spread":
            emit_child_fn(ch[0])
        elif t == "Template":
            quasis = a[0]
            emit_list_len(sink, "LIST_LEN_ARGS", 8, len(ch))
            for i, q in enumerate(quasis):
                emit_inline_str(sink, q)
                if i < len(ch):
                    emit_child_fn(ch[i])
        elif t == "TaggedTemplate":
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
        elif t == "Await":
            emit_child_fn(ch[0])
        elif t == "Yield":
            sink.put("OPT_FLAG", 1 if a[0] else 0)
            sink.put("OPT_FLAG", 1 if a[1] else 0)
            if a[1]:
                emit_child_fn(ch[0])
        elif t == "MetaProp":
            sink.put("META_KIND", 0 if a[0] == "new" else 1)
            emit_pooled(sink, "PROP_NAME", pools.prop_idx, a[1])
        elif t == "PatInAssign":
            emit_child_fn(ch[0])
        else:
            raise ValueError(f"Unknown EXPR tag {t}")
        return

    if g == "STMT":
        sink.put(node.ctx, STMT_TAG_ID[t])
        if t == "ExprStmt":
            emit_child_fn(ch[0])
        elif t == "VarDecl":
            kind, mask, is_simple = a
            sink.put("VAR_KIND", VAR_KIND_ID[kind])
            emit_list_len(sink, "LIST_LEN_DECL", 3, len(mask))
            if is_simple:
                sink.put("PAT_DECL", PAT_TAG_ID["BindCanon"])
                sink.put("OPT_INIT", mask[0])
                if mask[0]:
                    emit_child_fn(ch[0])
            else:
                ci = 0
                for has_init in mask:
                    emit_child_fn(ch[ci])
                    ci += 1
                    sink.put("OPT_INIT", has_init)
                    if has_init:
                        emit_child_fn(ch[ci])
                        ci += 1
        elif t == "Block":
            emit_list_len(sink, "LIST_LEN_STMT", 16, a[0])
            for c in ch:
                emit_child_fn(c)
        elif t == "If":
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
            sink.put("OPT_ELSE", 1 if a[0] else 0)
            if a[0]:
                emit_child_fn(ch[2])
        elif t == "Return":
            sink.put("OPT_RET_ARG", 1 if a[0] else 0)
            if a[0]:
                emit_child_fn(ch[0])
        elif t == "For":
            ik, ht, hu = a
            sink.put("FOR_INIT_KIND", ik)
            ci = 0
            if ik != 0:
                emit_child_fn(ch[ci])
                ci += 1
            sink.put("OPT_FLAG", 1 if ht else 0)
            if ht:
                emit_child_fn(ch[ci])
                ci += 1
            sink.put("OPT_FLAG", 1 if hu else 0)
            if hu:
                emit_child_fn(ch[ci])
                ci += 1
            emit_child_fn(ch[ci])
        elif t == "ForOf":
            sink.put("OPT_FLAG", 1 if a[0] else 0)
            sink.put("OPT_FLAG", 1 if a[1] else 0)
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
            emit_child_fn(ch[2])
        elif t == "ForIn":
            sink.put("OPT_FLAG", 1 if a[0] else 0)
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
            emit_child_fn(ch[2])
        elif t == "While":
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
        elif t == "DoWhile":
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
        elif t == "FuncDecl":
            is_async, is_gen, fid, nparams, nbody = a
            sink.put("FUNC_FLAGS", (2 if is_async else 0) + (1 if is_gen else 0))
            sink.put("OPT_FLAG", 1 if fid is not None else 0)
            if fid is not None:
                emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, fid)
            emit_list_len(sink, "LIST_LEN_ARGS", 8, nparams)
            for c in ch[:nparams]:
                emit_child_fn(c)
            emit_list_len(sink, "LIST_LEN_STMT", 16, nbody)
            for c in ch[nparams:]:
                emit_child_fn(c)
        elif t == "ClassDecl":
            cid, has_super, mspecs = a
            sink.put("OPT_FLAG", 1 if cid is not None else 0)
            if cid is not None:
                emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, cid)
            sink.put("OPT_FLAG", 1 if has_super else 0)
            ci = 0
            if has_super:
                emit_child_fn(ch[ci])
                ci += 1
            emit_class_members(sink, pools, mspecs, ch, ci, emit_child_fn)
        elif t in ("Break", "Continue"):
            sink.put("OPT_FLAG", 1 if a[0] is not None else 0)
            if a[0] is not None:
                emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, a[0])
        elif t == "Throw":
            emit_child_fn(ch[0])
        elif t == "Switch":
            cspecs = a[0]
            emit_child_fn(ch[0])
            emit_list_len(sink, "LIST_LEN_ARGS", 8, len(cspecs))
            ci = 1
            for ht, ncons in cspecs:
                sink.put("OPT_FLAG", 1 if ht else 0)
                if ht:
                    emit_child_fn(ch[ci])
                    ci += 1
                emit_list_len(sink, "LIST_LEN_STMT", 16, ncons)
                for _ in range(ncons):
                    emit_child_fn(ch[ci])
                    ci += 1
        elif t == "Try":
            hh, hp, hlen, hf = a
            emit_child_fn(ch[0])
            ci = 1
            sink.put("OPT_FLAG", 1 if hh else 0)
            if hh:
                sink.put("OPT_FLAG", 1 if hp else 0)
                if hp:
                    emit_child_fn(ch[ci])
                    ci += 1
                emit_list_len(sink, "LIST_LEN_STMT", 16, hlen)
                for _ in range(hlen):
                    emit_child_fn(ch[ci])
                    ci += 1
            sink.put("OPT_FLAG", 1 if hf else 0)
            if hf:
                emit_child_fn(ch[ci])
        elif t in ("Empty", "Debugger"):
            pass
        elif t == "Labeled":
            emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, a[0])
            emit_child_fn(ch[0])
        elif t == "With":
            emit_child_fn(ch[0])
            emit_child_fn(ch[1])
        elif t == "ImportDecl":
            specs, src = a
            emit_list_len(sink, "LIST_LEN_ARGS", 8, len(specs))
            kmap = {"default": 0, "ns": 1, "named": 2}
            for k, imp, loc in specs:
                sink.put("IMPORT_SPEC_KIND", kmap[k])
                if k == "named":
                    emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, imp)
                emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, loc)
            emit_pooled(sink, "STR_LIT", pools.str_idx, src)
        elif t == "ExportNamed":
            has_decl, specs, src = a
            sink.put("OPT_FLAG", 1 if has_decl else 0)
            if has_decl:
                emit_child_fn(ch[0])
            else:
                emit_list_len(sink, "LIST_LEN_ARGS", 8, len(specs))
                for loc, exp in specs:
                    emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, loc)
                    emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, exp)
                sink.put("OPT_FLAG", 1 if src is not None else 0)
                if src is not None:
                    emit_pooled(sink, "STR_LIT", pools.str_idx, src)
        elif t == "ExportDefault":
            dk = a[0]
            dmap = {"FuncDecl": 0, "ClassDecl": 1, "Expr": 2}
            sink.put("EXPORT_DEF_KIND", dmap[dk])
            emit_child_fn(ch[0])
        elif t == "ExportAll":
            exp, src = a
            sink.put("OPT_FLAG", 1 if exp is not None else 0)
            if exp is not None:
                emit_pooled(sink, "BIND_NAME", pools.bind_name_idx, exp)
            emit_pooled(sink, "STR_LIT", pools.str_idx, src)
        else:
            raise ValueError(f"Unknown STMT tag {t}")
        return
    raise ValueError(f"Unknown node group {g}")


def emit_class_members(sink: SymbolSink, pools: Pools, mspecs: tuple, ch: tuple, ci: int, emit_child_fn) -> int:
    emit_list_len(sink, "LIST_LEN_ARGS", 8, len(mspecs))
    kmap = {"method": 0, "get": 1, "set": 2, "field": 3}
    for mkind, is_stat, is_async, is_gen, k_info, has_val in mspecs:
        sink.put("CLASS_MEM_KIND", kmap[mkind])
        sink.put("OPT_FLAG", 1 if is_stat else 0)
        sink.put("FUNC_FLAGS", (2 if is_async else 0) + (1 if is_gen else 0))
        if k_info[0] == "comp":
            sink.put("OBJ_PROP_KIND", 4)
            emit_child_fn(ch[ci])
            ci += 1
        else:
            emit_key_spec(sink, pools, k_info)
        sink.put("OPT_FLAG", 1 if has_val else 0)
        if has_val:
            emit_child_fn(ch[ci])
            ci += 1
    return ci


# ---------------------------------------------------------------------------
# Frame Definition Header Serialization (Arithmetic-Coded via Base AST Tables)
# ---------------------------------------------------------------------------

def child_contexts_of_frame_node(group: str, tag: str, atoms: tuple) -> list[tuple[str, str]]:
    """Return exact (group, ctx) of each child slot for any frame-eligible AST node."""
    if group == "EXPR":
        if tag in ("Binary", "Logical"):
            return [("EXPR", "EXPR_BIN_L"), ("EXPR", "EXPR_BIN_R")]
        if tag == "Assign":
            return [("EXPR", "EXPR_LHS"), ("EXPR", "EXPR_INIT")]
        if tag in ("Unary", "Await"):
            return [("EXPR", "EXPR_OTHER")]
        if tag == "Update":
            return [("EXPR", "EXPR_LHS")]
        if tag == "Cond":
            return [("EXPR", "EXPR_TEST"), ("EXPR", "EXPR_OTHER"), ("EXPR", "EXPR_OTHER")]
        if tag == "MemberProp":
            return [("EXPR", "EXPR_OBJ")]
        if tag == "MemberComp":
            return [("EXPR", "EXPR_OBJ"), ("EXPR", "EXPR_PROP_IDX")]
        if tag == "Call":
            return [("EXPR", "EXPR_CALLEE")] + [("EXPR", "EXPR_ARG")] * atoms[1]
        if tag == "New":
            return [("EXPR", "EXPR_CALLEE")] + [("EXPR", "EXPR_ARG")] * atoms[0]
        if tag == "ArrayExpr":
            return [("EXPR", "EXPR_OTHER")] * sum(atoms[0])
        if tag == "Sequence":
            return [("EXPR", "EXPR_OTHER")] * atoms[0]
        if tag == "Spread":
            return [("EXPR", "EXPR_ARG")]
        return []
    if group == "STMT":
        if tag == "ExprStmt":
            return [("EXPR", "EXPR_STMT")]
        if tag == "VarDecl":
            # frameable VarDecl is always single BindCanon declarator
            return [("EXPR", "EXPR_INIT")] if atoms[1][0] else []
        if tag == "Block":
            return [("STMT", "STMT_BLOCK")] * atoms[0]
        if tag == "If":
            base = [("EXPR", "EXPR_TEST"), ("STMT", "STMT_BRANCH")]
            if atoms[0]:
                base.append(("STMT", "STMT_BRANCH"))
            return base
        if tag == "Return":
            return [("EXPR", "EXPR_ARG")] if atoms[0] else []
        if tag == "For":
            ik, ht, hu = atoms
            res = []
            if ik == 1:
                res.append(("STMT", "STMT_BLOCK"))
            elif ik == 2:
                res.append(("EXPR", "EXPR_STMT"))
            if ht:
                res.append(("EXPR", "EXPR_TEST"))
            if hu:
                res.append(("EXPR", "EXPR_STMT"))
            res.append(("STMT", "STMT_BRANCH"))
            return res
        if tag in ("ForOf", "ForIn"):
            ld = atoms[1] if tag == "ForOf" else atoms[0]
            return [("STMT", "STMT_BLOCK") if ld else ("EXPR", "EXPR_LHS"),
                    ("EXPR", "EXPR_OTHER"), ("STMT", "STMT_BRANCH")]
        if tag == "While":
            return [("EXPR", "EXPR_TEST"), ("STMT", "STMT_BRANCH")]
        if tag == "DoWhile":
            return [("STMT", "STMT_BRANCH"), ("EXPR", "EXPR_TEST")]
        if tag == "Throw":
            return [("EXPR", "EXPR_ARG")]
        return []
    return []


def _def_mode_weights(def_mode_w: list[int], allow_hole: bool, has_elig: bool) -> list[int]:
    if allow_hole and has_elig:
        return [def_mode_w[0], def_mode_w[1], def_mode_w[2]]
    if allow_hole:
        return [def_mode_w[0], def_mode_w[1]]
    if has_elig:
        return [def_mode_w[0], def_mode_w[2]]
    return [1]


def emit_frame_def_template(
    sink: SymbolSink,
    pools: Pools,
    tpl: tuple,
    ctx: str,
    group: str,
    max_depth: int,
    prev_eligible: dict[str, list[FrameDef]],
    def_mode_w: list[int],
    allow_hole: bool,
    mode_counts: list[int] | None = None,
) -> None:
    """Emit a frame definition template tree in header definition mode using DEF_MODE weights."""
    kind = tpl[0]
    elig = prev_eligible[group] if max_depth >= 2 else []
    has_elig = bool(elig)
    mw = _def_mode_weights(def_mode_w, allow_hole, has_elig)

    def emit_mode(choice_idx: int, raw_kind_idx: int) -> None:
        if mode_counts is not None:
            mode_counts[raw_kind_idx] += 1
        if len(mw) == 1:
            return
        if isinstance(sink, AC32Sink):
            sink.enc.encode(build_cum(mw), choice_idx)
        elif isinstance(sink, BitCostSink):
            sink.bits += math.log2(sum(mw) / float(mw[choice_idx]))

    if kind == "NODE":
        emit_mode(0, 0)
        _, g, tag, atoms, children = tpl
        assert g == group
        child_ctxs = child_contexts_of_frame_node(g, tag, atoms)
        dummy = TNode(group=g, tag=tag, ctx=ctx, atoms=atoms, children=tuple(range(len(children))), frameable=True)

        def emit_ch(idx: int) -> None:
            cg, cctx = child_ctxs[idx]
            emit_frame_def_template(sink, pools, children[idx], cctx, cg, max_depth, prev_eligible, def_mode_w, True, mode_counts)

        emit_tnode_local_only(sink, pools, dummy, emit_ch)
    elif kind == "HOLE":
        assert allow_hole
        emit_mode(1, 1)
    elif kind == "CALL":
        _, fid, grp, sub_s, args = tpl
        assert grp == group and has_elig
        emit_mode(2 if allow_hole else 1, 2)
        pos = next(i for i, f in enumerate(elig) if f.fid == fid)
        sink.put_uniform(pos, len(elig))
        sub_frame = elig[pos]
        if sub_frame.has_regs:
            sink.put_uniform(sub_s, 8)
        for (hg, hctx), arg_tpl in zip(sub_frame.holes, args):
            emit_frame_def_template(sink, pools, arg_tpl, hctx, hg, max_depth, prev_eligible, def_mode_w, True, mode_counts)
    else:
        raise ValueError(f"Unknown template kind: {kind}")


def fit_def_mode_weights(
    frames_ordered: list[FrameDef],
    pools: Pools,
    base_costs: dict[str, list[float]],
    max_depth: int,
) -> list[int]:
    """Fit exact DEF_MODE weights ([w_node, w_hole] or [w_node, w_hole, w_call]) from frames."""
    raw_counts = [0, 0, 0] if max_depth >= 2 else [0, 0]
    default_w = [12, 6, 3] if max_depth >= 2 else [12, 6]
    sink = BitCostSink(base_costs)
    prev_eligible: dict[str, list[FrameDef]] = {"EXPR": [], "STMT": []}
    for f in frames_ordered:
        root_ctx = "EXPR_OTHER" if f.group == "EXPR" else "STMT_BLOCK"
        emit_frame_def_template(sink, pools, f.tpl, root_ctx, f.group, max_depth, prev_eligible, default_w, False, raw_counts)
        if f.def_depth < max_depth:
            prev_eligible[f.group].append(f)
    return quantize_weights(raw_counts, max_total=255)


def serialize_frame_definitions(
    frames_ordered: list[FrameDef],
    pools: Pools,
    cums: dict[str, list[int]],
    def_mode_w: list[int],
    max_depth: int,
) -> bytes:
    """Serialize all frame definitions in topological order into a single AC32 byte block."""
    enc = ArithmeticEncoder()
    sink = AC32Sink(enc, cums)
    prev_eligible: dict[str, list[FrameDef]] = {"EXPR": [], "STMT": []}
    for f in frames_ordered:
        sink.put_uniform(0 if f.group == "EXPR" else 1, 2)
        root_ctx = "EXPR_OTHER" if f.group == "EXPR" else "STMT_BLOCK"
        emit_frame_def_template(sink, pools, f.tpl, root_ctx, f.group, max_depth, prev_eligible, def_mode_w, False)
        if f.def_depth < max_depth:
            prev_eligible[f.group].append(f)
    return enc.finish()


def estimate_frame_def_bits(
    tpl: tuple,
    group: str,
    pools: Pools,
    base_costs: dict[str, list[float]],
    max_depth: int,
    prev_eligible: dict[str, list[FrameDef]],
    def_mode_w: list[int] | None = None,
) -> float:
    """Exact bit cost of serializing one frame definition in the archive header."""
    mw = def_mode_w if def_mode_w is not None else ([12, 6, 3] if max_depth >= 2 else [12, 6])
    sink = BitCostSink(base_costs)
    sink.put_uniform(0 if group == "EXPR" else 1, 2)  # 1 bit group tag
    root_ctx = "EXPR_OTHER" if group == "EXPR" else "STMT_BLOCK"
    emit_frame_def_template(sink, pools, tpl, root_ctx, group, max_depth, prev_eligible, mw, False)
    return sink.bits + 8.0  # +1 byte for its probability weight entry in FRAME_ID table


def _match_flat_tpl_on_tpl(pat: tuple, target: tuple, shift: int, holes_out: list[tuple]) -> bool:
    """Match flat pattern `pat` shifted by +shift (mod 8) against flat template `target`."""
    if pat[0] == "HOLE":
        if target[0] == "HOLE":
            if target[1] != pat[1]:
                return False
            holes_out.append(target)
            return True
        if target[1] != pat[1]:
            return False
        holes_out.append(target)
        return True
    if target[0] != "NODE":
        return False
    _, pg, ptag, patoms, pch = pat
    _, tg, ttag, tatoms, tch = target
    if pg != tg or ptag != ttag:
        return False
    if ptag == "Reg8":
        return ((patoms[0] + shift) & 7) == tatoms[0]
    if patoms != tatoms or len(pch) != len(tch):
        return False
    for pc, tc in zip(pch, tch):
        if not _match_flat_tpl_on_tpl(pc, tc, shift, holes_out):
            return False
    return True


def optimize_frame_def_recursive(
    flat_tpl: tuple,
    group: str,
    pools: Pools,
    base_costs: dict[str, list[float]],
    max_depth: int,
    prev_eligible: dict[str, list[FrameDef]],
    def_mode_w: list[int],
    op_counter: dict[str, int] | None = None,
) -> tuple[tuple, float]:
    """Find the minimum-header-bit template representation of flat_tpl using base AST
    nodes and (when max_depth >= 2) earlier frames in prev_eligible via exact 8-shift
    enumeration. When max_depth == 1, returns (flat_tpl, flat_bits) identically."""
    root_ctx = "EXPR_OTHER" if group == "EXPR" else "STMT_BLOCK"
    if max_depth <= 1 or (not prev_eligible["EXPR"] and not prev_eligible["STMT"]):
        return flat_tpl, estimate_frame_def_bits(flat_tpl, group, pools, base_costs, max_depth, prev_eligible, def_mode_w)

    shift_ops = 0

    def dp(sub: tuple, grp: str, ctx: str, allow_hole: bool, rem_depth: int) -> tuple[tuple, float]:
        nonlocal shift_ops
        elig = prev_eligible[grp] if rem_depth >= 2 else []
        has_elig = bool(elig)
        mw = _def_mode_weights(def_mode_w, allow_hole, has_elig)
        tot_mw = float(sum(mw))

        if sub[0] == "HOLE":
            assert allow_hole
            b = math.log2(tot_mw / float(mw[1])) if len(mw) > 1 else 0.0
            return sub, b

        # Option 0: emit as base NODE + optimal children
        _, g, tag, atoms, children = sub
        child_ctxs = child_contexts_of_frame_node(g, tag, atoms)
        dummy = TNode(group=g, tag=tag, ctx=ctx, atoms=atoms, children=tuple(range(len(children))), frameable=True)
        local_sink = BitCostSink(base_costs)
        emit_tnode_local_only(local_sink, pools, dummy, lambda _: None)
        mode0_bits = math.log2(tot_mw / float(mw[0])) if len(mw) > 1 else 0.0
        best_children = []
        ch_bits = 0.0
        for c_sub, (cg, cctx) in zip(children, child_ctxs):
            ct, cb = dp(c_sub, cg, cctx, True, rem_depth)
            best_children.append(ct)
            ch_bits += cb
        best_tpl: tuple = ("NODE", g, tag, atoms, tuple(best_children))
        best_bits = mode0_bits + local_sink.bits + ch_bits

        # Option 1: emit as CALL to an eligible earlier frame (with exact 8-shift enumeration!)
        if has_elig:
            call_mode_idx = 2 if allow_hole else 1
            call_base_bits = math.log2(tot_mw / float(mw[call_mode_idx])) + math.log2(len(elig))
            for f in elig:
                if f.def_depth >= rem_depth:
                    continue
                if f.root_tag != tag:
                    continue
                shifts = range(8) if f.has_regs else (0,)
                sh_bits = 3.0 if f.has_regs else 0.0
                for s in shifts:
                    shift_ops += 1
                    matched_holes: list[tuple] = []
                    if _match_flat_tpl_on_tpl(f.flat_tpl, sub, s, matched_holes):
                        # Avoid trivial identity wrapping (1-to-1 with same hole count and no node reduction)
                        if not allow_hole and f.base_node_count == tpl_node_count(sub) and len(matched_holes) == 0:
                            continue
                        arg_tpls = []
                        arg_bits = 0.0
                        for (hg, hctx), mh in zip(f.holes, matched_holes):
                            at, ab = dp(mh, hg, hctx, True, rem_depth - 1)
                            arg_tpls.append(at)
                            arg_bits += ab
                        tot = call_base_bits + sh_bits + arg_bits
                        if tot + 1e-9 < best_bits:
                            best_bits = tot
                            best_tpl = ("CALL", f.fid, grp, s if f.has_regs else 0, tuple(arg_tpls))

        return best_tpl, best_bits

    opt_tpl, opt_bits = dp(flat_tpl, group, root_ctx, False, max_depth)
    if op_counter is not None:
        op_counter["shift_evaluations"] = op_counter.get("shift_evaluations", 0) + shift_ops
    return opt_tpl, opt_bits + 1.0 + 8.0  # +1 group bit + 8 weight bits


# ---------------------------------------------------------------------------
# Exact Optimal Bottom-Up Tree DP Parser (with Exact 8-Cyclic-Shift Matching!)
# ---------------------------------------------------------------------------

def match_flat_template_at_shift(flat_tpl: tuple, node: TNode, shift: int, holes_out: list[TNode]) -> bool:
    """Test whether flat_tpl shifted by +shift (mod 8) matches node, collecting hole TNodes."""
    if flat_tpl[0] == "HOLE":
        if node.group != flat_tpl[1]:
            return False
        holes_out.append(node)
        return True
    if not node.frameable:
        return False
    _, grp, tag, atoms, children = flat_tpl
    if node.group != grp or node.tag != tag:
        return False
    if tag == "Reg8":
        return ((atoms[0] + shift) & 7) == node.atoms[0]
    if node.atoms != atoms or len(node.children) != len(children):
        return False
    for tc, nc in zip(children, node.children):
        if not match_flat_template_at_shift(tc, nc, shift, holes_out):
            return False
    return True


def compute_node_local_cost(node: TNode, pools: Pools, costs: dict[str, list[float]]) -> float:
    """Exact bit cost of node's own tag + scalar atoms (excluding children)."""
    sink = BitCostSink(costs)
    emit_tnode_local_only(sink, pools, node, lambda _: None)
    return sink.bits


@dataclass
class ParseChoice:
    use_frame: bool
    frame: FrameDef | None
    shift: int
    hole_nodes: list[TNode]
    cost: float


def parse_ast_optimal(
    stmts: list[TNode],
    pools: Pools,
    costs: dict[str, list[float]],
    frames_by_root: dict[tuple[str, str], list[FrameDef]],
    has_frames: bool,
    op_counter: dict[str, int] | None = None,
) -> tuple[dict[int, ParseChoice], float]:
    """Exact bottom-up minimum-bit tree DP parse over all legal frame matches and
    exact 8-cyclic-register-shift enumerations (NO FFT/NTT)."""
    choices: dict[int, ParseChoice] = {}
    dp_cost: dict[int, float] = {}

    shift_evals = 0
    dp_nodes = 0

    def solve(node: TNode) -> float:
        nonlocal shift_evals, dp_nodes
        dp_nodes += 1
        # Solve all children bottom-up first
        child_sum = 0.0
        for ch in node.children:
            child_sum += solve(ch)

        local_cost = compute_node_local_cost(node, pools, costs)
        best_cost = local_cost + child_sum
        best_choice = ParseChoice(False, None, 0, [], best_cost)

        if has_frames and node.frameable and node.group in ("EXPR", "STMT"):
            cands = frames_by_root.get((node.group, node.tag))
            if cands:
                sw_sym = NUM_BASE_EXPR if node.group == "EXPR" else NUM_BASE_STMT
                sw_cost = costs[node.ctx][sw_sym]
                fid_ctx = "EXPR_FRAME_ID" if node.group == "EXPR" else "STMT_FRAME_ID"
                fid_costs = costs[fid_ctx]
                sh_costs = costs["REG_SHIFT"]
                for f in cands:
                    shifts = range(8) if f.has_regs else (0,)
                    base_f_cost = sw_cost + fid_costs[f.fid]
                    for s in shifts:
                        shift_evals += 1
                        holes: list[TNode] = []
                        if match_flat_template_at_shift(f.flat_tpl, node, s, holes):
                            tot = base_f_cost + (sh_costs[s] if f.has_regs else 0.0)
                            for h in holes:
                                tot += dp_cost[h.node_id]
                            # Strict deterministic tie-breaking (prefer strictly smaller bits, then smaller fid/shift)
                            if tot + 1e-9 < best_cost:
                                best_cost = tot
                                best_choice = ParseChoice(True, f, s, holes, tot)

        dp_cost[node.node_id] = best_cost
        choices[node.node_id] = best_choice
        return best_cost

    total = 0.0
    for st in stmts:
        total += solve(st)

    if op_counter is not None:
        op_counter["shift_evaluations"] = op_counter.get("shift_evaluations", 0) + shift_evals
        op_counter["dp_nodes_visited"] = op_counter.get("dp_nodes_visited", 0) + dp_nodes
    return choices, total


def emit_parsed_program(
    sink: SymbolSink,
    pools: Pools,
    stmts: list[TNode],
    choices: dict[int, ParseChoice],
    stats: dict[str, int] | None = None,
) -> None:
    """Emit a full AST Program using the DP ParseChoices."""
    emit_list_len(sink, "LIST_LEN_STMT", 16, len(stmts))

    def count_nested_in_tpl(tpl: tuple, frames_by_id: dict[tuple[str, int], FrameDef] | None = None) -> int:
        if tpl[0] == "CALL":
            c = 1 + sum(count_nested_in_tpl(a) for a in tpl[4])
            return c
        if tpl[0] == "NODE":
            return sum(count_nested_in_tpl(ch) for ch in tpl[4])
        return 0

    def emit_node(node: TNode) -> None:
        ch = choices[node.node_id]
        if ch.use_frame and ch.frame is not None:
            f = ch.frame
            if f.group == "EXPR":
                sink.put(node.ctx, NUM_BASE_EXPR)
                sink.put("EXPR_FRAME_ID", f.fid)
            else:
                sink.put(node.ctx, NUM_BASE_STMT)
                sink.put("STMT_FRAME_ID", f.fid)
            if f.has_regs:
                sink.put("REG_SHIFT", ch.shift)
            if stats is not None:
                stats["frame_uses"] = stats.get("frame_uses", 0) + 1
                if f.def_depth >= 2:
                    stats["recursive_frame_uses"] = stats.get("recursive_frame_uses", 0) + 1
                    stats["nested_subframe_calls"] = stats.get("nested_subframe_calls", 0) + count_nested_in_tpl(f.tpl)
            for hn in ch.hole_nodes:
                emit_node(hn)
        else:
            emit_tnode_local_only(sink, pools, node, emit_node)

    for st in stmts:
        emit_node(st)


# ---------------------------------------------------------------------------
# Unified Multi-Round Complete-Bit Frame Learner (Arm 3 max_depth=1, Arm 4 max_depth=3)
# ---------------------------------------------------------------------------

def tnode_to_closed_tpl(node: TNode, max_nodes: int) -> tuple | None:
    """Convert a small frameable TNode subtree to a closed template (0 holes) if <= max_nodes."""
    if not node.frameable or max_nodes <= 0:
        return None
    rem = max_nodes - 1
    ch_tpls = []
    for ch in node.children:
        if ch.group not in ("EXPR", "STMT"):
            return None
        ct = tnode_to_closed_tpl(ch, rem)
        if ct is None:
            return None
        rem -= tpl_node_count(ct)
        if rem < 0:
            return None
        ch_tpls.append(ct)
    return ("NODE", node.group, node.tag, node.atoms, tuple(ch_tpls))


def extract_candidates_from_parse(
    stmts: list[TNode],
    choices: dict[int, ParseChoice],
    frames_by_id: dict[tuple[str, int], FrameDef],
    max_depth: int,
    max_expanded_nodes: int = 12,
    max_holes: int = 3,
) -> list[tuple[str, tuple, TNode, list[TNode]]]:
    """Extract candidate frame patterns (group, raw_tpl, root_node, hole_nodes) from one
    program's current DP parse.
    When max_depth >= 2, children already parsed as frames of depth < max_depth become
    nested CALL_FRAMEs inside new compound patterns. When max_depth == 1, the exact same
    compound patterns are flattened to depth-1 base AST templates (100% fair comparison!)."""
    out: list[tuple[str, tuple, TNode, list[TNode]]] = []

    def current_unit(node: TNode) -> tuple[tuple, list[TNode], int] | None:
        """Represent node as either its current chosen frame CALL (if any) or small closed subtree."""
        ch = choices[node.node_id]
        if ch.use_frame and ch.frame is not None:
            f = ch.frame
            if f.base_node_count > max_expanded_nodes:
                return None
            if max_depth >= 2 and f.def_depth < max_depth:
                # Represent as a nested CALL with pass-through HOLEs for f's holes
                call_args = tuple(("HOLE", hg, hctx) for hg, hctx in f.holes)
                tpl = ("CALL", f.fid, f.group, ch.shift if f.has_regs else 0, call_args)
                return tpl, list(ch.hole_nodes), f.base_node_count
            else:
                # Flatten to base AST template (Arm 3 depth-1 or at max_depth cap!)
                flat = tpl_shift_exact(f.flat_tpl, ch.shift if f.has_regs else 0, frames_by_id)
                return flat, list(ch.hole_nodes), f.base_node_count
        # Otherwise try small closed AST subtree (<= 4 nodes)
        ct = tnode_to_closed_tpl(node, 4)
        if ct is not None:
            return ct, [], tpl_node_count(ct)
        return None

    def walk(node: TNode) -> None:
        if node.frameable and node.group in ("EXPR", "STMT") and node.children:
            c_ctxs = child_contexts_of_frame_node(node.group, node.tag, node.atoms)
            n_ch = len(node.children)
            if len(c_ctxs) == n_ch and all(c.group in ("EXPR", "STMT") for c in node.children):
                ch_units = [current_unit(c) for c in node.children]

                # Candidate type 1: Node + ALL children as HOLEs (only if node itself has rich atoms or >=2 children)
                if n_ch <= max_holes and (
                    node.tag in ("VarDecl", "For", "ForOf", "ForIn", "If", "Return", "Binary", "Logical",
                                 "Assign", "Unary", "Update", "MemberProp", "Call", "New")
                ):
                    all_h = tuple(("HOLE", cg, cc) for cg, cc in c_ctxs)
                    t1 = ("NODE", node.group, node.tag, node.atoms, all_h)
                    out.append((node.group, t1, node, list(node.children)))

                # Candidate type 2: Node + 1 concrete/sub-frame child, rest HOLEs
                for i in range(n_ch):
                    u = ch_units[i]
                    if u is None:
                        continue
                    u_tpl, u_holes, u_sz = u
                    tot_holes = (n_ch - 1) + len(u_holes)
                    if 1 + u_sz <= max_expanded_nodes and tot_holes <= max_holes:
                        ctpls = []
                        hnodes = []
                        for j in range(n_ch):
                            if j == i:
                                ctpls.append(u_tpl)
                                hnodes.extend(u_holes)
                            else:
                                ctpls.append(("HOLE", c_ctxs[j][0], c_ctxs[j][1]))
                                hnodes.append(node.children[j])
                        out.append((node.group, ("NODE", node.group, node.tag, node.atoms, tuple(ctpls)), node, hnodes))

                # Candidate type 3: Node + ALL concrete/sub-frame children (when n_ch >= 2 and small)
                if 2 <= n_ch <= 4 and all(u is not None for u in ch_units):
                    tot_sz = 1 + sum(u[2] for u in ch_units)
                    tot_holes = sum(len(u[1]) for u in ch_units)
                    if tot_sz <= max_expanded_nodes and tot_holes <= max_holes:
                        ctpls = tuple(u[0] for u in ch_units)
                        hnodes = []
                        for u in ch_units:
                            hnodes.extend(u[1])
                        out.append((node.group, ("NODE", node.group, node.tag, node.atoms, ctpls), node, hnodes))

                # Candidate type 4: Node + all children EXCEPT last (classic For/If/While header with body HOLE!)
                if n_ch >= 3 and all(ch_units[j] is not None for j in range(n_ch - 1)):
                    tot_sz = 1 + sum(ch_units[j][2] for j in range(n_ch - 1))
                    tot_holes = 1 + sum(len(ch_units[j][1]) for j in range(n_ch - 1))
                    if tot_sz <= max_expanded_nodes and tot_holes <= max_holes:
                        ctpls = [ch_units[j][0] for j in range(n_ch - 1)] + [("HOLE", c_ctxs[-1][0], c_ctxs[-1][1])]
                        hnodes = []
                        for j in range(n_ch - 1):
                            hnodes.extend(ch_units[j][1])
                        hnodes.append(node.children[-1])
                        out.append((node.group, ("NODE", node.group, node.tag, node.atoms, tuple(ctpls)), node, hnodes))

        # Candidate type 5: Specializing an already-chosen frame by plugging 1 of its holes!
        ch = choices[node.node_id]
        if ch.use_frame and ch.frame is not None and ch.hole_nodes:
            f = ch.frame
            for hi, hnode in enumerate(ch.hole_nodes):
                hu = current_unit(hnode)
                if hu is None:
                    continue
                hu_tpl, hu_holes, hu_sz = hu
                tot_sz = f.base_node_count + hu_sz
                tot_holes = (len(ch.hole_nodes) - 1) + len(hu_holes)
                if tot_sz > max_expanded_nodes or tot_holes > max_holes:
                    continue
                new_hnodes = []
                arg_tpls = []
                for hj, (hg, hctx) in enumerate(f.holes):
                    if hj == hi:
                        arg_tpls.append(hu_tpl)
                        new_hnodes.extend(hu_holes)
                    else:
                        arg_tpls.append(("HOLE", hg, hctx))
                        new_hnodes.append(ch.hole_nodes[hj])
                if max_depth >= 2 and f.def_depth < max_depth:
                    cand_tpl = ("CALL", f.fid, f.group, ch.shift if f.has_regs else 0, tuple(arg_tpls))
                    # Ensure depth <= max_depth
                    if tpl_def_depth(cand_tpl, frames_by_id) <= max_depth:
                        out.append((f.group, cand_tpl, node, new_hnodes))
                else:
                    # Flatten for Arm 3 depth-1 fairness!
                    raw_call = ("CALL", f.fid, f.group, ch.shift if f.has_regs else 0, tuple(arg_tpls))
                    flat = tpl_expand_to_flat(raw_call, frames_by_id, 0)
                    out.append((f.group, flat, node, new_hnodes))

        for c in node.children:
            walk(c)

    for st in stmts:
        walk(st)
    return out


def compute_costs_from_weights(weights: dict[str, list[int]]) -> dict[str, list[float]]:
    out = {}
    for ctx, ws in weights.items():
        tot = float(sum(ws))
        out[ctx] = [math.log2(tot / float(w)) for w in ws]
    return out


def fit_base_model(
    train_irs: list[list[TNode] | None],
    train_raw_bytes: list[bytes],
    pools: Pools,
    has_frames: bool = False,
) -> tuple[dict[str, list[int]], dict[str, list[float]]]:
    specs = all_base_context_specs(pools, has_frames=has_frames)
    csink = CountSink(specs)
    for ir, raw in zip(train_irs, train_raw_bytes):
        if ir is None:
            csink.put("FILE_MODE", 1)
            emit_uint(csink, len(raw))
            for b in raw:
                csink.put("INLINE_BYTE", b)
        else:
            csink.put("FILE_MODE", 0)
            emit_list_len(csink, "LIST_LEN_STMT", 16, len(ir))
            for st in ir:
                def walk(n: TNode) -> None:
                    emit_tnode_local_only(csink, pools, n, walk)
                walk(st)
    weights = {ctx: quantize_weights(cnts) for ctx, cnts in csink.counts.items()}
    return weights, compute_costs_from_weights(weights)


def learn_frames_unified(
    train_irs: list[list[TNode] | None],
    train_lineages: list[str],
    train_raw_bytes: list[bytes],
    pools: Pools,
    max_depth: int,
    max_frames: int = 160,
    min_lineage_support: int = 2,
    op_counter: dict[str, int] | None = None,
) -> tuple[list[FrameDef], dict[str, list[int]]]:
    """Unified multi-round complete-bit greedy frame learner.
    - max_depth == 0 -> Arm 2 (returns [], base weights)
    - max_depth == 1 -> Arm 3 (depth-1 non-recursive frames)
    - max_depth == 3 -> Arm 4 (recursive frames up to depth 3)
    Equivalence guarantee: calling with max_depth=1 is 100% bit-for-bit Arm 3!"""
    if max_depth == 0:
        w, _ = fit_base_model(train_irs, train_raw_bytes, pools, has_frames=False)
        return [], w

    base_weights, base_costs = fit_base_model(train_irs, train_raw_bytes, pools, has_frames=True)
    # Initialize frame-mode weights
    weights = dict(base_weights)
    weights["EXPR_FRAME_ID"] = [1]
    weights["STMT_FRAME_ID"] = [1]
    weights["REG_SHIFT"] = [1] * 8
    costs = compute_costs_from_weights(weights)

    frames_ordered: list[FrameDef] = []
    frames_by_id: dict[tuple[str, int], FrameDef] = {}
    frames_by_root: dict[tuple[str, str], list[FrameDef]] = {}
    seen_flat_keys: set[tuple[str, str]] = set()
    prev_eligible: dict[str, list[FrameDef]] = {"EXPR": [], "STMT": []}
    counts_by_group = {"EXPR": 0, "STMT": 0}

    def rebuild_frame_index() -> None:
        frames_by_root.clear()
        for f in frames_ordered:
            frames_by_root.setdefault((f.group, f.root_tag), []).append(f)

    def refit_tables_on_train(cur_frames: list[FrameDef], passes: int = 3) -> tuple[dict[str, list[int]], dict[str, list[float]], list[dict[int, ParseChoice] | None]]:
        f_e = sum(1 for f in cur_frames if f.group == "EXPR")
        f_s = sum(1 for f in cur_frames if f.group == "STMT")
        specs = all_base_context_specs(pools, has_frames=True)
        if f_e > 0:
            specs.append(("EXPR_FRAME_ID", f_e))
        if f_s > 0:
            specs.append(("STMT_FRAME_ID", f_s))
        specs.append(("REG_SHIFT", 8))

        # Cold-start prior: give USE_EXPR_FRAME / USE_STMT_FRAME a neutral ~25% prior weight
        # on Pass 0 (instead of 1/16384 = 14-bit penalty!) so EM converges to true minimum bits.
        cur_w = {}
        for ctx, ws in base_weights.items():
            w_copy = list(ws)
            if f_e > 0 and ctx in EXPR_CONTEXTS:
                w_copy[NUM_BASE_EXPR] = max(1, sum(w_copy[:-1]) // 3)
                w_copy = quantize_weights(w_copy)
            elif f_s > 0 and ctx in STMT_CONTEXTS:
                w_copy[NUM_BASE_STMT] = max(1, sum(w_copy[:-1]) // 3)
                w_copy = quantize_weights(w_copy)
            cur_w[ctx] = w_copy
        if f_e > 0:
            cur_w["EXPR_FRAME_ID"] = [1] * f_e
        if f_s > 0:
            cur_w["STMT_FRAME_ID"] = [1] * f_s
        cur_w["REG_SHIFT"] = [8, 2, 2, 2, 1, 1, 1, 1]
        cur_c = compute_costs_from_weights(cur_w)
        all_parses: list[dict[int, ParseChoice] | None] = [None] * len(train_irs)

        for _ in range(passes):
            csink = CountSink(specs)
            for idx, (ir, raw) in enumerate(zip(train_irs, train_raw_bytes)):
                if ir is None:
                    csink.put("FILE_MODE", 1)
                    emit_uint(csink, len(raw))
                    for b in raw:
                        csink.put("INLINE_BYTE", b)
                    all_parses[idx] = None
                else:
                    csink.put("FILE_MODE", 0)
                    choices, _ = parse_ast_optimal(ir, pools, cur_c, frames_by_root, bool(cur_frames), op_counter)
                    all_parses[idx] = choices
                    emit_parsed_program(csink, pools, ir, choices)
            cur_w = {ctx: quantize_weights(cnts) for ctx, cnts in csink.counts.items()}
            cur_c = compute_costs_from_weights(cur_w)
        return cur_w, cur_c, all_parses

    # 4 progressive bottom-up rounds (IDENTICAL schedule & expanded-size limits across Arm 3 and Arm 4!):
    #   Round 0: atomic motifs (max_expanded_nodes=4)
    #   Round 1: medium compositions (max_expanded_nodes=9)
    #   Round 2: deep compositions (max_expanded_nodes=14)
    #   Round 3: polish (max_expanded_nodes=18)
    round_schedule = [
        (64, 4),
        (64, 9),
        (64, 14),
        (max(0, max_frames - 192), 18),
    ]
    def_mode_prior = [12, 6, 3] if max_depth >= 2 else [12, 6]
    all_parses: list[dict[int, ParseChoice] | None] = [None] * len(train_irs)

    # Initial Round 0 parse (pure base AST)
    for idx, ir in enumerate(train_irs):
        if ir is not None:
            ch, _ = parse_ast_optimal(ir, pools, base_costs, {}, False, op_counter)
            all_parses[idx] = ch

    cur_costs = base_costs
    for r_idx, (r_cap, r_max_nodes) in enumerate(round_schedule):
        if r_cap <= 0 or len(frames_ordered) >= max_frames:
            break

        # Gather candidate statistics with exact 8-cyclic-shift canonicalization
        cand_savings: dict[tuple[str, str], float] = {}
        cand_count: Counter[tuple[str, str]] = Counter()
        cand_lineages: dict[tuple[str, str], set[str]] = {}
        cand_tpl_obj: dict[tuple[str, str], tuple] = {}
        cand_flat_obj: dict[tuple[str, str], tuple] = {}
        cand_has_regs: dict[tuple[str, str], bool] = {}
        cand_shifts: dict[tuple[str, str], Counter[int]] = {}
        cand_spans: dict[tuple[str, str], list[tuple[int, int]]] = {}  # (file_idx, root_node_id)

        shift_evals_round = 0

        for f_idx, (ir, lin, choices) in enumerate(zip(train_irs, train_lineages, all_parses)):
            if ir is None or choices is None:
                continue
            node_cost = {nid: pc.cost for nid, pc in choices.items()}
            cands = extract_candidates_from_parse(
                ir, choices, frames_by_id, max_depth=max_depth, max_expanded_nodes=r_max_nodes,
            )
            seen_in_file: set[tuple[str, str, int]] = set()
            for grp, raw_tpl, root_node, hole_nodes in cands:
                canon_tpl, win_s, n_ev = tpl_canonicalize_shift_exact(raw_tpl, frames_by_id)
                shift_evals_round += n_ev
                flat_tpl = tpl_expand_to_flat(canon_tpl, frames_by_id, 0)
                if flat_tpl[0] != "NODE":
                    continue
                if tpl_node_count(flat_tpl) > r_max_nodes:
                    continue
                if tpl_node_count(flat_tpl) < 2 and len(hole_nodes) == 0:
                    continue
                if tpl_node_count(flat_tpl) < 2 and root_node.tag not in ("VarDecl", "MemberProp", "Binary", "Assign", "Call", "For", "If", "Return"):
                    continue
                flat_key = (grp, repr(flat_tpl))
                if flat_key in seen_flat_keys:
                    continue
                dedup_occ = (grp, flat_key[1], root_node.node_id)
                if dedup_occ in seen_in_file:
                    continue
                seen_in_file.add(dedup_occ)

                holes_cost = sum(node_cost[hn.node_id] for hn in hole_nodes)
                body_saved = node_cost[root_node.node_id] - holes_cost
                if body_saved <= 1.0:
                    continue

                if flat_key not in cand_tpl_obj:
                    cand_tpl_obj[flat_key] = canon_tpl
                    cand_flat_obj[flat_key] = flat_tpl
                    cand_has_regs[flat_key] = tpl_has_regs(canon_tpl, frames_by_id)
                    cand_lineages[flat_key] = set()
                    cand_shifts[flat_key] = Counter()
                    cand_savings[flat_key] = 0.0
                    cand_spans[flat_key] = []
                else:
                    if max_depth >= 2 and tpl_uses_nested_call(canon_tpl) and not tpl_uses_nested_call(cand_tpl_obj[flat_key]):
                        cand_tpl_obj[flat_key] = canon_tpl
                        cand_has_regs[flat_key] = tpl_has_regs(canon_tpl, frames_by_id)

                cand_savings[flat_key] += body_saved
                cand_count[flat_key] += 1
                cand_lineages[flat_key].add(lin)
                cand_shifts[flat_key][win_s] += 1
                cand_spans[flat_key].append((f_idx, root_node.node_id))

        if op_counter is not None:
            op_counter["shift_evaluations"] = op_counter.get("shift_evaluations", 0) + shift_evals_round

        # Score candidates by exact complete-bit net gain: payload_saved - optimal_header_def_cost
        est_call_overhead = 5.5
        scored = []
        for flat_key, raw_saved in cand_savings.items():
            grp = flat_key[0]
            cnt = cand_count[flat_key]
            if len(cand_lineages[flat_key]) < min_lineage_support or cnt < 3:
                continue
            flat_tpl = cand_flat_obj[flat_key]
            has_regs = cand_has_regs[flat_key]
            if has_regs:
                sh_cnts = cand_shifts[flat_key]
                sh_bits = sum(c * math.log2(cnt / c) for c in sh_cnts.values()) + 0.35 * cnt
            else:
                sh_bits = 0.0
            call_bits = cnt * (est_call_overhead + (math.log2(max(2, len(frames_ordered) + 16)) * 0.4)) + sh_bits
            # Optimal minimum-header-bit representation (recursive DP when max_depth >= 2, flat when max_depth == 1)
            opt_tpl, def_bits = optimize_frame_def_recursive(
                flat_tpl, grp, pools, base_costs, max_depth, prev_eligible, def_mode_prior, op_counter,
            )
            # Also compare with directly mined recursive cand_tpl_obj if it is even cheaper
            mined_tpl = cand_tpl_obj[flat_key]
            if max_depth >= 2 and mined_tpl != opt_tpl and tpl_def_depth(mined_tpl, frames_by_id) <= max_depth:
                mined_bits = estimate_frame_def_bits(mined_tpl, grp, pools, base_costs, max_depth, prev_eligible, def_mode_prior)
                if mined_bits + 1e-9 < def_bits:
                    opt_tpl = mined_tpl
                    def_bits = mined_bits
            has_regs = tpl_has_regs(opt_tpl, frames_by_id)
            net_gain = (raw_saved - call_bits) - def_bits
            if net_gain > 0.0:
                scored.append((-net_gain, grp, flat_key[1], opt_tpl, flat_tpl, has_regs, flat_key))

        scored.sort(key=lambda x: (round(x[0], 6), x[1], x[2]))
        if not scored:
            break

        admitted_this_round = 0
        claimed_roots: set[tuple[int, int]] = set()
        for neg_gain, grp, fkey_str, tpl, flat_tpl, has_regs, flat_key in scored:
            if admitted_this_round >= r_cap or len(frames_ordered) >= max_frames:
                break
            spans = cand_spans[flat_key]
            unclaimed = [sp for sp in spans if sp not in claimed_roots]
            if len(unclaimed) < 3:
                continue
            frac = len(unclaimed) / max(1, len(spans))
            if (-neg_gain) * frac <= 0.0:
                continue
            # Re-optimize definition against latest prev_eligible (in case earlier frame in this round helps!)
            if max_depth >= 2:
                tpl2, b2 = optimize_frame_def_recursive(
                    flat_tpl, grp, pools, base_costs, max_depth, prev_eligible, def_mode_prior, op_counter,
                )
                b1 = estimate_frame_def_bits(tpl, grp, pools, base_costs, max_depth, prev_eligible, def_mode_prior)
                if b2 + 1e-9 < b1:
                    tpl = tpl2
                    has_regs = tpl_has_regs(tpl, frames_by_id)
            d = tpl_def_depth(tpl, frames_by_id)
            if d > max_depth:
                continue
            fid = counts_by_group[grp]
            counts_by_group[grp] += 1
            fdef = FrameDef(
                group=grp,
                fid=fid,
                order_idx=len(frames_ordered),
                tpl=tpl,
                flat_tpl=flat_tpl,
                has_regs=has_regs,
                def_depth=d,
                holes=tpl_collect_holes(tpl, frames_by_id),
                root_tag=flat_tpl[2],
                base_node_count=tpl_node_count(flat_tpl),
            )
            frames_ordered.append(fdef)
            frames_by_id[(grp, fid)] = fdef
            seen_flat_keys.add(flat_key)
            if d < max_depth:
                prev_eligible[grp].append(fdef)
            for sp in unclaimed:
                claimed_roots.add(sp)
            admitted_this_round += 1

        if admitted_this_round == 0:
            break

        rebuild_frame_index()
        weights, cur_costs, all_parses = refit_tables_on_train(frames_ordered, passes=2)

    # Prune frames with < 2 runtime uses (preserving transitive sub-frame dependencies!)
    if frames_ordered:
        use_counts: Counter[tuple[str, int]] = Counter()
        for ir, choices in zip(train_irs, all_parses):
            if ir is None or choices is None:
                continue
            def count_used(node: TNode) -> None:
                pc = choices[node.node_id]
                if pc.use_frame and pc.frame is not None:
                    use_counts[(pc.frame.group, pc.frame.fid)] += 1
                    for hn in pc.hole_nodes:
                        count_used(hn)
                else:
                    for c in node.children:
                        count_used(c)
            for st in ir:
                count_used(st)

        keep: set[tuple[str, int]] = {k for k, c in use_counts.items() if c >= 2}
        changed = True
        while changed:
            changed = False
            for f in frames_ordered:
                if (f.group, f.fid) in keep:
                    for dep in tpl_direct_deps(f.tpl):
                        if dep not in keep:
                            keep.add(dep)
                            changed = True

        if len(keep) < len(frames_ordered):
            old_to_new: dict[tuple[str, int], int] = {}
            new_ordered: list[FrameDef] = []
            new_by_id: dict[tuple[str, int], FrameDef] = {}
            new_counts = {"EXPR": 0, "STMT": 0}

            def remap_tpl(tpl: tuple) -> tuple:
                if tpl[0] == "HOLE":
                    return tpl
                if tpl[0] == "CALL":
                    _, old_fid, grp, sub_s, args = tpl
                    return ("CALL", old_to_new[(grp, old_fid)], grp, sub_s, tuple(remap_tpl(a) for a in args))
                return ("NODE", tpl[1], tpl[2], tpl[3], tuple(remap_tpl(c) for c in tpl[4]))

            for f in frames_ordered:
                if (f.group, f.fid) not in keep:
                    continue
                nfid = new_counts[f.group]
                new_counts[f.group] += 1
                old_to_new[(f.group, f.fid)] = nfid
                ntpl = remap_tpl(f.tpl)
                nflat = tpl_expand_to_flat(ntpl, new_by_id, 0)
                nf = FrameDef(
                    group=f.group,
                    fid=nfid,
                    order_idx=len(new_ordered),
                    tpl=ntpl,
                    flat_tpl=nflat,
                    has_regs=tpl_has_regs(ntpl, new_by_id),
                    def_depth=tpl_def_depth(ntpl, new_by_id),
                    holes=tpl_collect_holes(ntpl, new_by_id),
                    root_tag=nflat[2],
                    base_node_count=tpl_node_count(nflat),
                )
                new_ordered.append(nf)
                new_by_id[(f.group, nfid)] = nf
            frames_ordered = new_ordered
            frames_by_id = new_by_id
            rebuild_frame_index()

        # Final 3-pass exact table refit on training ASTs + exact DEF_MODE weights
        weights, cur_costs, _ = refit_tables_on_train(frames_ordered, passes=3)
        weights["DEF_MODE"] = fit_def_mode_weights(frames_ordered, pools, cur_costs, max_depth)
    else:
        weights["DEF_MODE"] = [1, 1, 1] if max_depth >= 2 else [1, 1]

    return frames_ordered, weights
