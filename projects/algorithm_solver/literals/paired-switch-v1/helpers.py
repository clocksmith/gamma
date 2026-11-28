"""Tested helper implementations and boundary-behavior contracts for BITS paired-switch-v1.

Every experimental arm (frozen alias, score-only alias, score-and-input alias,
and ordinary named function baseline) executes the exact same tested helper
implementation recorded here.

Train development helpers (DEV_PROBLEMS):
  1. advance_rle_block     (family: run_codec)
  2. apply_weighted_span   (family: interval_algebra)
  3. step_frame_parser     (family: protocol_fsm)

Disjoint validation development helpers (DEV_VAL_PROBLEMS):
  4. parse_semver_key      (family: version_semver)
  5. shift_business_day    (family: calendar_business)
  6. eval_safe_op          (family: expr_rpn_vm)

Legacy mechanical verification helper:
  - skip_equal (retained strictly for Section 1-3 offline mechanical fixture/roundtrip checks)
"""

from __future__ import annotations

import hashlib
import inspect
import re
from dataclasses import dataclass
from typing import Any, Callable


def skip_equal(xs: list[Any], i: int) -> int:
    """Return the first index > i where xs[j] != xs[i], or len(xs) if at/past end."""
    n = len(xs)
    if not isinstance(i, int) or isinstance(i, bool) or i < 0:
        raise ValueError("index i must be a non-negative integer")
    if i >= n:
        return n
    val = xs[i]
    j = i + 1
    while j < n and xs[j] == val:
        j += 1
    return j


def advance_rle_block(tokens: list[int], i: int, escape_tok: int) -> tuple[int, int | None, int]:
    """Decode one block starting at index i in an escaped RLE integer stream.

    Protocol rules:
    - If i >= len(tokens): return (len(tokens), None, 0).
    - If tokens[i] != escape_tok: literal value with count 1 -> (i + 1, tokens[i], 1).
    - If tokens[i] == escape_tok:
      * If i + 1 >= len(tokens) (dangling escape): literal escape_tok -> (len(tokens), escape_tok, 1).
      * If tokens[i + 1] == escape_tok (doubled escape): literal escape_tok -> (i + 2, escape_tok, 1).
      * Otherwise val = tokens[i + 1]:
        - If i + 2 >= len(tokens) (truncated run missing count): literal val -> (len(tokens), val, 1).
        - Else cnt = tokens[i + 2]:
          * If cnt <= 0: skip 3-token directive -> (i + 3, val, 0).
          * Else: emit run -> (i + 3, val, cnt).
    """
    n = len(tokens)
    if not isinstance(i, int) or isinstance(i, bool) or i < 0:
        raise ValueError("index i must be a non-negative integer")
    if i >= n:
        return (n, None, 0)
    cur = tokens[i]
    if cur != escape_tok:
        return (i + 1, cur, 1)
    if i + 1 >= n:
        return (n, escape_tok, 1)
    nxt = tokens[i + 1]
    if nxt == escape_tok:
        return (i + 2, escape_tok, 1)
    if i + 2 >= n:
        return (n, nxt, 1)
    cnt = tokens[i + 2]
    if cnt <= 0:
        return (i + 3, nxt, 0)
    return (i + 3, nxt, cnt)


def apply_weighted_span(
    acc: list[list[int]],
    start: int,
    end: int,
    delta: int,
) -> list[list[int]]:
    """Add delta over half-open interval [start, end) into canonical piecewise-constant map acc.

    Canonical invariant for returned list of [s, e, w]:
    - s < e and w != 0 for every segment
    - sorted and disjoint (e_k <= s_{k+1})
    - adjacent segments with e_k == s_{k+1} and w_k == w_{k+1} are coalesced
    - zero-weight segments resulting from cancellation are removed
    """
    pts_set: set[int] = set()
    for s, e, _w in acc:
        if s < e:
            pts_set.add(s)
            pts_set.add(e)
    active_update = start < end and delta != 0
    if active_update:
        pts_set.add(start)
        pts_set.add(end)
    if not pts_set:
        return []
    pts = sorted(pts_set)
    out: list[list[int]] = []
    for k in range(len(pts) - 1):
        a = pts[k]
        b = pts[k + 1]
        if a >= b:
            continue
        w = delta if (active_update and start <= a and b <= end) else 0
        for s, e, sw in acc:
            if s <= a and b <= e:
                w += sw
        if w == 0:
            continue
        if out and out[-1][1] == a and out[-1][2] == w:
            out[-1][1] = b
        else:
            out.append([a, b, w])
    return out


def step_frame_parser(
    state: tuple[str, bool, list[int]],
    byte_val: int,
) -> tuple[tuple[str, bool, list[int]], list[int] | None]:
    """Advance byte-oriented framed packet parser (START=126, END=127, ESC=125, XOR=32).

    State is (mode, escaped, buf) initialized as ("IDLE", False, []).
    - In IDLE: ignore bytes until 126 (START) -> ("IN_FRAME", False, []).
    - In IN_FRAME:
      * If escaped: append (byte_val ^ 32), escaped=False.
      * Else if byte_val == 125 (ESC): escaped=True.
      * Else if byte_val == 126 (START): resync, discard partial buf -> ("IN_FRAME", False, []).
      * Else if byte_val == 127 (END): finalize frame and return to ("IDLE", False, []).
        Valid iff len(buf) >= 2 and XOR(buf[:-1]) == buf[-1]; emits buf[:-1] if valid else None.
      * Else: append byte_val to buf.
    """
    mode, escaped, raw_buf = state
    buf = list(raw_buf)
    if mode == "IDLE":
        if byte_val == 126:
            return (("IN_FRAME", False, []), None)
        return (("IDLE", False, []), None)
    if escaped:
        buf.append(byte_val ^ 32)
        return (("IN_FRAME", False, buf), None)
    if byte_val == 125:
        return (("IN_FRAME", True, buf), None)
    if byte_val == 126:
        return (("IN_FRAME", False, []), None)
    if byte_val == 127:
        if len(buf) >= 2:
            chk = 0
            for b in buf[:-1]:
                chk ^= b
            if chk == buf[-1]:
                return (("IDLE", False, []), buf[:-1])
        return (("IDLE", False, []), None)
    buf.append(byte_val)
    return (("IN_FRAME", False, buf), None)


def parse_semver_key(ver_str: str) -> tuple[bool, tuple[Any, ...]]:
    """Parse strict SemVer 2.0 string into (valid, comparable_precedence_key).

    Rules enforced:
    - MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
    - Core numbers: non-negative ASCII digits with no leading zeros (except "0").
    - Build metadata (+...): validated as dot-separated [0-9A-Za-z-]+ and ignored in precedence.
    - Prerelease (-...): dot-separated non-empty [0-9A-Za-z-]+ identifiers; numeric
      identifiers must have no leading zeros, sort numerically as (0, int(id)), and have
      lower precedence than alphanumeric identifiers (1, id).
    - Release versions have pre_rank=1; prereleases have pre_rank=0 (so release > prerelease).
    - Returns (True, (major, minor, patch, pre_rank, pre_parts)) or (False, ()).
    """
    if not isinstance(ver_str, str) or not ver_str:
        return (False, ())
    core_pre = ver_str
    if "+" in core_pre:
        core_pre, build = core_pre.split("+", 1)
        if not build:
            return (False, ())
        for part in build.split("."):
            if not part or not all(c.isalnum() or c == "-" for c in part):
                return (False, ())
    pre_str: str | None = None
    if "-" in core_pre:
        core_str, pre_str = core_pre.split("-", 1)
        if not pre_str:
            return (False, ())
    else:
        core_str = core_pre
    core_parts = core_str.split(".")
    if len(core_parts) != 3:
        return (False, ())
    nums: list[int] = []
    for p in core_parts:
        if not p or not p.isdigit() or not p.isascii():
            return (False, ())
        if len(p) > 1 and p[0] == "0":
            return (False, ())
        nums.append(int(p))
    if pre_str is None:
        return (True, (nums[0], nums[1], nums[2], 1, ()))
    pre_items: list[tuple[int, Any]] = []
    for p in pre_str.split("."):
        if not p or not all(c.isalnum() or c == "-" for c in p) or not p.isascii():
            return (False, ())
        if p.isdigit():
            if len(p) > 1 and p[0] == "0":
                return (False, ())
            pre_items.append((0, int(p)))
        else:
            pre_items.append((1, p))
    return (True, (nums[0], nums[1], nums[2], 0, tuple(pre_items)))


def shift_business_day(
    ymd: list[int],
    delta_days: int,
    holidays: list[list[int]],
) -> list[int]:
    """Shift proleptic Gregorian date [year, month, day] by delta_days business days.

    Skips Saturdays, Sundays, and dates in holidays ([y, m, d]).
    - delta_days == 0: if ymd is a weekend or holiday, snap forward to next business day; else keep ymd.
    - delta_days > 0: advance delta_days business days forward.
    - delta_days < 0: step |delta_days| business days backward.
    """
    def _to_ord(y: int, m: int, d: int) -> int:
        yy = y - (1 if m <= 2 else 0)
        era = yy // 400
        yoe = yy - era * 400
        doy = (153 * (m + (9 if m <= 2 else -3)) + 2) // 5 + d - 1
        doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
        return era * 146097 + doe - 719468

    def _from_ord(z: int) -> list[int]:
        zz = z + 719468
        era = zz // 146097
        doe = zz - era * 146097
        yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
        y = yoe + era * 400
        doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
        mp = (5 * doy + 2) // 153
        d = doy - (153 * mp + 2) // 5 + 1
        m = mp + (3 if mp < 10 else -9)
        y += 1 if m <= 2 else 0
        return [y, m, d]

    hol_ords = {_to_ord(h[0], h[1], h[2]) for h in holidays}

    def _is_biz(o: int) -> bool:
        return ((o + 3) % 7) < 5 and o not in hol_ords

    cur = _to_ord(ymd[0], ymd[1], ymd[2])
    if delta_days == 0:
        while not _is_biz(cur):
            cur += 1
        return _from_ord(cur)
    step = 1 if delta_days > 0 else -1
    rem = abs(delta_days)
    while rem > 0:
        cur += step
        if _is_biz(cur):
            rem -= 1
    return _from_ord(cur)


def eval_safe_op(
    stack: list[int],
    op_tok: str,
    env: dict[str, int],
) -> tuple[bool, list[int]]:
    """Execute one guarded saturating RPN VM token on stack with environment env.

    All pushed numeric results are saturated to [-10000, 10000].
    Supported tokens:
    - integer literal (optional leading '-'): push clamped int
    - '$name': push clamped env[name] (fails if missing)
    - DUP, SWAP, DROP: stack operations (fail on underflow)
    - ADD, SUB, MUL: binary ops (pop b then a, push clamped result)
    - DIV: truncating division toward zero int(a / b) (fails if b == 0)
    - CLAMP: pop hi, lo, x; fail if lo > hi; else push clamped min(max(x, lo), hi)
    Returns (ok, next_stack).
    """
    st = list(stack)

    def _sat(v: int) -> int:
        if v > 10000:
            return 10000
        if v < -10000:
            return -10000
        return v

    if op_tok.isdigit() or (op_tok.startswith("-") and len(op_tok) > 1 and op_tok[1:].isdigit()):
        st.append(_sat(int(op_tok)))
        return (True, st)
    if op_tok.startswith("$"):
        key = op_tok[1:]
        if key not in env:
            return (False, st)
        st.append(_sat(int(env[key])))
        return (True, st)
    if op_tok == "DUP":
        if len(st) < 1:
            return (False, st)
        st.append(st[-1])
        return (True, st)
    if op_tok == "DROP":
        if len(st) < 1:
            return (False, st)
        st.pop()
        return (True, st)
    if op_tok == "SWAP":
        if len(st) < 2:
            return (False, st)
        st[-1], st[-2] = st[-2], st[-1]
        return (True, st)
    if op_tok in ("ADD", "SUB", "MUL", "DIV"):
        if len(st) < 2:
            return (False, st)
        b = st.pop()
        a = st.pop()
        if op_tok == "ADD":
            st.append(_sat(a + b))
        elif op_tok == "SUB":
            st.append(_sat(a - b))
        elif op_tok == "MUL":
            st.append(_sat(a * b))
        else:
            if b == 0:
                return (False, st)
            st.append(_sat(int(a / b)))
        return (True, st)
    if op_tok == "CLAMP":
        if len(st) < 3:
            return (False, st)
        hi = st.pop()
        lo = st.pop()
        x = st.pop()
        if lo > hi:
            return (False, st)
        st.append(_sat(min(max(x, lo), hi)))
        return (True, st)
    return (False, st)


@dataclass(frozen=True)
class HelperSpec:
    name: str
    family: str
    signature: str
    call_template: str
    description: str
    operand_convention: str
    syntax_mask_regex: str
    implementation: Callable[..., Any]
    boundary_cases: tuple[dict[str, Any], ...]

    def source_code(self) -> str:
        return inspect.getsource(self.implementation)

    def implementation_sha256(self) -> str:
        return hashlib.sha256(self.source_code().encode("utf-8")).hexdigest()

    def exposure_block(self, operator_symbol: str) -> str:
        """Render the exact matched switch-time exposure block for any arm."""
        call_expr = self.call_template.format(OP=operator_symbol)
        lines = [
            f"HELPER_OPERATOR: {operator_symbol}",
            f"CALL_CONVENTION: {call_expr}",
            f"DESCRIPTION: {self.description}",
            f"OPERAND_CONVENTION: {self.operand_convention.format(OP=operator_symbol)}",
            "BOUNDARY_BEHAVIOR:",
        ]
        for case in self.boundary_cases:
            lines.append(
                f"  - {case['label']}: {operator_symbol}({case['args_repr']}) -> {case['expected_repr']}"
            )
        lines.append(f"SYNTAX_MASK: {self.syntax_mask_regex.format(OP=operator_symbol)}")
        return "\n".join(lines)


HELPER_SPECS: dict[str, HelperSpec] = {
    "skip_equal": HelperSpec(
        name="skip_equal",
        family="legacy_mechanical_fixture",
        signature="skip_equal(xs, i) -> int",
        call_template="j = {OP}(xs, i)",
        description=(
            "Given sequence xs and non-negative index i, return the smallest index j > i "
            "with xs[j] != xs[i], or len(xs) when i >= len(xs) or the equal run reaches the end."
        ),
        operand_convention=(
            "Assign result via `j = {OP}(xs, i)` with sequence `xs` and integer index `i`."
        ),
        syntax_mask_regex=r"[A-Za-z_][A-Za-z0-9_]*\s*=\s*{OP}\([^,()]+,\s*[^,()]+\)",
        implementation=skip_equal,
        boundary_cases=(
            {"label": "empty_suffix_empty_list", "args": ([], 0), "args_repr": "[], 0", "expected": 0, "expected_repr": "0"},
            {"label": "run_of_duplicates_prefix", "args": ([2, 2, 2, 5], 0), "args_repr": "[2, 2, 2, 5], 0", "expected": 3, "expected_repr": "3"},
            {"label": "end_of_array_duplicate_tail", "args": ([1, 3, 3], 1), "args_repr": "[1, 3, 3], 1", "expected": 3, "expected_repr": "3"},
        ),
    ),
    "advance_rle_block": HelperSpec(
        name="advance_rle_block",
        family="run_codec",
        signature="advance_rle_block(tokens, i, escape_tok) -> tuple[int, int | None, int]",
        call_template="i, val, cnt = {OP}(tokens, i, escape_tok)",
        description=(
            "Decode one escaped-RLE block from integer stream `tokens` starting at index `i` with "
            "sentinel `escape_tok`. Handles literal tokens, dangling trailing escape, doubled escape "
            "literal, truncated run missing count, zero/negative-count skipped directives, and valid runs."
        ),
        operand_convention=(
            "Unpack via `i, val, cnt = {OP}(tokens, i, escape_tok)` with list `tokens`, index `i`, "
            "and integer sentinel `escape_tok`."
        ),
        syntax_mask_regex=r"[A-Za-z_][A-Za-z0-9_]*\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*{OP}\([^,()]+,\s*[^,()]+,\s*[^,()]+\)",
        implementation=advance_rle_block,
        boundary_cases=(
            {"label": "end_of_stream", "args": ([7], 1, -1), "args_repr": "[7], 1, -1", "expected": (1, None, 0), "expected_repr": "(1, None, 0)"},
            {"label": "doubled_escape_literal", "args": ([-1, -1, 5], 0, -1), "args_repr": "[-1, -1, 5], 0, -1", "expected": (2, -1, 1), "expected_repr": "(2, -1, 1)"},
            {"label": "dangling_escape_eof", "args": ([3, -1], 1, -1), "args_repr": "[3, -1], 1, -1", "expected": (2, -1, 1), "expected_repr": "(2, -1, 1)"},
            {"label": "truncated_run_missing_count", "args": ([-1, 9], 0, -1), "args_repr": "[-1, 9], 0, -1", "expected": (2, 9, 1), "expected_repr": "(2, 9, 1)"},
            {"label": "zero_count_skipped_directive", "args": ([-1, 9, 0, 4], 0, -1), "args_repr": "[-1, 9, 0, 4], 0, -1", "expected": (3, 9, 0), "expected_repr": "(3, 9, 0)"},
            {"label": "valid_run_block", "args": ([-1, 7, 4, 2], 0, -1), "args_repr": "[-1, 7, 4, 2], 0, -1", "expected": (3, 7, 4), "expected_repr": "(3, 7, 4)"},
        ),
    ),
    "apply_weighted_span": HelperSpec(
        name="apply_weighted_span",
        family="interval_algebra",
        signature="apply_weighted_span(acc, start, end, delta) -> list[list[int]]",
        call_template="acc = {OP}(acc, start, end, delta)",
        description=(
            "Add `delta` across half-open span `[start, end)` in canonical piecewise-constant interval "
            "map `acc` (`[[s, e, w], ...]`), splitting overlaps, filling gaps, dropping zero-weight "
            "cancelled spans, and coalescing adjacent segments of equal weight."
        ),
        operand_convention=(
            "Assign canonical map via `acc = {OP}(acc, start, end, delta)` with list `acc` and ints "
            "`start`, `end`, `delta`."
        ),
        syntax_mask_regex=r"[A-Za-z_][A-Za-z0-9_]*\s*=\s*{OP}\([^,()]+,\s*[^,()]+,\s*[^,()]+,\s*[^,()]+\)",
        implementation=apply_weighted_span,
        boundary_cases=(
            {"label": "empty_acc_insert", "args": ([], 1, 5, 3), "args_repr": "[], 1, 5, 3", "expected": [[1, 5, 3]], "expected_repr": "[[1, 5, 3]]"},
            {"label": "overlap_split_and_add", "args": ([[1, 6, 2]], 3, 8, 5), "args_repr": "[[1, 6, 2]], 3, 8, 5", "expected": [[1, 3, 2], [3, 6, 7], [6, 8, 5]], "expected_repr": "[[1, 3, 2], [3, 6, 7], [6, 8, 5]]"},
            {"label": "exact_zero_cancellation", "args": ([[1, 6, 2]], 2, 4, -2), "args_repr": "[[1, 6, 2]], 2, 4, -2", "expected": [[1, 2, 2], [4, 6, 2]], "expected_repr": "[[1, 2, 2], [4, 6, 2]]"},
            {"label": "adjacent_equal_weight_coalesce", "args": ([[1, 3, 4], [5, 8, 4]], 3, 5, 4), "args_repr": "[[1, 3, 4], [5, 8, 4]], 3, 5, 4", "expected": [[1, 8, 4]], "expected_repr": "[[1, 8, 4]]"},
        ),
    ),
    "step_frame_parser": HelperSpec(
        name="step_frame_parser",
        family="protocol_fsm",
        signature="step_frame_parser(state, byte_val) -> tuple[tuple[str, bool, list[int]], list[int] | None]",
        call_template="state, frame = {OP}(state, byte_val)",
        description=(
            "Advance byte-stream packet parser FSM (START=126, END=127, ESC=125, XOR=32) by one byte. "
            "Handles IDLE framing, ESC XOR unescaping, mid-frame START resync, and trailing XOR "
            "checksum validation, returning `(next_state, verified_payload_or_none)`."
        ),
        operand_convention=(
            "Unpack via `state, frame = {OP}(state, byte_val)` with state tuple `state` (start "
            "`('IDLE', False, [])`) and int `byte_val`."
        ),
        syntax_mask_regex=r"[A-Za-z_][A-Za-z0-9_]*\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*{OP}\([^,()]+,\s*[^,()]+\)",
        implementation=step_frame_parser,
        boundary_cases=(
            {"label": "idle_start_byte", "args": (("IDLE", False, []), 126), "args_repr": "('IDLE', False, []), 126", "expected": (("IN_FRAME", False, []), None), "expected_repr": "(('IN_FRAME', False, []), None)"},
            {"label": "escaped_xor_unescape", "args": (("IN_FRAME", True, [10]), 94), "args_repr": "('IN_FRAME', True, [10]), 94", "expected": (("IN_FRAME", False, [10, 126]), None), "expected_repr": "(('IN_FRAME', False, [10, 126]), None)"},
            {"label": "valid_checksum_end_frame", "args": (("IN_FRAME", False, [10, 6, 12]), 127), "args_repr": "('IN_FRAME', False, [10, 6, 12]), 127", "expected": (("IDLE", False, []), [10, 6]), "expected_repr": "(('IDLE', False, []), [10, 6])"},
            {"label": "bad_checksum_rejected", "args": (("IN_FRAME", False, [10, 6, 99]), 127), "args_repr": "('IN_FRAME', False, [10, 6, 99]), 127", "expected": (("IDLE", False, []), None), "expected_repr": "(('IDLE', False, []), None)"},
        ),
    ),
    "parse_semver_key": HelperSpec(
        name="parse_semver_key",
        family="version_semver",
        signature="parse_semver_key(ver_str) -> tuple[bool, tuple]",
        call_template="ok, key = {OP}(ver_str)",
        description=(
            "Strictly validate a SemVer 2.0 string `MAJOR.MINOR.PATCH[-PRE][+BUILD]` (rejecting leading "
            "zeros on numeric core or prerelease identifiers, validating build metadata while ignoring "
            "it in precedence) and return `(valid, comparable_key)` where `key = (maj, min, pat, pre_rank, pre_parts)`."
        ),
        operand_convention=(
            "Unpack via `ok, key = {OP}(ver_str)` with string `ver_str`; compare valid keys directly with `<` or `<=`."
        ),
        syntax_mask_regex=r"[A-Za-z_][A-Za-z0-9_]*\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*{OP}\([^,()]+\)",
        implementation=parse_semver_key,
        boundary_cases=(
            {"label": "leading_zero_invalid", "args": ("01.2.3",), "args_repr": "'01.2.3'", "expected": (False, ()), "expected_repr": "(False, ())"},
            {"label": "release_beats_prerelease", "args": ("1.0.0+build.7",), "args_repr": "'1.0.0+build.7'", "expected": (True, (1, 0, 0, 1, ())), "expected_repr": "(True, (1, 0, 0, 1, ()))"},
            {"label": "numeric_vs_alnum_prerelease", "args": ("1.0.0-alpha.2",), "args_repr": "'1.0.0-alpha.2'", "expected": (True, (1, 0, 0, 0, ((1, "alpha"), (0, 2)))), "expected_repr": "(True, (1, 0, 0, 0, ((1, 'alpha'), (0, 2))))"},
            {"label": "invalid_prerelease_leading_zero", "args": ("1.0.0-01",), "args_repr": "'1.0.0-01'", "expected": (False, ()), "expected_repr": "(False, ())"},
        ),
    ),
    "shift_business_day": HelperSpec(
        name="shift_business_day",
        family="calendar_business",
        signature="shift_business_day(ymd, delta_days, holidays) -> list[int]",
        call_template="day = {OP}(ymd, delta_days, holidays)",
        description=(
            "Shift proleptic Gregorian date `[year, month, day]` by signed `delta_days` business days, "
            "handling leap years (4/100/400) and skipping weekends and `holidays` (`[[y, m, d], ...]`). "
            "`delta_days == 0` snaps weekend/holiday forward to the next business day."
        ),
        operand_convention=(
            "Assign via `day = {OP}(ymd, delta_days, holidays)` with `[y, m, d]`, signed int `delta_days`, and `holidays`."
        ),
        syntax_mask_regex=r"[A-Za-z_][A-Za-z0-9_]*\s*=\s*{OP}\([^,()]+,\s*[^,()]+,\s*[^,()]+\)",
        implementation=shift_business_day,
        boundary_cases=(
            {"label": "leap_year_weekend_skip", "args": ([2024, 2, 28], 2, []), "args_repr": "[2024, 2, 28], 2, []", "expected": [2024, 3, 1], "expected_repr": "[2024, 3, 1]"},
            {"label": "century_non_leap_year", "args": ([2100, 2, 26], 2, []), "args_repr": "[2100, 2, 26], 2, []", "expected": [2100, 3, 2], "expected_repr": "[2100, 3, 2]"},
            {"label": "zero_delta_snaps_holiday", "args": ([2025, 1, 1], 0, [[2025, 1, 1]]), "args_repr": "[2025, 1, 1], 0, [[2025, 1, 1]]", "expected": [2025, 1, 2], "expected_repr": "[2025, 1, 2]"},
            {"label": "negative_shift_across_weekend", "args": ([2025, 1, 6], -2, [[2025, 1, 3]]), "args_repr": "[2025, 1, 6], -2, [[2025, 1, 3]]", "expected": [2025, 1, 1], "expected_repr": "[2025, 1, 1]"},
        ),
    ),
    "eval_safe_op": HelperSpec(
        name="eval_safe_op",
        family="expr_rpn_vm",
        signature="eval_safe_op(stack, op_tok, env) -> tuple[bool, list[int]]",
        call_template="ok, stack = {OP}(stack, op_tok, env)",
        description=(
            "Execute one guarded saturating RPN VM step on `stack` with token `op_tok` and variable "
            "dict `env`. Saturates pushed values to `[-10000, 10000]`, truncates DIV toward zero, "
            "enforces underflow/zero-div/missing-var/invalid-CLAMP guards, returning `(ok, next_stack)`."
        ),
        operand_convention=(
            "Unpack via `ok, stack = {OP}(stack, op_tok, env)` with list `stack`, str `op_tok`, and dict `env`."
        ),
        syntax_mask_regex=r"[A-Za-z_][A-Za-z0-9_]*\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*{OP}\([^,()]+,\s*[^,()]+,\s*[^,()]+\)",
        implementation=eval_safe_op,
        boundary_cases=(
            {"label": "truncating_negative_div", "args": ([-7, 2], "DIV", {}), "args_repr": "[-7, 2], 'DIV', {}", "expected": (True, [-3]), "expected_repr": "(True, [-3])"},
            {"label": "div_by_zero_fails", "args": ([5, 0], "DIV", {}), "args_repr": "[5, 0], 'DIV', {}", "expected": (False, []), "expected_repr": "(False, [])"},
            {"label": "saturating_mul_overflow", "args": ([500, 50], "MUL", {}), "args_repr": "[500, 50], 'MUL', {}", "expected": (True, [10000]), "expected_repr": "(True, [10000])"},
            {"label": "clamp_bounds_check", "args": ([12, 10, 5], "CLAMP", {}), "args_repr": "[12, 10, 5], 'CLAMP', {}", "expected": (False, []), "expected_repr": "(False, [])"},
        ),
    ),
}


def verify_all_helpers() -> dict[str, dict[str, Any]]:
    """Run every declared boundary case for every helper and return a receipt."""
    receipt: dict[str, dict[str, Any]] = {}
    for name, spec in HELPER_SPECS.items():
        case_results = []
        for case in spec.boundary_cases:
            args = []
            for item in case["args"]:
                if isinstance(item, list):
                    args.append([x[:] if isinstance(x, list) else x for x in item])
                elif isinstance(item, dict):
                    args.append(dict(item))
                elif isinstance(item, tuple):
                    args.append(tuple(list(x) if isinstance(x, list) else x for x in item))
                elif isinstance(item, set):
                    args.append(set(item))
                else:
                    args.append(item)
            actual = spec.implementation(*args)
            if actual != case["expected"]:
                raise AssertionError(
                    f"Helper {name} failed boundary case {case['label']}: "
                    f"expected {case['expected']!r}, got {actual!r}"
                )
            case_results.append(
                {
                    "label": case["label"],
                    "args_repr": case["args_repr"],
                    "expected": case["expected"],
                    "actual": actual,
                    "ok": True,
                }
            )
        if name == "skip_equal":
            try:
                skip_equal([1, 2], -1)
            except ValueError:
                pass
            else:
                raise AssertionError("skip_equal accepted negative index")
        receipt[name] = {
            "family": spec.family,
            "signature": spec.signature,
            "implementation_sha256": spec.implementation_sha256(),
            "cases_passed": len(case_results),
            "cases": case_results,
        }
    return receipt
