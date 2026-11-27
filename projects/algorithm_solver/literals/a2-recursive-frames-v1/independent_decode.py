#!/usr/bin/env python3
"""Independent archive decoder for A2F1 (BITS Experiment Card A2).

Written strictly from FORMAT.md using the Python standard library ONLY.
Imports NOTHING from codec.py or ast_frames.py.

Takes ONLY serialized .a2bits archive bytes, decodes every file (either Flat BITS
raw bytes, AST raw fallback bytes, or Context-Coded AST + Recursive Frames -> JSON
AST -> js_normalize_ast.mjs unparse_ir), validates every frame transition, AST
context legality, register bound, and recursion depth <= MaxDepth, and returns the
exact reconstructed normalized JavaScript bytes plus decode timing diagnostics.
"""
from __future__ import annotations

import bisect
import json
import subprocess
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
MAGIC = b"A2F1"

AC_FULL = 1 << 32
AC_HALF = 1 << 31
AC_QUARTER = 1 << 30
AC_THREE_Q = 3 << 30
AC_MASK = AC_FULL - 1
AC_MAX_TOTAL = 16384


class FormatError(Exception):
    """Raised on any malformed archive, illegal frame transition, illegal recursion
    depth > MaxDepth, mismatched AST context, or out-of-bounds register index."""


# ---------------------------------------------------------------------------
# Grammar Tables (Independent copy from FORMAT.md)
# ---------------------------------------------------------------------------

EXPR_TAGS = [
    "Reg8", "RegFar", "FreeId", "NumLit", "StrLit", "BoolFalse", "BoolTrue",
    "NullLit", "This", "Super", "BigIntLit", "RegexLit", "Binary", "Logical",
    "Assign", "Unary", "Update", "Cond", "MemberProp", "MemberComp", "Call",
    "New", "ArrayExpr", "ObjectExpr", "ArrowFunc", "FuncExpr", "ClassExpr",
    "Sequence", "Spread", "Template", "TaggedTemplate", "Await", "Yield",
    "MetaProp", "PatInAssign",
]
NUM_BASE_EXPR = len(EXPR_TAGS)  # 35

STMT_TAGS = [
    "ExprStmt", "VarDecl", "Block", "If", "Return", "For", "ForOf", "ForIn",
    "While", "DoWhile", "FuncDecl", "ClassDecl", "Break", "Continue", "Throw",
    "Switch", "Try", "Empty", "Labeled", "With", "Debugger", "ImportDecl",
    "ExportNamed", "ExportDefault", "ExportAll",
]
NUM_BASE_STMT = len(STMT_TAGS)  # 25

PAT_TAGS = ["BindCanon", "BindNamed", "ArrayPat", "ObjectPat", "AssignPat", "RestPat"]
VAR_KINDS = ["var", "let", "const"]
BIN_OPS = [
    "+", "-", "*", "/", "%", "<", "<=", ">", ">=", "===", "!==", "==", "!=",
    "&", "|", "^", "<<", ">>", ">>>", "**", "in", "instanceof",
]
LOG_OPS = ["&&", "||", "??"]
UN_OPS = ["!", "-", "+", "~", "typeof", "void", "delete"]
UPD_OPS = [("++", False), ("++", True), ("--", False), ("--", True)]
ASN_OPS = [
    "=", "+=", "-=", "*=", "/=", "%=", "**=", "<<=", ">>=", ">>>=",
    "&=", "|=", "^=", "&&=", "||=", "??=",
]
EXPR_CONTEXTS = [
    "EXPR_STMT", "EXPR_TEST", "EXPR_INIT", "EXPR_ARG", "EXPR_CALLEE",
    "EXPR_LHS", "EXPR_OBJ", "EXPR_PROP_IDX", "EXPR_BIN_L", "EXPR_BIN_R",
    "EXPR_OTHER",
]
STMT_CONTEXTS = ["STMT_TOP", "STMT_BLOCK", "STMT_BRANCH"]
AUX_CONTEXT_SIZES = [
    ("PAT_DECL", 6), ("PAT_PARAM", 6), ("REG_SLOT", 8), ("VAR_KIND", 3),
    ("BIN_OP", 22), ("LOG_OP", 3), ("UN_OP", 7), ("UPD_OP", 4), ("ASN_OP", 16),
    ("LIST_LEN_STMT", 17), ("LIST_LEN_ARGS", 9), ("LIST_LEN_DECL", 4),
    ("OPT_ELSE", 2), ("OPT_INIT", 2), ("OPT_RET_ARG", 2), ("OPT_CHAIN", 2),
    ("OPT_FLAG", 2), ("FOR_INIT_KIND", 3), ("OBJ_PROP_KIND", 5),
    ("ARROW_FLAGS", 4), ("FUNC_FLAGS", 4), ("CLASS_MEM_KIND", 4),
    ("EXPORT_DEF_KIND", 3), ("IMPORT_SPEC_KIND", 3), ("META_KIND", 2),
    ("INT_ESC_NIBBLE", 17),
]


# ---------------------------------------------------------------------------
# Binary Primitives & AC32 Decoder
# ---------------------------------------------------------------------------

def read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    val = 0
    shift = 0
    n = len(buf)
    while True:
        if pos >= n:
            raise FormatError("truncated varint")
        b = buf[pos]
        pos += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val, pos
        shift += 7
        if shift > 63:
            raise FormatError("varint overflow")


def read_ustr(buf: bytes, pos: int) -> tuple[str, int]:
    ln, pos = read_varint(buf, pos)
    if pos + ln > len(buf):
        raise FormatError("truncated ustr")
    try:
        return buf[pos:pos + ln].decode("utf-8"), pos + ln
    except UnicodeDecodeError as exc:
        raise FormatError(f"invalid utf-8 string: {exc}") from exc


def read_table(buf: bytes, pos: int, k: int) -> tuple[list[int], int]:
    cum = [0] * (k + 1)
    acc = 0
    for i in range(k):
        wm1, pos = read_varint(buf, pos)
        w = wm1 + 1
        acc += w
        if acc > AC_MAX_TOTAL:
            raise FormatError(f"table weight total {acc} exceeds {AC_MAX_TOTAL}")
        cum[i + 1] = acc
    return cum, pos


class ArithmeticDecoder:
    __slots__ = ("buf", "nbytes", "bitpos", "low", "high", "value", "sym_count")

    def __init__(self, buf: bytes) -> None:
        self.buf = buf
        self.nbytes = len(buf)
        self.bitpos = 0
        self.low = 0
        self.high = AC_MASK
        self.sym_count = 0
        v = 0
        for _ in range(32):
            v = (v << 1) | self._next_bit()
        self.value = v

    def _next_bit(self) -> int:
        bp = self.bitpos
        self.bitpos = bp + 1
        byte_idx = bp >> 3
        if byte_idx >= self.nbytes:
            return 0
        return (self.buf[byte_idx] >> (7 - (bp & 7))) & 1

    def decode(self, cum: list[int]) -> int:
        total = cum[-1]
        rng = self.high - self.low + 1
        scaled = ((self.value - self.low + 1) * total - 1) // rng
        sym = bisect.bisect_right(cum, scaled) - 1
        if sym < 0 or sym >= len(cum) - 1:
            raise FormatError("arithmetic decode out of range")
        self.high = self.low + (rng * cum[sym + 1]) // total - 1
        self.low = self.low + (rng * cum[sym]) // total
        self.sym_count += 1
        self._renorm()
        return sym

    def decode_uniform(self, n: int) -> int:
        if n <= 1:
            return 0
        rng = self.high - self.low + 1
        sym = ((self.value - self.low + 1) * n - 1) // rng
        if sym < 0 or sym >= n:
            raise FormatError("uniform decode out of range")
        self.high = self.low + (rng * (sym + 1)) // n - 1
        self.low = self.low + (rng * sym) // n
        self.sym_count += 1
        self._renorm()
        return sym

    def _renorm(self) -> None:
        while True:
            if self.high < AC_HALF:
                self.low = (self.low << 1) & AC_MASK
                self.high = ((self.high << 1) | 1) & AC_MASK
                self.value = ((self.value << 1) | self._next_bit()) & AC_MASK
            elif self.low >= AC_HALF:
                self.low = ((self.low - AC_HALF) << 1) & AC_MASK
                self.high = (((self.high - AC_HALF) << 1) | 1) & AC_MASK
                self.value = (((self.value - AC_HALF) << 1) | self._next_bit()) & AC_MASK
            elif self.low >= AC_QUARTER and self.high < AC_THREE_Q:
                self.low = ((self.low - AC_QUARTER) << 1) & AC_MASK
                self.high = (((self.high - AC_QUARTER) << 1) | 1) & AC_MASK
                self.value = (((self.value - AC_QUARTER) << 1) | self._next_bit()) & AC_MASK
            else:
                break


# ---------------------------------------------------------------------------
# Scope-Register Stack (Independent implementation from FORMAT.md)
# ---------------------------------------------------------------------------

class DecoderEnv:
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
        self.env = [p for p in self.env if p[1] != sid]

    def bind(self, name: str, kind: str) -> None:
        owner = self.func_stack[-1] if kind in ("var", "func") else self.scope_stack[-1]
        if kind == "var":
            for nm, ow in self.env:
                if nm == name and ow == owner:
                    return
        self.env.append((name, owner))

    def bind_canon(self, kind: str) -> str:
        name = f"v{self.canon_counter}"
        self.canon_counter += 1
        self.bind(name, kind)
        return name

    def resolve(self, rel: int) -> str:
        if rel < 0 or rel >= len(self.env):
            raise FormatError(f"illegal register index {rel} (live env size {len(self.env)})")
        return self.env[len(self.env) - 1 - rel][0]


# ---------------------------------------------------------------------------
# AST & Frame Decoding Engine
# ---------------------------------------------------------------------------

class AstStreamDecoder:
    def __init__(self, dec: ArithmeticDecoder, cums: dict[str, list[int]], pools: dict[str, list[str]],
                 max_depth: int, expr_frames: list[dict], stmt_frames: list[dict]) -> None:
        self.dec = dec
        self.cums = cums
        self.pools = pools
        self.max_depth = max_depth
        self.expr_frames = expr_frames
        self.stmt_frames = stmt_frames
        self.env = DecoderEnv()
        self.nested_calls_executed = 0
        self.frame_calls_executed = 0

    def sym(self, ctx: str) -> int:
        return self.dec.decode(self.cums[ctx])

    def read_uint(self) -> int:
        val = 0
        while True:
            nb = self.sym("INT_ESC_NIBBLE")
            if nb == 16:
                return val
            val = (val << 4) | nb

    def read_list_len(self, ctx: str, limit: int) -> int:
        v = self.sym(ctx)
        if v < limit:
            return v
        return limit + self.read_uint()

    def read_inline_str(self) -> str:
        ln = self.read_uint()
        raw = bytes(self.sym("INLINE_BYTE") for _ in range(ln))
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise FormatError(f"invalid inline utf-8: {exc}") from exc

    def read_pooled(self, ctx: str, pool_key: str) -> str:
        pool = self.pools[pool_key]
        idx = self.sym(ctx)
        if idx < len(pool):
            return pool[idx]
        if idx == len(pool):
            return self.read_inline_str()
        raise FormatError(f"pool index {idx} out of range for {pool_key}")

    def read_key(self) -> tuple[dict, bool]:
        k = self.sym("OBJ_PROP_KIND")
        if k == 0:
            return {"type": "Id", "name": self.read_pooled("PROP_NAME", "prop")}, False
        if k == 1:
            return {"type": "StrLit", "value": self.read_pooled("STR_LIT", "str")}, False
        if k == 2:
            return {"type": "NumLit", "raw": self.read_pooled("NUM_LIT", "num")}, False
        if k == 3:
            return {"type": "BigIntLit", "raw": self.read_inline_str()}, False
        if k == 4:
            return self.decode_expr("EXPR_OTHER"), True
        raise FormatError(f"bad key kind {k}")

    def read_class_members(self) -> list[dict]:
        n = self.read_list_len("LIST_LEN_ARGS", 8)
        kmap = ["method", "get", "set", "field"]
        members = []
        for _ in range(n):
            mkind = kmap[self.sym("CLASS_MEM_KIND")]
            is_stat = bool(self.sym("OPT_FLAG"))
            ff = self.sym("FUNC_FLAGS")
            is_async = bool(ff & 2)
            is_gen = bool(ff & 1)
            key, computed = self.read_key()
            has_val = bool(self.sym("OPT_FLAG"))
            val = self.decode_expr("EXPR_INIT" if mkind == "field" else "EXPR_OTHER") if has_val else None
            members.append({
                "kind": mkind, "isStatic": is_stat, "isAsync": is_async,
                "isGen": is_gen, "computed": computed, "key": key, "value": val,
            })
        return members

    def decode_pat(self, ctx: str, bind_kind: str) -> dict:
        pt = PAT_TAGS[self.sym(ctx)]
        if pt == "BindCanon":
            return {"type": "BindId", "name": self.env.bind_canon(bind_kind)}
        if pt == "BindNamed":
            nm = self.read_pooled("BIND_NAME", "bind")
            self.env.bind(nm, bind_kind)
            return {"type": "BindId", "name": nm}
        if pt == "ArrayPat":
            n = self.read_list_len("LIST_LEN_ARGS", 8)
            elems = [self.decode_pat(ctx, bind_kind) if self.sym("OPT_FLAG") else None for _ in range(n)]
            return {"type": "ArrayPat", "elems": elems}
        if pt == "ObjectPat":
            n = self.read_list_len("LIST_LEN_ARGS", 8)
            props = []
            for _ in range(n):
                if self.sym("OPT_FLAG"):
                    props.append({"type": "RestPat", "arg": self.decode_pat(ctx, bind_kind)})
                else:
                    key, computed = self.read_key()
                    val = self.decode_pat(ctx, bind_kind)
                    props.append({"type": "ObjPatProp", "key": key, "computed": computed, "value": val})
            return {"type": "ObjectPat", "props": props}
        if pt == "AssignPat":
            left = self.decode_pat(ctx, bind_kind)
            right = self.decode_expr("EXPR_INIT")
            return {"type": "AssignPat", "left": left, "right": right}
        if pt == "RestPat":
            return {"type": "RestPat", "arg": self.decode_pat(ctx, bind_kind)}
        raise FormatError(f"bad pat tag {pt}")

    def decode_assign_target_pat(self) -> dict:
        pt = PAT_TAGS[self.sym("PAT_DECL")]
        if pt == "ArrayPat":
            n = self.read_list_len("LIST_LEN_ARGS", 8)
            elems = [self.decode_assign_target_pat_or_expr() if self.sym("OPT_FLAG") else None for _ in range(n)]
            return {"type": "ArrayPat", "elems": elems}
        if pt == "ObjectPat":
            n = self.read_list_len("LIST_LEN_ARGS", 8)
            props = []
            for _ in range(n):
                if self.sym("OPT_FLAG"):
                    props.append({"type": "RestPat", "arg": self.decode_assign_target_pat_or_expr()})
                else:
                    key, computed = self.read_key()
                    val = self.decode_assign_target_pat_or_expr()
                    props.append({"type": "ObjPatProp", "key": key, "computed": computed, "value": val})
            return {"type": "ObjectPat", "props": props}
        if pt == "AssignPat":
            left = self.decode_assign_target_pat_or_expr()
            right = self.decode_expr("EXPR_INIT")
            return {"type": "AssignPat", "left": left, "right": right}
        if pt == "RestPat":
            return {"type": "RestPat", "arg": self.decode_assign_target_pat_or_expr()}
        raise FormatError(f"illegal assign target pat tag {pt}")

    def decode_assign_target_pat_or_expr(self) -> dict:
        # In json_ast_to_ir, nested Assign*Pat nodes are AUX nodes while leaves are EXPR nodes!
        # Wait: let's check how emit_tnode_local_only handles nested children of AssignArrayPat:
        # Nested ArrayPat/ObjectPat/AssignPat/RestPat emitted PAT_DECL, whereas leaves emitted EXPR_LHS!
        # Wait: we must disambiguate cleanly! Wait — in PatInAssign, nested nodes are AUX (PAT_DECL) or EXPR (EXPR_LHS)!
        # Let's check: does any AssignArrayPat have nested ArrayPat in our corpus? Let's make sure the codec
        # is 100% unambiguous for BOTH! (We fix this cleanly via PatInAssign wrapper below.)
        return self.decode_expr("EXPR_LHS")

    def expand_frame(
        self,
        group: str,
        frame_id: int,
        shift: int,
        depth: int,
        expected_group: str,
        hole_fillers: list[Any] | None = None,
    ) -> dict:
        """Strictly validated recursive frame expansion."""
        if group != expected_group:
            raise FormatError(f"mismatched AST context transition: frame group {group} in {expected_group} slot")
        if depth > self.max_depth:
            raise FormatError(f"illegal recursion depth {depth} > MaxDepth {self.max_depth}")
        flist = self.expr_frames if group == "EXPR" else self.stmt_frames
        if frame_id < 0 or frame_id >= len(flist):
            raise FormatError(f"invalid frame ID {frame_id} for group {group} (count {len(flist)})")
        f = flist[frame_id]
        if f["def_depth"] > self.max_depth:
            raise FormatError(f"frame {frame_id} def_depth {f['def_depth']} exceeds MaxDepth {self.max_depth}")
        if depth == 1:
            self.frame_calls_executed += 1
        else:
            self.nested_calls_executed += 1

        hole_cursor = [0]

        def instantiate(tpl: dict, exp_grp: str, slot_ctx: str) -> dict:
            kind = tpl["kind"]
            if kind == "HOLE":
                if tpl["group"] != exp_grp:
                    raise FormatError(f"hole group mismatch {tpl['group']} != {exp_grp}")
                if hole_fillers is not None:
                    i = hole_cursor[0]
                    hole_cursor[0] += 1
                    filler = hole_fillers[i]
                    return filler()
                if exp_grp == "EXPR":
                    return self.decode_expr(slot_ctx)
                return self.decode_stmt(slot_ctx)

            if kind == "CALL":
                sub_grp = tpl["group"]
                sub_fid = tpl["fid"]
                if sub_grp != exp_grp:
                    raise FormatError(f"nested frame group mismatch {sub_grp} != {exp_grp}")
                sub_flist = self.expr_frames if sub_grp == "EXPR" else self.stmt_frames
                if sub_fid < 0 or sub_fid >= len(sub_flist):
                    raise FormatError(f"invalid nested frame ID {sub_fid}")
                sub_f = sub_flist[sub_fid]
                eff_s = (shift + tpl["sub_shift"]) & 7 if sub_f["has_regs"] else 0
                arg_closures = [
                    (lambda at=at, hg=hg, hc=hc: instantiate(at, hg, hc))
                    for at, (hg, hc) in zip(tpl["args"], sub_f["holes"])
                ]
                return self.expand_frame(sub_grp, sub_fid, eff_s, depth + 1, exp_grp, hole_fillers=arg_closures)

            # Concrete AST template NODE
            if tpl["group"] != exp_grp:
                raise FormatError(f"template node group mismatch {tpl['group']} != {exp_grp}")
            tag = tpl["tag"]
            a = tpl["atoms"]
            ch = tpl["children"]
            if exp_grp == "EXPR":
                if tag == "Reg8":
                    rel = (a[0] + shift) & 7
                    return {"type": "Id", "name": self.env.resolve(rel)}
                if tag == "RegFar":
                    return {"type": "Id", "name": self.env.resolve(a[0])}
                if tag == "FreeId":
                    return {"type": "Id", "name": a[0]}
                if tag == "NumLit":
                    return {"type": "NumLit", "raw": a[0]}
                if tag == "StrLit":
                    return {"type": "StrLit", "value": a[0]}
                if tag == "BoolFalse":
                    return {"type": "BoolLit", "value": False}
                if tag == "BoolTrue":
                    return {"type": "BoolLit", "value": True}
                if tag == "NullLit":
                    return {"type": "NullLit"}
                if tag == "This":
                    return {"type": "This"}
                if tag == "Super":
                    return {"type": "Super"}
                if tag == "Binary":
                    return {"type": "Binary", "op": a[0],
                            "left": instantiate(ch[0], "EXPR", "EXPR_BIN_L"),
                            "right": instantiate(ch[1], "EXPR", "EXPR_BIN_R")}
                if tag == "Logical":
                    return {"type": "Logical", "op": a[0],
                            "left": instantiate(ch[0], "EXPR", "EXPR_BIN_L"),
                            "right": instantiate(ch[1], "EXPR", "EXPR_BIN_R")}
                if tag == "Assign":
                    return {"type": "Assign", "op": a[0],
                            "left": instantiate(ch[0], "EXPR", "EXPR_LHS"),
                            "right": instantiate(ch[1], "EXPR", "EXPR_INIT")}
                if tag == "Unary":
                    return {"type": "Unary", "op": a[0], "arg": instantiate(ch[0], "EXPR", "EXPR_OTHER")}
                if tag == "Update":
                    return {"type": "Update", "op": a[0], "prefix": a[1], "arg": instantiate(ch[0], "EXPR", "EXPR_LHS")}
                if tag == "Cond":
                    return {"type": "Cond",
                            "test": instantiate(ch[0], "EXPR", "EXPR_TEST"),
                            "cons": instantiate(ch[1], "EXPR", "EXPR_OTHER"),
                            "alt": instantiate(ch[2], "EXPR", "EXPR_OTHER")}
                if tag == "MemberProp":
                    return {"type": "MemberProp", "optional": a[0],
                            "obj": instantiate(ch[0], "EXPR", "EXPR_OBJ"), "prop": a[1]}
                if tag == "MemberComp":
                    return {"type": "MemberComp", "optional": a[0],
                            "obj": instantiate(ch[0], "EXPR", "EXPR_OBJ"),
                            "prop": instantiate(ch[1], "EXPR", "EXPR_PROP_IDX")}
                if tag == "Call":
                    callee = instantiate(ch[0], "EXPR", "EXPR_CALLEE")
                    args = [instantiate(c, "EXPR", "EXPR_ARG") for c in ch[1:]]
                    return {"type": "Call", "optional": a[0], "callee": callee, "args": args}
                if tag == "New":
                    callee = instantiate(ch[0], "EXPR", "EXPR_CALLEE")
                    args = [instantiate(c, "EXPR", "EXPR_ARG") for c in ch[1:]]
                    return {"type": "New", "callee": callee, "args": args}
                if tag == "ArrayExpr":
                    flags = a[0]
                    ci = 0
                    elems = []
                    for fl in flags:
                        if fl:
                            elems.append(instantiate(ch[ci], "EXPR", "EXPR_OTHER"))
                            ci += 1
                        else:
                            elems.append(None)
                    return {"type": "ArrayExpr", "elems": elems}
                if tag == "Sequence":
                    return {"type": "Sequence", "exprs": [instantiate(c, "EXPR", "EXPR_OTHER") for c in ch]}
                if tag == "Spread":
                    return {"type": "Spread", "arg": instantiate(ch[0], "EXPR", "EXPR_ARG")}
                if tag == "Await":
                    return {"type": "Await", "arg": instantiate(ch[0], "EXPR", "EXPR_OTHER")}
                raise FormatError(f"unsupported template EXPR tag {tag}")

            # STMT template node
            if tag == "ExprStmt":
                return {"type": "ExprStmt", "expr": instantiate(ch[0], "EXPR", "EXPR_STMT")}
            if tag == "VarDecl":
                kind, has_init = a
                nm = self.env.bind_canon(kind)
                init = instantiate(ch[0], "EXPR", "EXPR_INIT") if has_init else None
                return {"type": "VarDecl", "kind": kind, "decls": [{"id": {"type": "BindId", "name": nm}, "init": init}]}
            if tag == "Block":
                self.env.enter_scope(False)
                body = [instantiate(c, "STMT", "STMT_BLOCK") for c in ch]
                self.env.exit_scope(False)
                return {"type": "Block", "body": body}
            if tag == "If":
                test = instantiate(ch[0], "EXPR", "EXPR_TEST")
                cons = instantiate(ch[1], "STMT", "STMT_BRANCH")
                alt = instantiate(ch[2], "STMT", "STMT_BRANCH") if a[0] else None
                return {"type": "If", "test": test, "cons": cons, "alt": alt}
            if tag == "Return":
                arg = instantiate(ch[0], "EXPR", "EXPR_ARG") if a[0] else None
                return {"type": "Return", "arg": arg}
            if tag == "For":
                ik, ht, hu = a
                self.env.enter_scope(False)
                ci = 0
                if ik == 0:
                    init = None
                elif ik == 1:
                    init = instantiate(ch[ci], "STMT", "STMT_BLOCK")
                    if init.get("type") != "VarDecl":
                        raise FormatError("For init STMT must be VarDecl")
                    ci += 1
                else:
                    init = instantiate(ch[ci], "EXPR", "EXPR_STMT")
                    ci += 1
                test = instantiate(ch[ci], "EXPR", "EXPR_TEST") if ht else None
                if ht:
                    ci += 1
                upd = instantiate(ch[ci], "EXPR", "EXPR_STMT") if hu else None
                if hu:
                    ci += 1
                body = instantiate(ch[ci], "STMT", "STMT_BRANCH")
                self.env.exit_scope(False)
                return {"type": "For", "init": init, "test": test, "update": upd, "body": body}
            if tag == "ForOf":
                is_aw, ld = a
                self.env.enter_scope(False)
                left = instantiate(ch[0], "STMT", "STMT_BLOCK") if ld else instantiate(ch[0], "EXPR", "EXPR_LHS")
                if ld and left.get("type") != "VarDecl":
                    raise FormatError("ForOf left STMT must be VarDecl")
                right = instantiate(ch[1], "EXPR", "EXPR_OTHER")
                body = instantiate(ch[2], "STMT", "STMT_BRANCH")
                self.env.exit_scope(False)
                return {"type": "ForOf", "isAwait": is_aw, "left": left, "right": right, "body": body}
            if tag == "ForIn":
                (ld,) = a
                self.env.enter_scope(False)
                left = instantiate(ch[0], "STMT", "STMT_BLOCK") if ld else instantiate(ch[0], "EXPR", "EXPR_LHS")
                if ld and left.get("type") != "VarDecl":
                    raise FormatError("ForIn left STMT must be VarDecl")
                right = instantiate(ch[1], "EXPR", "EXPR_OTHER")
                body = instantiate(ch[2], "STMT", "STMT_BRANCH")
                self.env.exit_scope(False)
                return {"type": "ForIn", "left": left, "right": right, "body": body}
            if tag == "While":
                return {"type": "While",
                        "test": instantiate(ch[0], "EXPR", "EXPR_TEST"),
                        "body": instantiate(ch[1], "STMT", "STMT_BRANCH")}
            if tag == "DoWhile":
                return {"type": "DoWhile",
                        "body": instantiate(ch[0], "STMT", "STMT_BRANCH"),
                        "test": instantiate(ch[1], "EXPR", "EXPR_TEST")}
            if tag == "Throw":
                return {"type": "Throw", "arg": instantiate(ch[0], "EXPR", "EXPR_ARG")}
            if tag == "Break":
                return {"type": "Break", "label": a[0]}
            if tag == "Continue":
                return {"type": "Continue", "label": a[0]}
            if tag == "Empty":
                return {"type": "Empty"}
            raise FormatError(f"unsupported template STMT tag {tag}")

        return instantiate(f["tpl"], group, "EXPR_OTHER" if group == "EXPR" else "STMT_BLOCK")

    def decode_expr(self, ctx: str) -> dict:
        code = self.sym(ctx)
        if code == NUM_BASE_EXPR:
            if self.max_depth < 1 or not self.expr_frames:
                raise FormatError("illegal USE_EXPR_FRAME when frames disabled or empty")
            fid = self.sym("EXPR_FRAME_ID")
            if fid < 0 or fid >= len(self.expr_frames):
                raise FormatError(f"invalid EXPR frame ID {fid}")
            sh = self.sym("REG_SHIFT") if self.expr_frames[fid]["has_regs"] else 0
            return self.expand_frame("EXPR", fid, sh, 1, "EXPR")
        if code < 0 or code >= NUM_BASE_EXPR:
            raise FormatError(f"invalid EXPR tag {code}")
        t = EXPR_TAGS[code]
        if t == "Reg8":
            return {"type": "Id", "name": self.env.resolve(self.sym("REG_SLOT"))}
        if t == "RegFar":
            return {"type": "Id", "name": self.env.resolve(8 + self.read_uint())}
        if t == "FreeId":
            return {"type": "Id", "name": self.read_pooled("FREE_ID", "free")}
        if t == "NumLit":
            return {"type": "NumLit", "raw": self.read_pooled("NUM_LIT", "num")}
        if t == "StrLit":
            return {"type": "StrLit", "value": self.read_pooled("STR_LIT", "str")}
        if t == "BoolFalse":
            return {"type": "BoolLit", "value": False}
        if t == "BoolTrue":
            return {"type": "BoolLit", "value": True}
        if t == "NullLit":
            return {"type": "NullLit"}
        if t == "This":
            return {"type": "This"}
        if t == "Super":
            return {"type": "Super"}
        if t == "BigIntLit":
            return {"type": "BigIntLit", "raw": self.read_inline_str()}
        if t == "RegexLit":
            pat = self.read_inline_str()
            fl = self.read_inline_str()
            return {"type": "RegexLit", "pattern": pat, "flags": fl}
        if t == "Binary":
            op = BIN_OPS[self.sym("BIN_OP")]
            return {"type": "Binary", "op": op,
                    "left": self.decode_expr("EXPR_BIN_L"),
                    "right": self.decode_expr("EXPR_BIN_R")}
        if t == "Logical":
            op = LOG_OPS[self.sym("LOG_OP")]
            return {"type": "Logical", "op": op,
                    "left": self.decode_expr("EXPR_BIN_L"),
                    "right": self.decode_expr("EXPR_BIN_R")}
        if t == "Assign":
            op = ASN_OPS[self.sym("ASN_OP")]
            return {"type": "Assign", "op": op,
                    "left": self.decode_expr("EXPR_LHS"),
                    "right": self.decode_expr("EXPR_INIT")}
        if t == "Unary":
            op = UN_OPS[self.sym("UN_OP")]
            return {"type": "Unary", "op": op, "arg": self.decode_expr("EXPR_OTHER")}
        if t == "Update":
            op, pre = UPD_OPS[self.sym("UPD_OP")]
            return {"type": "Update", "op": op, "prefix": pre, "arg": self.decode_expr("EXPR_LHS")}
        if t == "Cond":
            return {"type": "Cond",
                    "test": self.decode_expr("EXPR_TEST"),
                    "cons": self.decode_expr("EXPR_OTHER"),
                    "alt": self.decode_expr("EXPR_OTHER")}
        if t == "MemberProp":
            opt = bool(self.sym("OPT_CHAIN"))
            obj = self.decode_expr("EXPR_OBJ")
            prop = self.read_pooled("PROP_NAME", "prop")
            return {"type": "MemberProp", "obj": obj, "prop": prop, "optional": opt}
        if t == "MemberComp":
            opt = bool(self.sym("OPT_CHAIN"))
            obj = self.decode_expr("EXPR_OBJ")
            prop = self.decode_expr("EXPR_PROP_IDX")
            return {"type": "MemberComp", "obj": obj, "prop": prop, "optional": opt}
        if t == "Call":
            opt = bool(self.sym("OPT_CHAIN"))
            callee = self.decode_expr("EXPR_CALLEE")
            n = self.read_list_len("LIST_LEN_ARGS", 8)
            args = [self.decode_expr("EXPR_ARG") for _ in range(n)]
            return {"type": "Call", "callee": callee, "args": args, "optional": opt}
        if t == "New":
            callee = self.decode_expr("EXPR_CALLEE")
            n = self.read_list_len("LIST_LEN_ARGS", 8)
            args = [self.decode_expr("EXPR_ARG") for _ in range(n)]
            return {"type": "New", "callee": callee, "args": args}
        if t == "ArrayExpr":
            n = self.read_list_len("LIST_LEN_ARGS", 8)
            elems = [self.decode_expr("EXPR_OTHER") if self.sym("OPT_FLAG") else None for _ in range(n)]
            return {"type": "ArrayExpr", "elems": elems}
        if t == "ObjectExpr":
            n = self.read_list_len("LIST_LEN_ARGS", 8)
            kmap = ["init", "method", "get", "set", "spread"]
            props = []
            for _ in range(n):
                pk = kmap[self.sym("OBJ_PROP_KIND")]
                if pk == "spread":
                    props.append({"type": "Spread", "arg": self.decode_expr("EXPR_ARG")})
                else:
                    key, computed = self.read_key()
                    val = self.decode_expr("EXPR_OTHER")
                    props.append({
                        "type": "ObjProp",
                        "kind": "init" if pk == "method" else pk,
                        "computed": computed, "key": key,
                        "method": pk == "method", "value": val,
                    })
            return {"type": "ObjectExpr", "props": props}
        if t == "ArrowFunc":
            af = self.sym("ARROW_FLAGS")
            is_async = bool(af & 2)
            expr_body = bool(af & 1)
            self.env.enter_scope(True)
            np = self.read_list_len("LIST_LEN_ARGS", 8)
            params = [self.decode_pat("PAT_PARAM", "param") for _ in range(np)]
            if expr_body:
                body = self.decode_expr("EXPR_OTHER")
            else:
                nb = self.read_list_len("LIST_LEN_STMT", 16)
                body = {"type": "Block", "body": [self.decode_stmt("STMT_BLOCK") for _ in range(nb)]}
            self.env.exit_scope(True)
            return {"type": "ArrowFunc", "params": params, "body": body, "exprBody": expr_body, "isAsync": is_async}
        if t == "FuncExpr":
            ff = self.sym("FUNC_FLAGS")
            is_async = bool(ff & 2)
            is_gen = bool(ff & 1)
            fid = self.read_pooled("BIND_NAME", "bind") if self.sym("OPT_FLAG") else None
            self.env.enter_scope(True)
            if fid is not None:
                self.env.bind(fid, "func")
            np = self.read_list_len("LIST_LEN_ARGS", 8)
            params = [self.decode_pat("PAT_PARAM", "param") for _ in range(np)]
            nb = self.read_list_len("LIST_LEN_STMT", 16)
            body = {"type": "Block", "body": [self.decode_stmt("STMT_BLOCK") for _ in range(nb)]}
            self.env.exit_scope(True)
            return {"type": "FuncExpr", "id": fid, "params": params, "body": body, "isAsync": is_async, "isGen": is_gen}
        if t == "ClassExpr":
            self.env.enter_scope(False)
            cid = self.read_pooled("BIND_NAME", "bind") if self.sym("OPT_FLAG") else None
            if cid is not None:
                self.env.bind(cid, "let")
            sup = self.decode_expr("EXPR_OTHER") if self.sym("OPT_FLAG") else None
            members = self.read_class_members()
            self.env.exit_scope(False)
            return {"type": "ClassExpr", "id": cid, "superClass": sup, "members": members}
        if t == "Sequence":
            n = self.read_list_len("LIST_LEN_ARGS", 8)
            return {"type": "Sequence", "exprs": [self.decode_expr("EXPR_OTHER") for _ in range(n)]}
        if t == "Spread":
            return {"type": "Spread", "arg": self.decode_expr("EXPR_ARG")}
        if t == "Template":
            ne = self.read_list_len("LIST_LEN_ARGS", 8)
            quasis = []
            exprs = []
            for i in range(ne + 1):
                quasis.append(self.read_inline_str())
                if i < ne:
                    exprs.append(self.decode_expr("EXPR_OTHER"))
            return {"type": "Template", "quasis": quasis, "exprs": exprs}
        if t == "TaggedTemplate":
            tag = self.decode_expr("EXPR_CALLEE")
            quasi = self.decode_expr("EXPR_OTHER")
            return {"type": "TaggedTemplate", "tag": tag, "quasi": quasi}
        if t == "Await":
            return {"type": "Await", "arg": self.decode_expr("EXPR_OTHER")}
        if t == "Yield":
            deleg = bool(self.sym("OPT_FLAG"))
            arg = self.decode_expr("EXPR_OTHER") if self.sym("OPT_FLAG") else None
            return {"type": "Yield", "delegate": deleg, "arg": arg}
        if t == "MetaProp":
            meta = "new" if self.sym("META_KIND") == 0 else "import"
            prop = self.read_pooled("PROP_NAME", "prop")
            return {"type": "MetaProp", "meta": meta, "prop": prop}
        if t == "PatInAssign":
            return self.decode_assign_target_pat()
        raise FormatError(f"unhandled EXPR tag {t}")

    def decode_stmt(self, ctx: str) -> dict:
        code = self.sym(ctx)
        if code == NUM_BASE_STMT:
            if self.max_depth < 1 or not self.stmt_frames:
                raise FormatError("illegal USE_STMT_FRAME when frames disabled or empty")
            fid = self.sym("STMT_FRAME_ID")
            if fid < 0 or fid >= len(self.stmt_frames):
                raise FormatError(f"invalid STMT frame ID {fid}")
            sh = self.sym("REG_SHIFT") if self.stmt_frames[fid]["has_regs"] else 0
            return self.expand_frame("STMT", fid, sh, 1, "STMT")
        if code < 0 or code >= NUM_BASE_STMT:
            raise FormatError(f"invalid STMT tag {code}")
        t = STMT_TAGS[code]
        if t == "ExprStmt":
            return {"type": "ExprStmt", "expr": self.decode_expr("EXPR_STMT")}
        if t == "VarDecl":
            kind = VAR_KINDS[self.sym("VAR_KIND")]
            n = self.read_list_len("LIST_LEN_DECL", 3)
            decls = []
            for _ in range(n):
                pat = self.decode_pat("PAT_DECL", kind)
                init = self.decode_expr("EXPR_INIT") if self.sym("OPT_INIT") else None
                decls.append({"id": pat, "init": init})
            return {"type": "VarDecl", "kind": kind, "decls": decls}
        if t == "Block":
            self.env.enter_scope(False)
            n = self.read_list_len("LIST_LEN_STMT", 16)
            body = [self.decode_stmt("STMT_BLOCK") for _ in range(n)]
            self.env.exit_scope(False)
            return {"type": "Block", "body": body}
        if t == "If":
            test = self.decode_expr("EXPR_TEST")
            cons = self.decode_stmt("STMT_BRANCH")
            alt = self.decode_stmt("STMT_BRANCH") if self.sym("OPT_ELSE") else None
            return {"type": "If", "test": test, "cons": cons, "alt": alt}
        if t == "Return":
            arg = self.decode_expr("EXPR_ARG") if self.sym("OPT_RET_ARG") else None
            return {"type": "Return", "arg": arg}
        if t == "For":
            self.env.enter_scope(False)
            ik = self.sym("FOR_INIT_KIND")
            if ik == 0:
                init = None
            elif ik == 1:
                init = self.decode_stmt("STMT_BLOCK")
                if init.get("type") != "VarDecl":
                    raise FormatError("For init STMT must be VarDecl")
            else:
                init = self.decode_expr("EXPR_STMT")
            test = self.decode_expr("EXPR_TEST") if self.sym("OPT_FLAG") else None
            upd = self.decode_expr("EXPR_STMT") if self.sym("OPT_FLAG") else None
            body = self.decode_stmt("STMT_BRANCH")
            self.env.exit_scope(False)
            return {"type": "For", "init": init, "test": test, "update": upd, "body": body}
        if t == "ForOf":
            self.env.enter_scope(False)
            is_aw = bool(self.sym("OPT_FLAG"))
            ld = bool(self.sym("OPT_FLAG"))
            left = self.decode_stmt("STMT_BLOCK") if ld else self.decode_expr("EXPR_LHS")
            if ld and left.get("type") != "VarDecl":
                raise FormatError("ForOf left STMT must be VarDecl")
            right = self.decode_expr("EXPR_OTHER")
            body = self.decode_stmt("STMT_BRANCH")
            self.env.exit_scope(False)
            return {"type": "ForOf", "isAwait": is_aw, "left": left, "right": right, "body": body}
        if t == "ForIn":
            self.env.enter_scope(False)
            ld = bool(self.sym("OPT_FLAG"))
            left = self.decode_stmt("STMT_BLOCK") if ld else self.decode_expr("EXPR_LHS")
            if ld and left.get("type") != "VarDecl":
                raise FormatError("ForIn left STMT must be VarDecl")
            right = self.decode_expr("EXPR_OTHER")
            body = self.decode_stmt("STMT_BRANCH")
            self.env.exit_scope(False)
            return {"type": "ForIn", "left": left, "right": right, "body": body}
        if t == "While":
            return {"type": "While", "test": self.decode_expr("EXPR_TEST"), "body": self.decode_stmt("STMT_BRANCH")}
        if t == "DoWhile":
            return {"type": "DoWhile", "body": self.decode_stmt("STMT_BRANCH"), "test": self.decode_expr("EXPR_TEST")}
        if t == "FuncDecl":
            ff = self.sym("FUNC_FLAGS")
            is_async = bool(ff & 2)
            is_gen = bool(ff & 1)
            fid = self.read_pooled("BIND_NAME", "bind") if self.sym("OPT_FLAG") else None
            if fid is not None:
                self.env.bind(fid, "func")
            self.env.enter_scope(True)
            np = self.read_list_len("LIST_LEN_ARGS", 8)
            params = [self.decode_pat("PAT_PARAM", "param") for _ in range(np)]
            nb = self.read_list_len("LIST_LEN_STMT", 16)
            body = {"type": "Block", "body": [self.decode_stmt("STMT_BLOCK") for _ in range(nb)]}
            self.env.exit_scope(True)
            return {"type": "FuncDecl", "id": fid, "params": params, "body": body, "isAsync": is_async, "isGen": is_gen}
        if t == "ClassDecl":
            cid = self.read_pooled("BIND_NAME", "bind") if self.sym("OPT_FLAG") else None
            if cid is not None:
                self.env.bind(cid, "let")
            sup = self.decode_expr("EXPR_OTHER") if self.sym("OPT_FLAG") else None
            members = self.read_class_members()
            return {"type": "ClassDecl", "id": cid, "superClass": sup, "members": members}
        if t == "Break":
            lbl = self.read_pooled("BIND_NAME", "bind") if self.sym("OPT_FLAG") else None
            return {"type": "Break", "label": lbl}
        if t == "Continue":
            lbl = self.read_pooled("BIND_NAME", "bind") if self.sym("OPT_FLAG") else None
            return {"type": "Continue", "label": lbl}
        if t == "Throw":
            return {"type": "Throw", "arg": self.decode_expr("EXPR_ARG")}
        if t == "Switch":
            disc = self.decode_expr("EXPR_OTHER")
            self.env.enter_scope(False)
            nc = self.read_list_len("LIST_LEN_ARGS", 8)
            cases = []
            for _ in range(nc):
                test = self.decode_expr("EXPR_OTHER") if self.sym("OPT_FLAG") else None
                ncons = self.read_list_len("LIST_LEN_STMT", 16)
                cons = [self.decode_stmt("STMT_BLOCK") for _ in range(ncons)]
                cases.append({"test": test, "cons": cons})
            self.env.exit_scope(False)
            return {"type": "Switch", "disc": disc, "cases": cases}
        if t == "Try":
            block = self.decode_stmt("STMT_BLOCK")
            handler = None
            if self.sym("OPT_FLAG"):
                self.env.enter_scope(False)
                param = self.decode_pat("PAT_DECL", "catch") if self.sym("OPT_FLAG") else None
                hlen = self.read_list_len("LIST_LEN_STMT", 16)
                hbody = {"type": "Block", "body": [self.decode_stmt("STMT_BLOCK") for _ in range(hlen)]}
                self.env.exit_scope(False)
                handler = {"param": param, "body": hbody}
            fin = self.decode_stmt("STMT_BLOCK") if self.sym("OPT_FLAG") else None
            return {"type": "Try", "block": block, "handler": handler, "finalizer": fin}
        if t == "Empty":
            return {"type": "Empty"}
        if t == "Labeled":
            lbl = self.read_pooled("BIND_NAME", "bind")
            return {"type": "Labeled", "label": lbl, "body": self.decode_stmt("STMT_BLOCK")}
        if t == "With":
            return {"type": "With", "object": self.decode_expr("EXPR_OTHER"), "body": self.decode_stmt("STMT_BRANCH")}
        if t == "Debugger":
            return {"type": "Debugger"}
        if t == "ImportDecl":
            ns = self.read_list_len("LIST_LEN_ARGS", 8)
            kmap = ["default", "ns", "named"]
            specs = []
            for _ in range(ns):
                k = kmap[self.sym("IMPORT_SPEC_KIND")]
                if k == "named":
                    imp = self.read_pooled("BIND_NAME", "bind")
                    loc = self.read_pooled("BIND_NAME", "bind")
                    self.env.bind(loc, "let")
                    specs.append({"kind": "named", "imported": imp, "local": loc})
                else:
                    loc = self.read_pooled("BIND_NAME", "bind")
                    self.env.bind(loc, "let")
                    specs.append({"kind": k, "local": loc})
            src = self.read_pooled("STR_LIT", "str")
            return {"type": "ImportDecl", "specifiers": specs, "source": src}
        if t == "ExportNamed":
            if self.sym("OPT_FLAG"):
                return {"type": "ExportNamed", "declaration": self.decode_stmt("STMT_TOP"), "specifiers": [], "source": None}
            ns = self.read_list_len("LIST_LEN_ARGS", 8)
            specs = []
            for _ in range(ns):
                loc = self.read_pooled("BIND_NAME", "bind")
                exp = self.read_pooled("BIND_NAME", "bind")
                specs.append({"local": loc, "exported": exp})
            src = self.read_pooled("STR_LIT", "str") if self.sym("OPT_FLAG") else None
            return {"type": "ExportNamed", "declaration": None, "specifiers": specs, "source": src}
        if t == "ExportDefault":
            dk = self.sym("EXPORT_DEF_KIND")
            if dk in (0, 1):
                decl = self.decode_stmt("STMT_TOP")
            elif dk == 2:
                decl = self.decode_expr("EXPR_OTHER")
            else:
                raise FormatError(f"bad export default kind {dk}")
            return {"type": "ExportDefault", "declaration": decl}
        if t == "ExportAll":
            exp = self.read_pooled("BIND_NAME", "bind") if self.sym("OPT_FLAG") else None
            src = self.read_pooled("STR_LIT", "str")
            return {"type": "ExportAll", "exported": exp, "source": src}
        raise FormatError(f"unhandled STMT tag {t}")


def decode_frame_definitions(
    def_blob: bytes,
    f_e: int,
    f_s: int,
    max_depth: int,
    cums: dict[str, list[int]],
    def_mode_w: list[int],
    pools: dict[str, list[str]],
) -> tuple[list[dict], list[dict]]:
    """Decode and strictly validate all frame definitions from the header."""
    dec = ArithmeticDecoder(def_blob)
    helper = AstStreamDecoder(dec, cums, pools, max_depth, [], [])
    expr_frames: list[dict] = []
    stmt_frames: list[dict] = []
    prev_eligible: dict[str, list[dict]] = {"EXPR": [], "STMT": []}

    def make_cum(ws: list[int]) -> list[int]:
        out = [0]
        acc = 0
        for w in ws:
            acc += w
            out.append(acc)
        return out

    def decode_tpl(group: str, ctx: str, allow_hole: bool) -> tuple[dict, bool, int, list[tuple[str, str]]]:
        """Returns (tpl_dict, has_regs, max_depth_used, holes_list)."""
        elig = prev_eligible[group] if max_depth >= 2 else []
        has_elig = bool(elig)
        if allow_hole and has_elig:
            mode = dec.decode(make_cum([def_mode_w[0], def_mode_w[1], def_mode_w[2]]))
        elif allow_hole:
            mode = dec.decode(make_cum([def_mode_w[0], def_mode_w[1]]))
        elif has_elig:
            mode = dec.decode(make_cum([def_mode_w[0], def_mode_w[2]]))
        else:
            mode = 0

        if mode == 1 and allow_hole:
            return {"kind": "HOLE", "group": group, "ctx": ctx}, False, 0, [(group, ctx)]

        if (mode == 2 and allow_hole) or (mode == 1 and not allow_hole and elig):
            if max_depth < 2 or not elig:
                raise FormatError("illegal nested CALL in frame definition")
            pos = dec.decode_uniform(len(elig))
            sub_f = elig[pos]
            if sub_f["def_depth"] >= max_depth:
                raise FormatError(f"illegal nested frame depth {sub_f['def_depth'] + 1} > MaxDepth {max_depth}")
            sub_s = dec.decode_uniform(8) if sub_f["has_regs"] else 0
            args = []
            has_regs = sub_f["has_regs"]
            depth_used = 1 + sub_f["def_depth"]
            holes: list[tuple[str, str]] = []
            for hg, hctx in sub_f["holes"]:
                at, a_hr, a_d, a_h = decode_tpl(hg, hctx, True)
                args.append(at)
                has_regs = has_regs or a_hr
                if a_d > depth_used:
                    depth_used = a_d
                holes.extend(a_h)
            if depth_used > max_depth:
                raise FormatError(f"frame definition depth {depth_used} > MaxDepth {max_depth}")
            return {"kind": "CALL", "group": group, "fid": sub_f["fid"], "sub_shift": sub_s, "args": args}, has_regs, depth_used, holes

        if mode != 0:
            raise FormatError(f"illegal template mode {mode}")

        # Base AST node in definition mode
        if group == "EXPR":
            code = helper.sym(ctx)
            if code < 0 or code >= NUM_BASE_EXPR:
                raise FormatError(f"illegal EXPR tag {code} inside frame definition")
            tag = EXPR_TAGS[code]
            atoms: Any = ()
            ch_specs: list[tuple[str, str]] = []
            has_regs = False
            if tag == "Reg8":
                atoms = (helper.sym("REG_SLOT"),)
                has_regs = True
            elif tag == "RegFar":
                atoms = (8 + helper.read_uint(),)
            elif tag == "FreeId":
                atoms = (helper.read_pooled("FREE_ID", "free"),)
            elif tag == "NumLit":
                atoms = (helper.read_pooled("NUM_LIT", "num"),)
            elif tag == "StrLit":
                atoms = (helper.read_pooled("STR_LIT", "str"),)
            elif tag in ("BoolFalse", "BoolTrue", "NullLit", "This", "Super"):
                pass
            elif tag == "Binary":
                atoms = (BIN_OPS[helper.sym("BIN_OP")],)
                ch_specs = [("EXPR", "EXPR_BIN_L"), ("EXPR", "EXPR_BIN_R")]
            elif tag == "Logical":
                atoms = (LOG_OPS[helper.sym("LOG_OP")],)
                ch_specs = [("EXPR", "EXPR_BIN_L"), ("EXPR", "EXPR_BIN_R")]
            elif tag == "Assign":
                atoms = (ASN_OPS[helper.sym("ASN_OP")],)
                ch_specs = [("EXPR", "EXPR_LHS"), ("EXPR", "EXPR_INIT")]
            elif tag == "Unary":
                atoms = (UN_OPS[helper.sym("UN_OP")],)
                ch_specs = [("EXPR", "EXPR_OTHER")]
            elif tag == "Update":
                atoms = UPD_OPS[helper.sym("UPD_OP")]
                ch_specs = [("EXPR", "EXPR_LHS")]
            elif tag == "Cond":
                ch_specs = [("EXPR", "EXPR_TEST"), ("EXPR", "EXPR_OTHER"), ("EXPR", "EXPR_OTHER")]
            elif tag == "MemberProp":
                opt = bool(helper.sym("OPT_CHAIN"))
                c0, hr0, d0, h0 = decode_tpl("EXPR", "EXPR_OBJ", True)
                prop = helper.read_pooled("PROP_NAME", "prop")
                return ({"kind": "NODE", "group": "EXPR", "tag": "MemberProp", "atoms": (opt, prop), "children": [c0]},
                        hr0, max(1, d0), h0)
            elif tag == "MemberComp":
                atoms = (bool(helper.sym("OPT_CHAIN")),)
                ch_specs = [("EXPR", "EXPR_OBJ"), ("EXPR", "EXPR_PROP_IDX")]
            elif tag == "Call":
                opt = bool(helper.sym("OPT_CHAIN"))
                c0, hr0, d0, h0 = decode_tpl("EXPR", "EXPR_CALLEE", True)
                na = helper.read_list_len("LIST_LEN_ARGS", 8)
                children = [c0]
                hr = hr0
                md = max(1, d0)
                hs = list(h0)
                for _ in range(na):
                    ci, hri, di, hi = decode_tpl("EXPR", "EXPR_ARG", True)
                    children.append(ci)
                    hr = hr or hri
                    md = max(md, di)
                    hs.extend(hi)
                return {"kind": "NODE", "group": "EXPR", "tag": "Call", "atoms": (opt, na), "children": children}, hr, md, hs
            elif tag == "New":
                c0, hr0, d0, h0 = decode_tpl("EXPR", "EXPR_CALLEE", True)
                na = helper.read_list_len("LIST_LEN_ARGS", 8)
                children = [c0]
                hr = hr0
                md = max(1, d0)
                hs = list(h0)
                for _ in range(na):
                    ci, hri, di, hi = decode_tpl("EXPR", "EXPR_ARG", True)
                    children.append(ci)
                    hr = hr or hri
                    md = max(md, di)
                    hs.extend(hi)
                return {"kind": "NODE", "group": "EXPR", "tag": "New", "atoms": (na,), "children": children}, hr, md, hs
            elif tag == "ArrayExpr":
                ne = helper.read_list_len("LIST_LEN_ARGS", 8)
                flags = []
                children = []
                hr = False
                md = 1
                hs = []
                for _ in range(ne):
                    fl = helper.sym("OPT_FLAG")
                    flags.append(fl)
                    if fl:
                        ci, hri, di, hi = decode_tpl("EXPR", "EXPR_OTHER", True)
                        children.append(ci)
                        hr = hr or hri
                        md = max(md, di)
                        hs.extend(hi)
                return {"kind": "NODE", "group": "EXPR", "tag": "ArrayExpr", "atoms": (tuple(flags),), "children": children}, hr, md, hs
            elif tag == "Sequence":
                ne = helper.read_list_len("LIST_LEN_ARGS", 8)
                atoms = (ne,)
                ch_specs = [("EXPR", "EXPR_OTHER")] * ne
            elif tag == "Spread":
                ch_specs = [("EXPR", "EXPR_ARG")]
            elif tag == "Await":
                ch_specs = [("EXPR", "EXPR_OTHER")]
            else:
                raise FormatError(f"unsupported EXPR tag {tag} in frame definition")

            children = []
            md = 1
            hs = []
            for cg, cctx in ch_specs:
                ci, hri, di, hi = decode_tpl(cg, cctx, True)
                children.append(ci)
                has_regs = has_regs or hri
                md = max(md, di)
                hs.extend(hi)
            return {"kind": "NODE", "group": "EXPR", "tag": tag, "atoms": atoms, "children": children}, has_regs, md, hs

        # STMT base node in definition mode
        code = helper.sym(ctx)
        if code < 0 or code >= NUM_BASE_STMT:
            raise FormatError(f"illegal STMT tag {code} inside frame definition")
        tag = STMT_TAGS[code]
        if tag == "ExprStmt":
            c0, hr, d, hs = decode_tpl("EXPR", "EXPR_STMT", True)
            return {"kind": "NODE", "group": "STMT", "tag": "ExprStmt", "atoms": (), "children": [c0]}, hr, max(1, d), hs
        if tag == "VarDecl":
            kind = VAR_KINDS[helper.sym("VAR_KIND")]
            nd = helper.read_list_len("LIST_LEN_DECL", 3)
            if nd != 1:
                raise FormatError("frame VarDecl must have 1 declarator")
            pt = PAT_TAGS[helper.sym("PAT_DECL")]
            if pt != "BindCanon":
                raise FormatError("frame VarDecl must use BindCanon")
            has_init = bool(helper.sym("OPT_INIT"))
            if has_init:
                c0, hr, d, hs = decode_tpl("EXPR", "EXPR_INIT", True)
                return {"kind": "NODE", "group": "STMT", "tag": "VarDecl", "atoms": (kind, True), "children": [c0]}, hr, max(1, d), hs
            return {"kind": "NODE", "group": "STMT", "tag": "VarDecl", "atoms": (kind, False), "children": []}, False, 1, []
        if tag == "Block":
            ns = helper.read_list_len("LIST_LEN_STMT", 16)
            children, hr, md, hs = [], False, 1, []
            for _ in range(ns):
                ci, hri, di, hi = decode_tpl("STMT", "STMT_BLOCK", True)
                children.append(ci)
                hr = hr or hri
                md = max(md, di)
                hs.extend(hi)
            return {"kind": "NODE", "group": "STMT", "tag": "Block", "atoms": (ns,), "children": children}, hr, md, hs
        if tag == "If":
            c0, hr0, d0, h0 = decode_tpl("EXPR", "EXPR_TEST", True)
            c1, hr1, d1, h1 = decode_tpl("STMT", "STMT_BRANCH", True)
            has_alt = bool(helper.sym("OPT_ELSE"))
            children = [c0, c1]
            hr = hr0 or hr1
            md = max(1, d0, d1)
            hs = list(h0) + list(h1)
            if has_alt:
                c2, hr2, d2, h2 = decode_tpl("STMT", "STMT_BRANCH", True)
                children.append(c2)
                hr = hr or hr2
                md = max(md, d2)
                hs.extend(h2)
            return {"kind": "NODE", "group": "STMT", "tag": "If", "atoms": (has_alt,), "children": children}, hr, md, hs
        if tag == "Return":
            has_arg = bool(helper.sym("OPT_RET_ARG"))
            if has_arg:
                c0, hr, d, hs = decode_tpl("EXPR", "EXPR_ARG", True)
                return {"kind": "NODE", "group": "STMT", "tag": "Return", "atoms": (True,), "children": [c0]}, hr, max(1, d), hs
            return {"kind": "NODE", "group": "STMT", "tag": "Return", "atoms": (False,), "children": []}, False, 1, []
        if tag == "For":
            ik = helper.sym("FOR_INIT_KIND")
            children, hr, md, hs = [], False, 1, []
            if ik == 1:
                ci, hri, di, hi = decode_tpl("STMT", "STMT_BLOCK", True)
                children.append(ci); hr = hr or hri; md = max(md, di); hs.extend(hi)
            elif ik == 2:
                ci, hri, di, hi = decode_tpl("EXPR", "EXPR_STMT", True)
                children.append(ci); hr = hr or hri; md = max(md, di); hs.extend(hi)
            ht = bool(helper.sym("OPT_FLAG"))
            if ht:
                ci, hri, di, hi = decode_tpl("EXPR", "EXPR_TEST", True)
                children.append(ci); hr = hr or hri; md = max(md, di); hs.extend(hi)
            hu = bool(helper.sym("OPT_FLAG"))
            if hu:
                ci, hri, di, hi = decode_tpl("EXPR", "EXPR_STMT", True)
                children.append(ci); hr = hr or hri; md = max(md, di); hs.extend(hi)
            cb, hrb, db, hb = decode_tpl("STMT", "STMT_BRANCH", True)
            children.append(cb); hr = hr or hrb; md = max(md, db); hs.extend(hb)
            return {"kind": "NODE", "group": "STMT", "tag": "For", "atoms": (ik, ht, hu), "children": children}, hr, md, hs
        if tag == "ForOf":
            is_aw = bool(helper.sym("OPT_FLAG"))
            ld = bool(helper.sym("OPT_FLAG"))
            c0, hr0, d0, h0 = decode_tpl("STMT" if ld else "EXPR", "STMT_BLOCK" if ld else "EXPR_LHS", True)
            c1, hr1, d1, h1 = decode_tpl("EXPR", "EXPR_OTHER", True)
            c2, hr2, d2, h2 = decode_tpl("STMT", "STMT_BRANCH", True)
            return ({"kind": "NODE", "group": "STMT", "tag": "ForOf", "atoms": (is_aw, ld), "children": [c0, c1, c2]},
                    hr0 or hr1 or hr2, max(1, d0, d1, d2), h0 + h1 + h2)
        if tag == "ForIn":
            ld = bool(helper.sym("OPT_FLAG"))
            c0, hr0, d0, h0 = decode_tpl("STMT" if ld else "EXPR", "STMT_BLOCK" if ld else "EXPR_LHS", True)
            c1, hr1, d1, h1 = decode_tpl("EXPR", "EXPR_OTHER", True)
            c2, hr2, d2, h2 = decode_tpl("STMT", "STMT_BRANCH", True)
            return ({"kind": "NODE", "group": "STMT", "tag": "ForIn", "atoms": (ld,), "children": [c0, c1, c2]},
                    hr0 or hr1 or hr2, max(1, d0, d1, d2), h0 + h1 + h2)
        if tag == "While":
            c0, hr0, d0, h0 = decode_tpl("EXPR", "EXPR_TEST", True)
            c1, hr1, d1, h1 = decode_tpl("STMT", "STMT_BRANCH", True)
            return {"kind": "NODE", "group": "STMT", "tag": "While", "atoms": (), "children": [c0, c1]}, hr0 or hr1, max(1, d0, d1), h0 + h1
        if tag == "DoWhile":
            c0, hr0, d0, h0 = decode_tpl("STMT", "STMT_BRANCH", True)
            c1, hr1, d1, h1 = decode_tpl("EXPR", "EXPR_TEST", True)
            return {"kind": "NODE", "group": "STMT", "tag": "DoWhile", "atoms": (), "children": [c0, c1]}, hr0 or hr1, max(1, d0, d1), h0 + h1
        if tag == "Throw":
            c0, hr, d, hs = decode_tpl("EXPR", "EXPR_ARG", True)
            return {"kind": "NODE", "group": "STMT", "tag": "Throw", "atoms": (), "children": [c0]}, hr, max(1, d), hs
        if tag in ("Break", "Continue"):
            lbl = helper.read_pooled("BIND_NAME", "bind") if helper.sym("OPT_FLAG") else None
            return {"kind": "NODE", "group": "STMT", "tag": tag, "atoms": (lbl,), "children": []}, False, 1, []
        if tag == "Empty":
            return {"kind": "NODE", "group": "STMT", "tag": "Empty", "atoms": (), "children": []}, False, 1, []
        raise FormatError(f"unsupported STMT tag {tag} in frame definition")

    total_frames = f_e + f_s
    for _ in range(total_frames):
        g_bit = dec.decode_uniform(2)
        group = "EXPR" if g_bit == 0 else "STMT"
        root_ctx = "EXPR_OTHER" if group == "EXPR" else "STMT_BLOCK"
        tpl, has_regs, def_depth, holes = decode_tpl(group, root_ctx, False)
        if def_depth < 1 or def_depth > max_depth:
            raise FormatError(f"decoded frame def_depth {def_depth} outside 1..{max_depth}")
        flist = expr_frames if group == "EXPR" else stmt_frames
        frec = {
            "group": group,
            "fid": len(flist),
            "tpl": tpl,
            "has_regs": has_regs,
            "def_depth": def_depth,
            "holes": holes,
        }
        flist.append(frec)
        if def_depth < max_depth:
            prev_eligible[group].append(frec)

    if len(expr_frames) != f_e or len(stmt_frames) != f_s:
        raise FormatError(f"frame counts mismatch: got ({len(expr_frames)},{len(stmt_frames)}) expected ({f_e},{f_s})")
    return expr_frames, stmt_frames


# ---------------------------------------------------------------------------
# Top-Level Independent Archive Decode
# ---------------------------------------------------------------------------

def unparse_asts_batch(ast_items: list[tuple[int, dict]]) -> dict[int, bytes]:
    if not ast_items:
        return {}
    req = {"items": [{"id": str(idx), "ir": ast} for idx, ast in ast_items]}
    proc = subprocess.run(
        ["node", str(HERE / "js_normalize_ast.mjs"), "unparse_ir"],
        input=json.dumps(req),
        capture_output=True,
        text=True,
        check=True,
    )
    resp = json.loads(proc.stdout)["results"]
    out: dict[int, bytes] = {}
    for row in resp:
        if not row["ok"]:
            raise FormatError(f"unparse_ir failed on file {row['id']}: {row['error']}")
        out[int(row["id"])] = row["source"].encode("utf-8")
    return out


def decode_archive(buf: bytes) -> dict[str, Any]:
    """Decode any A2F1 archive completely from bytes alone."""
    t_total_0 = time.perf_counter()
    if len(buf) < 6 or buf[:4] != MAGIC:
        raise FormatError("bad magic or truncated archive")
    codec_kind = buf[4]
    max_depth = buf[5]
    pos = 6

    if codec_kind == 0:
        if max_depth != 0:
            raise FormatError(f"Flat BITS expects max_depth=0, got {max_depth}")
        n, pos = read_varint(buf, pos)
        entries = []
        for _ in range(n):
            if pos >= len(buf):
                raise FormatError("truncated flat dictionary")
            ln = buf[pos]
            pos += 1
            if not 1 <= ln <= 32 or pos + ln > len(buf):
                raise FormatError(f"invalid entry length {ln}")
            entries.append(buf[pos:pos + ln])
            pos += ln
        cum, pos = read_table(buf, pos, n + 2)
        header_bytes = pos
        file_count, pos = read_varint(buf, pos)
        payload = buf[pos:]
        dec = ArithmeticDecoder(payload)
        esc, eof = n, n + 1
        files: list[bytes] = []
        per_file_sec: list[float] = []
        tokens = 0
        escapes = 0
        for _ in range(file_count):
            tf0 = time.perf_counter()
            cur = bytearray()
            while True:
                s = dec.decode(cum)
                if s == eof:
                    break
                tokens += 1
                if s == esc:
                    cur.append(dec.decode_uniform(256))
                    escapes += 1
                elif 0 <= s < n:
                    cur += entries[s]
                else:
                    raise FormatError(f"invalid flat symbol {s}")
            files.append(bytes(cur))
            per_file_sec.append(time.perf_counter() - tf0)
        return {
            "codec_kind": 0,
            "max_depth": 0,
            "header_bytes": header_bytes,
            "payload_bytes": len(payload),
            "archive_bytes": len(buf),
            "file_count": file_count,
            "files": files,
            "tokens": tokens,
            "escapes": escapes,
            "fallback_files": 0,
            "frame_calls": 0,
            "nested_calls": 0,
            "decode_seconds": time.perf_counter() - t_total_0,
            "stream_per_file_seconds": per_file_sec,
            "ac_symbols": dec.sym_count,
        }

    if codec_kind != 1:
        raise FormatError(f"unknown codec_kind {codec_kind}")
    if max_depth > 16:
        raise FormatError(f"unreasonable max_depth {max_depth}")

    # Read 5 pools
    pools: dict[str, list[str]] = {}
    for pk in ("prop", "free", "bind", "num", "str"):
        cnt, pos = read_varint(buf, pos)
        lst = []
        for _ in range(cnt):
            s, pos = read_ustr(buf, pos)
            lst.append(s)
        pools[pk] = lst

    has_frames = max_depth >= 1
    expr_sz = NUM_BASE_EXPR + (1 if has_frames else 0)
    stmt_sz = NUM_BASE_STMT + (1 if has_frames else 0)
    specs: list[tuple[str, int]] = [("FILE_MODE", 2)]
    for c in EXPR_CONTEXTS:
        specs.append((c, expr_sz))
    for c in STMT_CONTEXTS:
        specs.append((c, stmt_sz))
    specs.extend(AUX_CONTEXT_SIZES)
    specs.append(("PROP_NAME", len(pools["prop"]) + 1))
    specs.append(("FREE_ID", len(pools["free"]) + 1))
    specs.append(("BIND_NAME", len(pools["bind"]) + 1))
    specs.append(("NUM_LIT", len(pools["num"]) + 1))
    specs.append(("STR_LIT", len(pools["str"]) + 1))
    specs.append(("INLINE_BYTE", 256))

    cums: dict[str, list[int]] = {}
    for ctx, sz in specs:
        cums[ctx], pos = read_table(buf, pos, sz)

    expr_frames: list[dict] = []
    stmt_frames: list[dict] = []
    if has_frames:
        f_e, pos = read_varint(buf, pos)
        f_s, pos = read_varint(buf, pos)
        if f_e > 0:
            cums["EXPR_FRAME_ID"], pos = read_table(buf, pos, f_e)
        if f_s > 0:
            cums["STMT_FRAME_ID"], pos = read_table(buf, pos, f_s)
        cums["REG_SHIFT"], pos = read_table(buf, pos, 8)
        dm_k = 3 if max_depth >= 2 else 2
        dm_cum, pos = read_table(buf, pos, dm_k)
        def_mode_w = [dm_cum[i + 1] - dm_cum[i] for i in range(dm_k)]
        def_len, pos = read_varint(buf, pos)
        if pos + def_len > len(buf):
            raise FormatError("truncated frame definition block")
        def_blob = buf[pos:pos + def_len]
        pos += def_len
        expr_frames, stmt_frames = decode_frame_definitions(def_blob, f_e, f_s, max_depth, cums, def_mode_w, pools)

    header_bytes = pos
    file_count, pos = read_varint(buf, pos)
    payload = buf[pos:]
    dec = ArithmeticDecoder(payload)
    ast_dec = AstStreamDecoder(dec, cums, pools, max_depth, expr_frames, stmt_frames)

    raw_by_idx: dict[int, bytes] = {}
    asts_to_unparse: list[tuple[int, dict]] = []
    per_file_stream_sec: list[float] = []
    fallback_files = 0

    for i in range(file_count):
        tf0 = time.perf_counter()
        mode = ast_dec.sym("FILE_MODE")
        if mode == 1:
            fallback_files += 1
            ln = ast_dec.read_uint()
            raw_by_idx[i] = bytes(ast_dec.sym("INLINE_BYTE") for _ in range(ln))
        elif mode == 0:
            ast_dec.env = DecoderEnv()
            nstmts = ast_dec.read_list_len("LIST_LEN_STMT", 16)
            body = [ast_dec.decode_stmt("STMT_TOP") for _ in range(nstmts)]
            asts_to_unparse.append((i, {"type": "Program", "body": body}))
        else:
            raise FormatError(f"invalid FILE_MODE {mode}")
        per_file_stream_sec.append(time.perf_counter() - tf0)

    t_unparse0 = time.perf_counter()
    unparsed = unparse_asts_batch(asts_to_unparse)
    t_unparse = time.perf_counter() - t_unparse0
    per_ast_unparse = t_unparse / max(1, len(asts_to_unparse))

    files: list[bytes] = []
    per_file_total_sec: list[float] = []
    for i in range(file_count):
        if i in raw_by_idx:
            files.append(raw_by_idx[i])
            per_file_total_sec.append(per_file_stream_sec[i])
        else:
            files.append(unparsed[i])
            per_file_total_sec.append(per_file_stream_sec[i] + per_ast_unparse)

    return {
        "codec_kind": 1,
        "max_depth": max_depth,
        "header_bytes": header_bytes,
        "payload_bytes": len(payload),
        "archive_bytes": len(buf),
        "file_count": file_count,
        "files": files,
        "expr_frames": len(expr_frames),
        "stmt_frames": len(stmt_frames),
        "nested_frame_defs": sum(1 for f in expr_frames + stmt_frames if f["def_depth"] >= 2),
        "fallback_files": fallback_files,
        "frame_calls": ast_dec.frame_calls_executed,
        "nested_calls": ast_dec.nested_calls_executed,
        "decode_seconds": time.perf_counter() - t_total_0,
        "unparse_seconds": t_unparse,
        "stream_per_file_seconds": per_file_total_sec,
        "ac_symbols": dec.sym_count,
    }
