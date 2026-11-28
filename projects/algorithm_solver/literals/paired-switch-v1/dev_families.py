"""Development problem families for BITS paired-switch-v1.

Train development families (`DEV_PROBLEMS`, 12 problems across 3 families):
  1. run_codec         (helper: advance_rle_block(tokens, i, escape_tok))
  2. interval_algebra  (helper: apply_weighted_span(acc, start, end, delta))
  3. protocol_fsm      (helper: step_frame_parser(state, byte_val))

Disjoint validation development families (`DEV_VAL_PROBLEMS`, 12 problems across 3 families):
  4. version_semver    (helper: parse_semver_key(ver_str))
  5. calendar_business (helper: shift_business_day(ymd, delta_days, holidays))
  6. expr_rpn_vm       (helper: eval_safe_op(stack, op_tok, env))

Every family includes 4 verified problems spanning all three helper utility regimes:
  - 1 useful_once        (helper fixes a single call site cleanly)
  - 2 repeatedly_useful  (helper is reused across >=2 passes or call sites)
  - 1 irrelevant_decoy   (helper looks domain-adjacent, but the two pre-switch
                          failures stem from an unrelated algorithmic paradigm)

Every problem statement gives the complete mathematical/protocol specification so
`no_helper` can solve it fairly in standard Python without hidden oracle rules.
"""

from __future__ import annotations

from typing import Any

from helpers import HELPER_SPECS
from verifier import HELPER_TOKEN_SYMBOL, SingleBindRegistry, verify_candidate


_RLE_SPEC_TEXT = (
    "Escaped RLE stream rules with sentinel `escape_tok`: scan index `i` from 0; "
    "if `tokens[i] != escape_tok`, emit literal `tokens[i]` once and advance by 1; "
    "if `tokens[i] == escape_tok`: "
    "(a) if `i + 1 >= len(tokens)` (dangling trailing escape), emit literal `escape_tok` once and stop; "
    "(b) if `tokens[i + 1] == escape_tok` (doubled escape), emit literal `escape_tok` once and advance by 2; "
    "(c) else let `val = tokens[i + 1]`: if `i + 2 >= len(tokens)` (truncated run missing count), "
    "emit literal `val` once and stop; else let `cnt = tokens[i + 2]`: if `cnt <= 0`, skip all 3 tokens "
    "(emit nothing) and advance by 3; else emit `val` repeated `cnt` times and advance by 3."
)

_SPAN_SPEC_TEXT = (
    "Canonical half-open weighted step-function map `acc = [[s, e, w], ...]`: "
    "segments are half-open `[s, e)` with `s < e` and `w != 0`, sorted and disjoint (`e_k <= s_{k+1}`), "
    "with adjacent equal-weight segments (`e_k == s_{k+1}` and `w_k == w_{k+1}`) coalesced into one. "
    "Applying update `[start, end, delta]` (ignoring `start >= end` or `delta == 0`) adds `delta` over "
    "`[start, end)` by splitting overlapping segments at `start` and `end`, summing weights on overlaps, "
    "creating new segments on gaps, dropping any segment whose new weight is 0, and coalescing adjacent "
    "segments with equal weights."
)

_FSM_SPEC_TEXT = (
    "Framed byte-stream protocol (START=126, END=127, ESC=125, XOR_MASK=32): "
    "start in IDLE ignoring bytes until START (126) enters IN_FRAME with empty buffer; "
    "while IN_FRAME: if previous byte was ESC (125), append `byte ^ 32` to buffer; "
    "else if `byte == 125` (ESC), mark next byte escaped; "
    "else if `byte == 126` (START), resync by discarding partial buffer and staying IN_FRAME; "
    "else if `byte == 127` (END), return to IDLE and emit payload `buf[:-1]` ONLY if `len(buf) >= 2` "
    "and XOR of all bytes in `buf[:-1]` equals checksum `buf[-1]` (otherwise discard); "
    "else append `byte` to buffer."
)

_SEMVER_SPEC_TEXT = (
    "Strict SemVer 2.0 rules (`MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`): "
    "core has exactly 3 non-negative ASCII integer parts with no leading zeros (except `'0'`); "
    "optional `+BUILD` must be dot-separated non-empty `[0-9A-Za-z-]+` parts and is IGNORED in precedence; "
    "optional `-PRERELEASE` must be dot-separated non-empty `[0-9A-Za-z-]+` parts where numeric-only "
    "parts have no leading zeros, compare numerically, and sort BEFORE alphanumeric parts (lexicographic ASCII); "
    "a release version (no `-PRERELEASE`) has HIGHER precedence than any prerelease with the same core; "
    "if all earlier prerelease parts match, a shorter prerelease tuple has lower precedence."
)

_CAL_SPEC_TEXT = (
    "Proleptic Gregorian business-day rules: leap year iff `y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)`; "
    "business days exclude Saturdays, Sundays, and dates in `holidays` (`[[y, m, d], ...]`). "
    "Shifting `[y, m, d]` by `delta_days`: if `delta_days == 0`, snap forward to the next business day if "
    "the date is a weekend or holiday (else keep it); if `delta_days > 0`, advance `delta_days` business days; "
    "if `delta_days < 0`, step `|delta_days|` business days backward."
)

_VM_SPEC_TEXT = (
    "Guarded saturating RPN VM rules (all pushed numeric values clamped to `[-10000, 10000]`): "
    "integer literal token pushes clamped int; `'$name'` pushes clamped `env[name]` (fail if missing); "
    "`DUP` duplicates top (needs >=1); `DROP` pops top (needs >=1); `SWAP` swaps top two (needs >=2); "
    "`ADD`/`SUB`/`MUL` pop `b` then `a` and push clamped `a+b`/`a-b`/`a*b` (needs >=2); "
    "`DIV` pops `b` then `a`, fails if `b == 0`, else pushes clamped `int(a / b)` (truncating toward zero, NOT `//`); "
    "`CLAMP` pops `hi`, `lo`, `x`, fails if `lo > hi`, else pushes clamped `min(max(x, lo), hi)` (needs >=3); "
    "unknown tokens or stack underflow fail immediately."
)


DEV_PROBLEMS: list[dict[str, Any]] = [
    # ------------------------------------------------------------------
    # Family 1: run_codec (helper: advance_rle_block)
    # ------------------------------------------------------------------
    {
        "problem_id": "rle_01_decode_sum_and_len",
        "family": "run_codec",
        "utility_regime": "useful_once",
        "helper_name": "advance_rle_block",
        "entry_point": "rle_decode_stats",
        "statement": (
            "Write `rle_decode_stats(tokens, escape_tok)` returning `[decoded_length, decoded_sum]` "
            "for an escaped RLE integer stream. " + _RLE_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def rle_decode_stats(tokens, escape_tok):\n"
                "    n = len(tokens)\n"
                "    i = 0\n"
                "    length = 0\n"
                "    total = 0\n"
                "    while i < n:\n"
                "        if tokens[i] == escape_tok:\n"
                "            val = tokens[i + 1]\n"
                "            cnt = tokens[i + 2]\n"
                "            length += cnt\n"
                "            total += val * cnt\n"
                "            i += 3\n"
                "        else:\n"
                "            length += 1\n"
                "            total += tokens[i]\n"
                "            i += 1\n"
                "    return [length, total]\n"
            ),
            (
                "def rle_decode_stats(tokens, escape_tok):\n"
                "    n = len(tokens)\n"
                "    i = 0\n"
                "    length = 0\n"
                "    total = 0\n"
                "    while i < n:\n"
                "        if tokens[i] == escape_tok:\n"
                "            if i + 2 < n:\n"
                "                val = tokens[i + 1]\n"
                "                cnt = tokens[i + 2]\n"
                "                length += max(0, cnt)\n"
                "                total += val * max(0, cnt)\n"
                "                i += 3\n"
                "            else:\n"
                "                break\n"
                "        else:\n"
                "            length += 1\n"
                "            total += tokens[i]\n"
                "            i += 1\n"
                "    return [length, total]\n"
            ),
        ],
        "reference_with_helper": (
            "def rle_decode_stats(tokens, escape_tok):\n"
            "    i = 0\n"
            "    n = len(tokens)\n"
            "    length = 0\n"
            "    total = 0\n"
            "    while i < n:\n"
            "        i, val, cnt = {OP}(tokens, i, escape_tok)\n"
            "        if cnt > 0:\n"
            "            length += cnt\n"
            "            total += val * cnt\n"
            "    return [length, total]\n"
        ),
        "public_cases": [
            {"label": "doubled_escape_and_dangling_escape", "args": [[-1, -1, 5, -1], -1], "expected": [3, 3]},
            {"label": "truncated_run_and_zero_count_escape", "args": [[-1, 9, 0, -1, 7], -1], "expected": [1, 7]},
            {"label": "negative_count_and_valid_run", "args": [[-1, 4, -2, -1, 3, 5, 2], -1], "expected": [6, 17]},
        ],
        "hidden_cases": [
            {"label": "empty_stream", "args": [[], -1], "expected": [0, 0]},
            {"label": "escape_as_run_count_and_doubled", "args": [[0, 0, 0, 8, 3, 0], 0], "expected": [5, 24]},
            {"label": "chained_zero_and_valid_runs", "args": [[99, 5, 0, 99, 99, 99, 2, 4, 99], 99], "expected": [6, 206]},
        ],
    },
    {
        "problem_id": "rle_02_stream_diff_metrics",
        "family": "run_codec",
        "utility_regime": "repeatedly_useful",
        "canonical_section1_fixture": True,
        "helper_name": "advance_rle_block",
        "entry_point": "compare_rle_streams",
        "statement": (
            "Write `compare_rle_streams(stream_a, stream_b, escape_tok)` decoding both escaped RLE "
            "streams and returning `[len_a, len_b, first_mismatch_index]` where `first_mismatch_index` "
            "is the smallest index where the expanded streams differ (or the shorter length if one is "
            "a strict prefix of the other, or `-1` if expanded streams are identical). " + _RLE_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def compare_rle_streams(stream_a, stream_b, escape_tok):\n"
                "    def dec(toks):\n"
                "        out = []\n"
                "        i = 0\n"
                "        while i < len(toks):\n"
                "            if toks[i] == escape_tok:\n"
                "                out.extend([toks[i + 1]] * toks[i + 2])\n"
                "                i += 3\n"
                "            else:\n"
                "                out.append(toks[i])\n"
                "                i += 1\n"
                "        return out\n"
                "    a, b = dec(stream_a), dec(stream_b)\n"
                "    m = min(len(a), len(b))\n"
                "    for k in range(m):\n"
                "        if a[k] != b[k]:\n"
                "            return [len(a), len(b), k]\n"
                "    return [len(a), len(b), -1 if len(a) == len(b) else m]\n"
            ),
            (
                "def compare_rle_streams(stream_a, stream_b, escape_tok):\n"
                "    def dec(toks):\n"
                "        out = []\n"
                "        i = 0\n"
                "        while i < len(toks):\n"
                "            if toks[i] == escape_tok and i + 2 < len(toks):\n"
                "                if toks[i + 2] > 0:\n"
                "                    out.extend([toks[i + 1]] * toks[i + 2])\n"
                "                i += 3\n"
                "            else:\n"
                "                out.append(toks[i])\n"
                "                i += 1\n"
                "        return out\n"
                "    a, b = dec(stream_a), dec(stream_b)\n"
                "    m = min(len(a), len(b))\n"
                "    for k in range(m):\n"
                "        if a[k] != b[k]:\n"
                "            return [len(a), len(b), k]\n"
                "    return [len(a), len(b), -1 if len(a) == len(b) else m]\n"
            ),
        ],
        "reference_with_helper": (
            "def compare_rle_streams(stream_a, stream_b, escape_tok):\n"
            "    a = []\n"
            "    ia = 0\n"
            "    while ia < len(stream_a):\n"
            "        ia, val, cnt = {OP}(stream_a, ia, escape_tok)\n"
            "        if cnt > 0:\n"
            "            a.extend([val] * cnt)\n"
            "    b = []\n"
            "    ib = 0\n"
            "    while ib < len(stream_b):\n"
            "        ib, val, cnt = {OP}(stream_b, ib, escape_tok)\n"
            "        if cnt > 0:\n"
            "            b.extend([val] * cnt)\n"
            "    m = min(len(a), len(b))\n"
            "    for k in range(m):\n"
            "        if a[k] != b[k]:\n"
            "            return [len(a), len(b), k]\n"
            "    return [len(a), len(b), -1 if len(a) == len(b) else m]\n"
        ),
        "public_cases": [
            {"label": "doubled_escape_equivalence", "args": [[-1, -1, -1, 4, 2, -1], [-1, -1, 4, 4, -1], -1], "expected": [4, 4, -1]},
            {"label": "truncated_run_and_zero_skip_mismatch", "args": [[-1, 5, 0, -1, 8], [8, 9], -1], "expected": [1, 2, 1]},
        ],
        "hidden_cases": [
            {"label": "mid_stream_diff", "args": [[-1, 3, 3, 7], [3, 3, 3, 8], -1], "expected": [4, 4, 3]},
            {"label": "both_empty_after_zero_runs", "args": [[0, 5, 0], [0, 9, -3], 0], "expected": [0, 0, -1]},
        ],
    },
    {
        "problem_id": "rle_03_header_body_checksum",
        "family": "run_codec",
        "utility_regime": "repeatedly_useful",
        "helper_name": "advance_rle_block",
        "entry_point": "rle_header_body_checksum",
        "statement": (
            "Write `rle_header_body_checksum(header_tokens, body_tokens, escape_tok, mod)` that "
            "decodes `header_tokens` to compute shift `k = sum(header) % mod`, then decodes "
            "`body_tokens` and returns `sum((idx + k) * val for idx, val in enumerate(body)) % mod` "
            "(assuming `mod > 0`). " + _RLE_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def rle_header_body_checksum(header_tokens, body_tokens, escape_tok, mod):\n"
                "    k = sum(header_tokens) % mod\n"
                "    total = 0\n"
                "    for idx, v in enumerate(body_tokens):\n"
                "        total = (total + (idx + k) * v) % mod\n"
                "    return total\n"
            ),
            (
                "def rle_header_body_checksum(header_tokens, body_tokens, escape_tok, mod):\n"
                "    def dec(toks):\n"
                "        out, i = [], 0\n"
                "        while i < len(toks):\n"
                "            if toks[i] == escape_tok and i + 2 < len(toks):\n"
                "                out.extend([toks[i + 1]] * toks[i + 2])\n"
                "                i += 3\n"
                "            else:\n"
                "                out.append(toks[i])\n"
                "                i += 1\n"
                "        return out\n"
                "    k = sum(dec(header_tokens)) % mod\n"
                "    body = dec(body_tokens)\n"
                "    return sum((idx + k) * v for idx, v in enumerate(body)) % mod\n"
            ),
        ],
        "reference_with_helper": (
            "def rle_header_body_checksum(header_tokens, body_tokens, escape_tok, mod):\n"
            "    ih = 0\n"
            "    h_sum = 0\n"
            "    while ih < len(header_tokens):\n"
            "        ih, val, cnt = {OP}(header_tokens, ih, escape_tok)\n"
            "        if cnt > 0:\n"
            "            h_sum += val * cnt\n"
            "    k = h_sum % mod\n"
            "    ib = 0\n"
            "    pos = 0\n"
            "    acc = 0\n"
            "    while ib < len(body_tokens):\n"
            "        ib, val, cnt = {OP}(body_tokens, ib, escape_tok)\n"
            "        if cnt > 0:\n"
            "            idx_sum = cnt * (pos + k) + (cnt * (cnt - 1)) // 2\n"
            "            acc = (acc + idx_sum * val) % mod\n"
            "            pos += cnt\n"
            "    return acc % mod\n"
        ),
        "public_cases": [
            {"label": "doubled_escape_header_and_truncated_body", "args": [[9, 9, 2], [9, 4, 0, 9, 5], 9, 100], "expected": [11 * 5 % 100][0]},
            {"label": "dangling_escape_and_negative_count", "args": [[7, 2, 3, 7], [7, 8, -1, 7, 3, 2, 7], 7, 97], "expected": ((13 * 3) + (14 * 3) + (15 * 7)) % 97},
        ],
        "hidden_cases": [
            {"label": "empty_body", "args": [[-1, 5, 2], [-1, 9, 0], -1, 50], "expected": 0},
            {"label": "large_run_count_mod", "args": [[-1, 1, 3], [-1, 2, 10, -1, -1], -1, 1000], "expected": (sum((i + 3) * 2 for i in range(10)) + (13 * -1)) % 1000},
        ],
    },
    {
        "problem_id": "rle_04_max_subarray_decoy",
        "family": "run_codec",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "advance_rle_block",
        "entry_point": "max_contiguous_sum",
        "statement": (
            "Write `max_contiguous_sum(nums)` returning the maximum sum of any non-empty contiguous "
            "subarray of integer list `nums` (which contains plain unencoded signed integers, possibly all negative)."
        ),
        "failed_attempts": [
            (
                "def max_contiguous_sum(nums):\n"
                "    best = 0\n"
                "    cur = 0\n"
                "    for x in nums:\n"
                "        cur = max(0, cur + x)\n"
                "        best = max(best, cur)\n"
                "    return best\n"
            ),
            (
                "def max_contiguous_sum(nums):\n"
                "    return sum(x for x in nums if x > 0) if any(x > 0 for x in nums) else max(nums)\n"
            ),
        ],
        "reference_with_helper": (
            "def max_contiguous_sum(nums):\n"
            "    best = cur = nums[0]\n"
            "    for x in nums[1:]:\n"
            "        cur = x if cur < 0 else cur + x\n"
            "        if cur > best:\n"
            "            best = cur\n"
            "    return best\n"
        ),
        "public_cases": [
            {"label": "all_negative_subarray_sum", "args": [[-8, -3, -6, -2, -9]], "expected": -2},
            {"label": "non_contiguous_positive_sum_bug", "args": [[4, -10, 5, -1, 3]], "expected": 7},
        ],
        "hidden_cases": [
            {"label": "singleton_negative", "args": [[-5]], "expected": -5},
            {"label": "mixed_kadane", "args": [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], "expected": 6},
        ],
    },
    # ------------------------------------------------------------------
    # Family 2: interval_algebra (helper: apply_weighted_span)
    # ------------------------------------------------------------------
    {
        "problem_id": "span_01_net_positive_coverage",
        "family": "interval_algebra",
        "utility_regime": "useful_once",
        "helper_name": "apply_weighted_span",
        "entry_point": "positive_span_metrics",
        "statement": (
            "Write `positive_span_metrics(updates)` taking a list of `[start, end, delta]` updates "
            "applied sequentially to an initially empty canonical weighted step-function map, and "
            "returning `[positive_length, max_weight, canonical_segment_count]` where `positive_length` "
            "is the total length of segments with `w > 0`, `max_weight` is the highest positive weight "
            "(or `0` if none), and `canonical_segment_count` is `len(acc)` after zero-removal and coalescing. "
            + _SPAN_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def positive_span_metrics(updates):\n"
                "    acc = []\n"
                "    for s, e, d in updates:\n"
                "        if s < e and d != 0:\n"
                "            acc.append([s, e, d])\n"
                "    pos_len = sum(e - s for s, e, w in acc if w > 0)\n"
                "    mx = max((w for _, _, w in acc if w > 0), default=0)\n"
                "    return [pos_len, mx, len(acc)]\n"
            ),
            (
                "def positive_span_metrics(updates):\n"
                "    pts = sorted({x for s, e, d in updates if s < e and d != 0 for x in (s, e)})\n"
                "    segs = []\n"
                "    for i in range(len(pts) - 1):\n"
                "        a, b = pts[i], pts[i + 1]\n"
                "        w = sum(d for s, e, d in updates if s <= a and b <= e)\n"
                "        if w != 0:\n"
                "            segs.append([a, b, w])\n"
                "    pos_len = sum(e - s for s, e, w in segs if w > 0)\n"
                "    mx = max((w for _, _, w in segs if w > 0), default=0)\n"
                "    return [pos_len, mx, len(segs)]\n"
            ),
        ],
        "reference_with_helper": (
            "def positive_span_metrics(updates):\n"
            "    acc = []\n"
            "    for start, end, delta in updates:\n"
            "        acc = {OP}(acc, start, end, delta)\n"
            "    pos_len = sum(e - s for s, e, w in acc if w > 0)\n"
            "    mx = max((w for _, _, w in acc if w > 0), default=0)\n"
            "    return [pos_len, mx, len(acc)]\n"
        ),
        "public_cases": [
            {"label": "overlap_zero_cancellation_and_coalesce", "args": [[[1, 6, 3], [3, 8, -3], [6, 8, 6]]], "expected": [4, 3, 2]},
            {"label": "adjacent_equal_weight_coalesce_count", "args": [[[0, 4, 2], [4, 9, 2], [2, 6, 0]]], "expected": [9, 2, 1]},
        ],
        "hidden_cases": [
            {"label": "all_cancelled_empty", "args": [[[2, 7, 5], [2, 7, -5]]], "expected": [0, 0, 0]},
            {"label": "negative_middle_island", "args": [[[0, 10, 2], [3, 7, -5]]], "expected": [6, 2, 3]},
        ],
    },
    {
        "problem_id": "span_02_two_channel_peak_overlap",
        "family": "interval_algebra",
        "utility_regime": "repeatedly_useful",
        "helper_name": "apply_weighted_span",
        "entry_point": "two_channel_span_summary",
        "statement": (
            "Write `two_channel_span_summary(base_updates, boost_updates)` that first builds canonical "
            "weighted step-function map `A` from `base_updates`, then builds combined canonical map `B` "
            "by applying `boost_updates` on top of `A`, and returns `[len(A), len(B), signed_area_B]` "
            "where `signed_area_B = sum((e - s) * w for s, e, w in B)`. " + _SPAN_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def two_channel_span_summary(base_updates, boost_updates):\n"
                "    a = [u for u in base_updates if u[0] < u[1] and u[2] != 0]\n"
                "    b = a + [u for u in boost_updates if u[0] < u[1] and u[2] != 0]\n"
                "    area = sum((e - s) * w for s, e, w in b)\n"
                "    return [len(a), len(b), area]\n"
            ),
            (
                "def two_channel_span_summary(base_updates, boost_updates):\n"
                "    def build(us):\n"
                "        pts = sorted({x for s, e, d in us if s < e and d != 0 for x in (s, e)})\n"
                "        out = []\n"
                "        for i in range(len(pts) - 1):\n"
                "            a, b = pts[i], pts[i + 1]\n"
                "            w = sum(d for s, e, d in us if s <= a and b <= e)\n"
                "            out.append([a, b, w])\n"
                "        return out\n"
                "    ma = build(base_updates)\n"
                "    mb = build(base_updates + boost_updates)\n"
                "    return [len(ma), len(mb), sum((e - s) * w for s, e, w in mb)]\n"
            ),
        ],
        "reference_with_helper": (
            "def two_channel_span_summary(base_updates, boost_updates):\n"
            "    acc = []\n"
            "    for start, end, delta in base_updates:\n"
            "        acc = {OP}(acc, start, end, delta)\n"
            "    len_a = len(acc)\n"
            "    for start, end, delta in boost_updates:\n"
            "        acc = {OP}(acc, start, end, delta)\n"
            "    area_b = sum((e - s) * w for s, e, w in acc)\n"
            "    return [len_a, len(acc), area_b]\n"
        ),
        "public_cases": [
            {"label": "coalesce_across_gap_and_zero_drop", "args": [[[1, 4, 2], [6, 9, 2]], [[4, 6, 2], [1, 2, -2]]], "expected": [2, 1, 14]},
            {"label": "boost_cancels_interior_split", "args": [[[0, 10, 5]], [[2, 5, -5], [5, 8, -5]]], "expected": [1, 2, 20]},
        ],
        "hidden_cases": [
            {"label": "empty_boost", "args": [[[1, 3, 4], [3, 5, 4]], []], "expected": [1, 1, 16]},
            {"label": "degenerate_ignored", "args": [[[5, 5, 10], [1, 4, 3]], [[1, 4, -3], [2, 1, 9]]], "expected": [1, 0, 0]},
        ],
    },
    {
        "problem_id": "span_03_apply_and_revert_audit",
        "family": "interval_algebra",
        "utility_regime": "repeatedly_useful",
        "helper_name": "apply_weighted_span",
        "entry_point": "audit_span_add_and_revert",
        "statement": (
            "Write `audit_span_add_and_revert(adds, reverts)` where `adds` and `reverts` are lists of "
            "`[start, end, weight]`. First apply every `[s, e, w]` in `adds` with delta `+w` to an empty "
            "canonical weighted step-function map, recording `peak_after_adds = max((w for _, _, w in acc), default=0)`. "
            "Then apply every `[s, e, w]` in `reverts` with negated delta `-w`, and return "
            "`[peak_after_adds, len(acc), sum((e - s) * w for s, e, w in acc)]`. " + _SPAN_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def audit_span_add_and_revert(adds, reverts):\n"
                "    peak = max((w for s, e, w in adds if s < e), default=0)\n"
                "    area = sum((e - s) * w for s, e, w in adds if s < e) - sum((e - s) * w for s, e, w in reverts if s < e)\n"
                "    return [peak, len(adds), area]\n"
            ),
            (
                "def audit_span_add_and_revert(adds, reverts):\n"
                "    pts = sorted({x for s, e, _ in adds + reverts if s < e for x in (s, e)})\n"
                "    peak = 0\n"
                "    segs = []\n"
                "    for i in range(len(pts) - 1):\n"
                "        a, b = pts[i], pts[i + 1]\n"
                "        wa = sum(w for s, e, w in adds if s <= a and b <= e)\n"
                "        peak = max(peak, wa)\n"
                "        wr = wa - sum(w for s, e, w in reverts if s <= a and b <= e)\n"
                "        if wr != 0:\n"
                "            segs.append([a, b, wr])\n"
                "    return [peak, len(segs), sum((e - s) * w for s, e, w in segs)]\n"
            ),
        ],
        "reference_with_helper": (
            "def audit_span_add_and_revert(adds, reverts):\n"
            "    acc = []\n"
            "    for start, end, w in adds:\n"
            "        acc = {OP}(acc, start, end, w)\n"
            "    peak = max((w for _, _, w in acc), default=0)\n"
            "    for start, end, w in reverts:\n"
            "        acc = {OP}(acc, start, end, -w)\n"
            "    return [peak, len(acc), sum((e - s) * w for s, e, w in acc)]\n"
        ),
        "public_cases": [
            {"label": "overlap_peak_and_partial_revert_coalesce", "args": [[[1, 6, 3], [3, 9, 2]], [[3, 6, 2], [6, 9, -1]]], "expected": [5, 1, 24]},
            {"label": "full_revert_leaves_empty_map", "args": [[[0, 4, 7], [2, 6, 3]], [[0, 4, 7], [2, 6, 3]]], "expected": [10, 0, 0]},
        ],
        "hidden_cases": [
            {"label": "empty_inputs", "args": [[], []], "expected": [0, 0, 0]},
            {"label": "revert_creates_negative_gap", "args": [[[0, 8, 2]], [[2, 5, 4]]], "expected": [2, 3, 4]},
        ],
    },
    {
        "problem_id": "span_04_weighted_job_dp_decoy",
        "family": "interval_algebra",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "apply_weighted_span",
        "entry_point": "max_job_profit",
        "statement": (
            "Write `max_job_profit(jobs)` taking jobs `[start, end, profit]` (`start < end`, `profit > 0`) "
            "and returning the maximum total profit of a subset of non-overlapping jobs (a job ending at "
            "`t` does not overlap one starting at `t`)."
        ),
        "failed_attempts": [
            (
                "def max_job_profit(jobs):\n"
                "    chosen = []\n"
                "    total = 0\n"
                "    for s, e, p in sorted(jobs, key=lambda x: -x[2]):\n"
                "        if all(e <= cs or s >= ce for cs, ce, _ in chosen):\n"
                "            chosen.append((s, e, p))\n"
                "            total += p\n"
                "    return total\n"
            ),
            (
                "def max_job_profit(jobs):\n"
                "    cur_end = -10**9\n"
                "    total = 0\n"
                "    for s, e, p in sorted(jobs, key=lambda x: x[1]):\n"
                "        if s >= cur_end:\n"
                "            total += p\n"
                "            cur_end = e\n"
                "    return total\n"
            ),
        ],
        "reference_with_helper": (
            "def max_job_profit(jobs):\n"
            "    if not jobs:\n"
            "        return 0\n"
            "    js = sorted(jobs, key=lambda x: x[1])\n"
            "    n = len(js)\n"
            "    dp = [0] * (n + 1)\n"
            "    ends = [j[1] for j in js]\n"
            "    for i in range(1, n + 1):\n"
            "        s, e, p = js[i - 1]\n"
            "        lo, hi = 0, i - 1\n"
            "        while lo < hi:\n"
            "            mid = (lo + hi) // 2\n"
            "            if ends[mid] <= s:\n"
            "                lo = mid + 1\n"
            "            else:\n"
            "                hi = mid\n"
            "        dp[i] = max(dp[i - 1], dp[lo] + p)\n"
            "    return dp[n]\n"
        ),
        "public_cases": [
            {"label": "greedy_profit_and_end_dp_trap", "args": [[[1, 3, 5], [2, 5, 6], [4, 6, 5], [1, 6, 9]]], "expected": 10},
            {"label": "earliest_end_greedy_fails_dp", "args": [[[1, 2, 1], [1, 4, 10], [3, 5, 1]]], "expected": 10},
        ],
        "hidden_cases": [
            {"label": "empty_jobs", "args": [[]], "expected": 0},
            {"label": "chain_vs_long", "args": [[[0, 2, 4], [2, 4, 4], [4, 6, 4], [0, 6, 11]]], "expected": 12},
        ],
    },
    # ------------------------------------------------------------------
    # Family 3: protocol_fsm (helper: step_frame_parser)
    # ------------------------------------------------------------------
    {
        "problem_id": "fsm_01_extract_valid_payloads",
        "family": "protocol_fsm",
        "utility_regime": "useful_once",
        "helper_name": "step_frame_parser",
        "entry_point": "parse_valid_frame_stats",
        "statement": (
            "Write `parse_valid_frame_stats(stream)` taking a list of byte integers (`0..255`) and "
            "returning `[valid_frame_count, total_payload_bytes, sum_payload_bytes]` across all valid "
            "frames decoded from `stream`. " + _FSM_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def parse_valid_frame_stats(stream):\n"
                "    in_f = False\n"
                "    buf = []\n"
                "    cnt = total = s = 0\n"
                "    for b in stream:\n"
                "        if b == 126:\n"
                "            in_f = True\n"
                "            buf = []\n"
                "        elif b == 127 and in_f:\n"
                "            if len(buf) >= 2:\n"
                "                cnt += 1\n"
                "                total += len(buf) - 1\n"
                "                s += sum(buf[:-1])\n"
                "            in_f = False\n"
                "        elif in_f:\n"
                "            buf.append(b)\n"
                "    return [cnt, total, s]\n"
            ),
            (
                "def parse_valid_frame_stats(stream):\n"
                "    in_f = False\n"
                "    esc = False\n"
                "    buf = []\n"
                "    cnt = total = s = 0\n"
                "    for b in stream:\n"
                "        if not in_f:\n"
                "            if b == 126:\n"
                "                in_f = True\n"
                "                buf = []\n"
                "        elif esc:\n"
                "            buf.append(b)\n"
                "            esc = False\n"
                "        elif b == 125:\n"
                "            esc = True\n"
                "        elif b == 127:\n"
                "            chk = 0\n"
                "            for x in buf[:-1]:\n"
                "                chk ^= x\n"
                "            if len(buf) >= 2 and chk == buf[-1]:\n"
                "                cnt += 1\n"
                "                total += len(buf) - 1\n"
                "                s += sum(buf[:-1])\n"
                "            in_f = False\n"
                "        else:\n"
                "            buf.append(b)\n"
                "    return [cnt, total, s]\n"
            ),
        ],
        "reference_with_helper": (
            "def parse_valid_frame_stats(stream):\n"
            "    state = ('IDLE', False, [])\n"
            "    cnt = 0\n"
            "    total = 0\n"
            "    s = 0\n"
            "    for byte_val in stream:\n"
            "        state, frame = {OP}(state, byte_val)\n"
            "        if frame is not None:\n"
            "            cnt += 1\n"
            "            total += len(frame)\n"
            "            s += sum(frame)\n"
            "    return [cnt, total, s]\n"
        ),
        "public_cases": [
            # Escaped START (126^32=94) inside payload: payload=[126, 10], chk=126^10=116; plus bad-checksum frame
            {"label": "escaped_xor_and_bad_checksum", "args": [[1, 2, 126, 125, 94, 10, 116, 127, 126, 5, 9, 127]], "expected": [1, 2, 136]},
            # Mid-frame START resync discards [55, 66], then valid payload [125, 4] (125 escaped as 125,93; chk=125^4=121)
            {"label": "mid_frame_resync_and_escaped_esc", "args": [[126, 55, 66, 126, 125, 93, 4, 121, 127]], "expected": [1, 2, 129]},
        ],
        "hidden_cases": [
            # Escaped END (127^32=95) as checksum! payload=[127] -> chk=127 -> encoded as [126, 125, 95, 125, 95, 127]
            {"label": "escaped_end_and_empty_frame", "args": [[126, 127, 126, 9, 127, 126, 125, 95, 125, 95, 127]], "expected": [1, 1, 127]},
            {"label": "noise_only", "args": [[10, 20, 127, 125, 30]], "expected": [0, 0, 0]},
        ],
    },
    {
        "problem_id": "fsm_02_dual_link_sync_merge",
        "family": "protocol_fsm",
        "utility_regime": "repeatedly_useful",
        "helper_name": "step_frame_parser",
        "entry_point": "dual_link_frame_audit",
        "statement": (
            "Write `dual_link_frame_audit(stream_a, stream_b)` parsing valid frames independently from "
            "`stream_a` and `stream_b` under the byte-stream framing protocol, returning "
            "`[count_a, count_b, sum_first_bytes]` where `sum_first_bytes` sums `frame[0]` across all "
            "valid frames from both links. " + _FSM_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def dual_link_frame_audit(stream_a, stream_b):\n"
                "    def parse(st):\n"
                "        out, cur, on = [], [], False\n"
                "        for b in st:\n"
                "            if b == 126:\n"
                "                on, cur = True, []\n"
                "            elif b == 127 and on:\n"
                "                if len(cur) >= 2:\n"
                "                    out.append(cur[:-1])\n"
                "                on = False\n"
                "            elif on:\n"
                "                cur.append(b)\n"
                "        return out\n"
                "    fa, fb = parse(stream_a), parse(stream_b)\n"
                "    return [len(fa), len(fb), sum(f[0] for f in fa + fb)]\n"
            ),
            (
                "def dual_link_frame_audit(stream_a, stream_b):\n"
                "    def parse(st):\n"
                "        out, cur, on, esc = [], [], False, False\n"
                "        for b in st:\n"
                "            if not on:\n"
                "                if b == 126:\n"
                "                    on, cur = True, []\n"
                "            elif esc:\n"
                "                cur.append(b ^ 32)\n"
                "                esc = False\n"
                "            elif b == 125:\n"
                "                esc = True\n"
                "            elif b == 127:\n"
                "                chk = 0\n"
                "                for x in cur[:-1]:\n"
                "                    chk ^= x\n"
                "                if len(cur) >= 2 and chk == cur[-1]:\n"
                "                    out.append(cur[:-1])\n"
                "                on = False\n"
                "            else:\n"
                "                cur.append(b)\n"
                "        return out\n"
                "    fa, fb = parse(stream_a), parse(stream_b)\n"
                "    return [len(fa), len(fb), sum(f[0] for f in fa + fb)]\n"
            ),
        ],
        "reference_with_helper": (
            "def dual_link_frame_audit(stream_a, stream_b):\n"
            "    sa = ('IDLE', False, [])\n"
            "    fa = []\n"
            "    for byte_val in stream_a:\n"
            "        sa, frame = {OP}(sa, byte_val)\n"
            "        if frame is not None:\n"
            "            fa.append(frame)\n"
            "    sb = ('IDLE', False, [])\n"
            "    fb = []\n"
            "    for byte_val in stream_b:\n"
            "        sb, frame = {OP}(sb, byte_val)\n"
            "        if frame is not None:\n"
            "            fb.append(frame)\n"
            "    return [len(fa), len(fb), sum(f[0] for f in fa + fb)]\n"
        ),
        "public_cases": [
            # stream_a has mid-frame START resync before [126, 2, 124]; stream_b has escaped END [127, 1, 126] (126^32=94)
            {"label": "resync_link_a_and_escaped_link_b", "args": [[126, 9, 126, 20, 4, 16, 127], [126, 125, 95, 1, 125, 94, 127]], "expected": [1, 1, 147]},
            {"label": "bad_checksum_filtered_on_both", "args": [[126, 5, 5, 127, 126, 5, 6, 127], [126, 127, 126, 10, 10, 127]], "expected": [1, 1, 15]},
        ],
        "hidden_cases": [
            {"label": "one_empty_link", "args": [[], [126, 3, 4, 7, 127]], "expected": [0, 1, 3]},
            {"label": "multi_frame_both", "args": [[126, 1, 1, 127, 126, 2, 2, 127], [126, 8, 8, 127]], "expected": [2, 1, 11]},
        ],
    },
    {
        "problem_id": "fsm_03_chunked_stream_resume",
        "family": "protocol_fsm",
        "utility_regime": "repeatedly_useful",
        "helper_name": "step_frame_parser",
        "entry_point": "parse_chunked_with_trailer",
        "statement": (
            "Write `parse_chunked_with_trailer(chunks, trailer_bytes)` where `chunks` is a list of "
            "byte lists (frames and ESC sequences may split across chunk boundaries and into `trailer_bytes`). "
            "Feed all bytes of `chunks` in order preserving FSM state, record `frames_in_chunks`, then "
            "continue feeding `trailer_bytes` into the SAME FSM state, returning "
            "`[frames_in_chunks, total_frames, last_frame_total]` (`last_frame_total = 0` if no valid frames). "
            + _FSM_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def parse_chunked_with_trailer(chunks, trailer_bytes):\n"
                "    # Bug: resets state between chunks and forgets ESC across boundaries\n"
                "    frames = []\n"
                "    for ch in chunks:\n"
                "        if len(ch) >= 4 and ch[0] == 126 and ch[-1] == 127:\n"
                "            frames.append(ch[1:-2])\n"
                "    n1 = len(frames)\n"
                "    if len(trailer_bytes) >= 4 and trailer_bytes[0] == 126 and trailer_bytes[-1] == 127:\n"
                "        frames.append(trailer_bytes[1:-2])\n"
                "    return [n1, len(frames), sum(frames[-1]) if frames else 0]\n"
            ),
            (
                "def parse_chunked_with_trailer(chunks, trailer_bytes):\n"
                "    # Bug: mishandles ESC XOR and mid-frame resync\n"
                "    on = False\n"
                "    buf = []\n"
                "    frames = []\n"
                "    for ch in chunks:\n"
                "        for b in ch:\n"
                "            if b == 126:\n"
                "                on, buf = True, []\n"
                "            elif b == 127 and on:\n"
                "                if len(buf) >= 2:\n"
                "                    frames.append(buf[:-1])\n"
                "                on = False\n"
                "            elif on:\n"
                "                buf.append(b)\n"
                "    n1 = len(frames)\n"
                "    for b in trailer_bytes:\n"
                "        if b == 126:\n"
                "            on, buf = True, []\n"
                "        elif b == 127 and on:\n"
                "            if len(buf) >= 2:\n"
                "                frames.append(buf[:-1])\n"
                "            on = False\n"
                "        elif on:\n"
                "            buf.append(b)\n"
                "    return [n1, len(frames), sum(frames[-1]) if frames else 0]\n"
            ),
        ],
        "reference_with_helper": (
            "def parse_chunked_with_trailer(chunks, trailer_bytes):\n"
            "    state = ('IDLE', False, [])\n"
            "    frames = []\n"
            "    for chunk in chunks:\n"
            "        for byte_val in chunk:\n"
            "            state, frame = {OP}(state, byte_val)\n"
            "            if frame is not None:\n"
            "                frames.append(frame)\n"
            "    n1 = len(frames)\n"
            "    for byte_val in trailer_bytes:\n"
            "        state, frame = {OP}(state, byte_val)\n"
            "        if frame is not None:\n"
            "            frames.append(frame)\n"
            "    return [n1, len(frames), sum(frames[-1]) if frames else 0]\n"
        ),
        "public_cases": [
            # Frame 1 split across chunks 0 & 1; Frame 2 starts in chunk 1 with ESC at end, completed in trailer!
            # Frame 1: [126, 4, 4, 127]; Frame 2: payload=[126, 2], chk=124 -> [126, 125] + [94, 2, 124, 127]
            {"label": "esc_frame_xor_split_into_trailer", "args": [[[126, 4], [4, 127, 126, 125]], [94, 2, 124, 127]], "expected": [1, 2, 128]},
            {"label": "resync_across_chunk_and_bad_trailer_checksum", "args": [[[126, 9], [126, 12, 12, 127, 126, 8]], [99, 127]], "expected": [1, 1, 12]},
        ],
        "hidden_cases": [
            {"label": "empty_chunks_valid_trailer", "args": [[], [126, 7, 3, 4, 127]], "expected": [0, 1, 10]},
            {"label": "all_invalid", "args": [[[126, 1, 2]], [127]], "expected": [0, 0, 0]},
        ],
    },
    {
        "problem_id": "fsm_04_min_coins_dp_decoy",
        "family": "protocol_fsm",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "step_frame_parser",
        "entry_point": "min_coins_needed",
        "statement": (
            "Write `min_coins_needed(coins, amount)` taking positive integer coin denominations `coins` "
            "and non-negative integer `amount`, returning the fewest coins summing to `amount` (or `-1` if impossible)."
        ),
        "failed_attempts": [
            (
                "def min_coins_needed(coins, amount):\n"
                "    rem = amount\n"
                "    cnt = 0\n"
                "    for c in sorted(coins, reverse=True):\n"
                "        cnt += rem // c\n"
                "        rem %= c\n"
                "    return cnt if rem == 0 else -1\n"
            ),
            (
                "def min_coins_needed(coins, amount):\n"
                "    if amount == 0:\n"
                "        return 0\n"
                "    best = 10**9\n"
                "    for c in coins:\n"
                "        if amount % c == 0:\n"
                "            best = min(best, amount // c)\n"
                "    return best if best < 10**9 else -1\n"
            ),
        ],
        "reference_with_helper": (
            "def min_coins_needed(coins, amount):\n"
            "    inf = amount + 1\n"
            "    dp = [inf] * (amount + 1)\n"
            "    dp[0] = 0\n"
            "    for a in range(1, amount + 1):\n"
            "        for c in coins:\n"
            "            if c <= a and dp[a - c] + 1 < dp[a]:\n"
            "                dp[a] = dp[a - c] + 1\n"
            "    return dp[amount] if dp[amount] <= amount else -1\n"
        ),
        "public_cases": [
            {"label": "greedy_coin_trap_dp", "args": [[1, 3, 4], 6], "expected": 2},
            {"label": "mixed_coin_sum_dp", "args": [[1, 3, 4], 7], "expected": 2},
            {"label": "unreachable_amount_dp", "args": [[2, 5], 3], "expected": -1},
        ],
        "hidden_cases": [
            {"label": "zero_amount", "args": [[1, 5], 0], "expected": 0},
            {"label": "non_canonical_denominations", "args": [[1, 6, 10], 12], "expected": 2},
        ],
    },
]


# Strictly disjoint validation development families reserved for Stage 2
# paired installation outcomes & frozen predictor evaluation (`--dev-split val`).
# Zero overlap with DEV_PROBLEMS above; sealed holdout remains untouched.
DEV_VAL_PROBLEMS: list[dict[str, Any]] = [
    # ------------------------------------------------------------------
    # Validation Family 4: version_semver (helper: parse_semver_key)
    # ------------------------------------------------------------------
    {
        "problem_id": "sem_01_sort_valid_versions",
        "family": "version_semver",
        "utility_regime": "useful_once",
        "helper_name": "parse_semver_key",
        "entry_point": "sort_valid_semvers",
        "statement": (
            "Write `sort_valid_semvers(versions)` filtering only strictly valid SemVer 2.0 strings "
            "from `versions` and returning them sorted in ascending SemVer 2.0 precedence order "
            "(tie-breaking equal precedence by the original string). " + _SEMVER_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def sort_valid_semvers(versions):\n"
                "    out = []\n"
                "    for v in versions:\n"
                "        parts = v.split('.')\n"
                "        if len(parts) == 3 and all(p.isdigit() for p in parts):\n"
                "            out.append((tuple(int(p) for p in parts), v))\n"
                "    return [v for _, v in sorted(out)]\n"
            ),
            (
                "def sort_valid_semvers(versions):\n"
                "    def key(v):\n"
                "        core = v.split('-', 1)[0].split('+', 1)[0]\n"
                "        nums = tuple(int(x) for x in core.split('.'))\n"
                "        return (nums, v)\n"
                "    return sorted([v for v in versions if len(v.split('.')) >= 3], key=key)\n"
            ),
        ],
        "reference_with_helper": (
            "def sort_valid_semvers(versions):\n"
            "    valid = []\n"
            "    for ver_str in versions:\n"
            "        ok, key = {OP}(ver_str)\n"
            "        if ok:\n"
            "            valid.append((key, ver_str))\n"
            "    valid.sort()\n"
            "    return [v for _, v in valid]\n"
        ),
        "public_cases": [
            {
                "label": "prerelease_precedence_and_leading_zero_filter",
                "args": [["1.0.0", "1.0.0-alpha.10", "1.0.0-alpha.2", "01.0.0", "1.0.0-alpha.beta"]],
                "expected": ["1.0.0-alpha.2", "1.0.0-alpha.10", "1.0.0-alpha.beta", "1.0.0"],
            },
            {
                "label": "build_metadata_ignored_and_invalid_pre_zero",
                "args": [["1.0.0+b2", "1.0.0+b1", "1.0.0-01", "1.0.0-1"]],
                "expected": ["1.0.0-1", "1.0.0+b1", "1.0.0+b2"],
            },
        ],
        "hidden_cases": [
            {"label": "invalid_only", "args": [["1.2", "1.02.3", "1.2.3-"]], "expected": []},
            {"label": "pre_shorter_tuple_first", "args": [["1.0.0-alpha.1", "1.0.0-alpha", "1.0.0-1", "1.0.0"]], "expected": ["1.0.0-1", "1.0.0-alpha", "1.0.0-alpha.1", "1.0.0"]},
        ],
    },
    {
        "problem_id": "sem_02_compatible_upgrade_pair",
        "family": "version_semver",
        "utility_regime": "repeatedly_useful",
        "helper_name": "parse_semver_key",
        "entry_point": "best_compatible_upgrade",
        "statement": (
            "Write `best_compatible_upgrade(current_ver, candidates)` that validates `current_ver` "
            "(returning `None` if invalid) and returns the highest-precedence valid SemVer 2.0 string in "
            "`candidates` that has the SAME major version as `current_ver` and strictly higher precedence "
            "than `current_ver` (tie-breaking equal precedence by lexicographically smallest string; "
            "returning `None` if no candidate qualifies). " + _SEMVER_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def best_compatible_upgrade(current_ver, candidates):\n"
                "    c_maj = int(current_ver.split('.')[0])\n"
                "    cands = [v for v in candidates if v.startswith(str(c_maj) + '.') and v > current_ver]\n"
                "    return max(cands) if cands else None\n"
            ),
            (
                "def best_compatible_upgrade(current_ver, candidates):\n"
                "    def p(v):\n"
                "        c = v.split('-', 1)[0].split('+', 1)[0].split('.')\n"
                "        return tuple(int(x) for x in c)\n"
                "    cur = p(current_ver)\n"
                "    best = None\n"
                "    for v in candidates:\n"
                "        kv = p(v)\n"
                "        if kv[0] == cur[0] and kv > cur:\n"
                "            if best is None or kv > p(best):\n"
                "                best = v\n"
                "    return best\n"
            ),
        ],
        "reference_with_helper": (
            "def best_compatible_upgrade(current_ver, candidates):\n"
            "    cur_ok, cur_key = {OP}(current_ver)\n"
            "    if not cur_ok:\n"
            "        return None\n"
            "    best_key = None\n"
            "    best_ver = None\n"
            "    for ver_str in candidates:\n"
            "        ok, key = {OP}(ver_str)\n"
            "        if not ok or key[0] != cur_key[0] or key <= cur_key:\n"
            "            continue\n"
            "        if best_key is None or key > best_key or (key == best_key and ver_str < best_ver):\n"
            "            best_key = key\n"
            "            best_ver = ver_str\n"
            "    return best_ver\n"
        ),
        "public_cases": [
            {
                "label": "prerelease_to_release_upgrade_same_major",
                "args": ["2.1.0-alpha.2", ["2.1.0-alpha.10", "2.1.0+meta", "3.0.0", "2.02.0"]],
                "expected": "2.1.0+meta",
            },
            {
                "label": "build_only_diff_not_strictly_greater",
                "args": ["1.2.3+a", ["1.2.3+z", "1.2.4-01", "1.2.4-rc.1"]],
                "expected": "1.2.4-rc.1",
            },
        ],
        "hidden_cases": [
            {"label": "invalid_current", "args": ["01.2.3", ["1.2.4"]], "expected": None},
            {"label": "no_upgrade", "args": ["1.5.0", ["1.5.0-rc.1", "2.0.0"]], "expected": None},
        ],
    },
    {
        "problem_id": "sem_03_range_filter_and_max",
        "family": "version_semver",
        "utility_regime": "repeatedly_useful",
        "helper_name": "parse_semver_key",
        "entry_point": "semver_range_summary",
        "statement": (
            "Write `semver_range_summary(min_ver, max_ver, candidates)` returning `[count_in_range, highest_ver]` "
            "counting valid SemVer 2.0 candidates satisfying `min_ver <= c <= max_ver` under SemVer 2.0 "
            "precedence (returns `[0, '']` if either bound is invalid or no candidate matches; tie-breaks "
            "equal highest precedence by lexicographically smallest string). " + _SEMVER_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def semver_range_summary(min_ver, max_ver, candidates):\n"
                "    hits = [c for c in candidates if min_ver <= c <= max_ver]\n"
                "    return [len(hits), max(hits) if hits else '']\n"
            ),
            (
                "def semver_range_summary(min_ver, max_ver, candidates):\n"
                "    def p(v):\n"
                "        return tuple(int(x) for x in v.split('-', 1)[0].split('+', 1)[0].split('.'))\n"
                "    lo, hi = p(min_ver), p(max_ver)\n"
                "    hits = [(p(c), c) for c in candidates if lo <= p(c) <= hi]\n"
                "    return [len(hits), max(hits)[1] if hits else '']\n"
            ),
        ],
        "reference_with_helper": (
            "def semver_range_summary(min_ver, max_ver, candidates):\n"
            "    ok_lo, lo_key = {OP}(min_ver)\n"
            "    ok_hi, hi_key = {OP}(max_ver)\n"
            "    if not ok_lo or not ok_hi or lo_key > hi_key:\n"
            "        return [0, '']\n"
            "    count = 0\n"
            "    best_key = None\n"
            "    best_ver = ''\n"
            "    for ver_str in candidates:\n"
            "        ok, key = {OP}(ver_str)\n"
            "        if ok and lo_key <= key <= hi_key:\n"
            "            count += 1\n"
            "            if best_key is None or key > best_key or (key == best_key and ver_str < best_ver):\n"
            "                best_key = key\n"
            "                best_ver = ver_str\n"
            "    return [count, best_ver]\n"
        ),
        "public_cases": [
            {
                "label": "prerelease_range_bounds_and_invalid_skip",
                "args": ["1.0.0-alpha.2", "1.0.0", ["1.0.0-alpha.1", "1.0.0-alpha.10", "1.0.0-beta", "1.0.0+b", "1.0.0-01"]],
                "expected": [3, "1.0.0+b"],
            },
            {
                "label": "invalid_bound_returns_empty",
                "args": ["01.0.0", "2.0.0", ["1.5.0"]],
                "expected": [0, ""],
            },
        ],
        "hidden_cases": [
            {"label": "numeric_before_alpha_in_range", "args": ["1.0.0-1", "1.0.0-alpha", ["1.0.0-2", "1.0.0-alpha.1", "1.0.0-alpha"]], "expected": [2, "1.0.0-alpha"]},
            {"label": "no_match", "args": ["2.0.0", "3.0.0", ["1.9.9", "3.0.1"]], "expected": [0, ""]},
        ],
    },
    {
        "problem_id": "sem_04_longest_palindrome_decoy",
        "family": "version_semver",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "parse_semver_key",
        "entry_point": "longest_palindrome_len",
        "statement": (
            "Write `longest_palindrome_len(s)` taking a lowercase ASCII string `s` and returning the "
            "length of the longest palindromic contiguous substring of `s` (`0` if `s` is empty)."
        ),
        "failed_attempts": [
            (
                "def longest_palindrome_len(s):\n"
                "    return len(s) if s == s[::-1] else (1 if s else 0)\n"
            ),
            (
                "def longest_palindrome_len(s):\n"
                "    best = 0\n"
                "    for i in range(len(s)):\n"
                "        l, r = i, i + 1\n"
                "        while l >= 0 and r < len(s) and s[l] == s[r]:\n"
                "            best = max(best, r - l + 1)\n"
                "            l -= 1\n"
                "            r += 1\n"
                "    return best\n"
            ),
        ],
        "reference_with_helper": (
            "def longest_palindrome_len(s):\n"
            "    if not s:\n"
            "        return 0\n"
            "    best = 1\n"
            "    n = len(s)\n"
            "    for c in range(n):\n"
            "        for l, r in ((c, c), (c, c + 1)):\n"
            "            while l >= 0 and r < n and s[l] == s[r]:\n"
            "                if r - l + 1 > best:\n"
            "                    best = r - l + 1\n"
            "                l -= 1\n"
            "                r += 1\n"
            "    return best\n"
        ),
        "public_cases": [
            {"label": "odd_palindrome_substring", "args": ["abacdfgdcaba"], "expected": 3},
            {"label": "even_and_odd_palindromic_center", "args": ["babad"], "expected": 3},
        ],
        "hidden_cases": [
            {"label": "empty_string", "args": [""], "expected": 0},
            {"label": "even_center", "args": ["xabban"], "expected": 4},
        ],
    },
    # ------------------------------------------------------------------
    # Validation Family 5: calendar_business (helper: shift_business_day)
    # ------------------------------------------------------------------
    {
        "problem_id": "cal_01_settlement_schedule",
        "family": "calendar_business",
        "utility_regime": "useful_once",
        "helper_name": "shift_business_day",
        "entry_point": "compute_settlement_dates",
        "statement": (
            "Write `compute_settlement_dates(trades, holidays)` where each trade is `[year, month, day, t_plus]` "
            "(`t_plus` is a signed integer business-day offset) and `holidays` is `[[y, m, d], ...]`. "
            "Return the list of settled `[y, m, d]` dates. " + _CAL_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def compute_settlement_dates(trades, holidays):\n"
                "    return [[y, m, d + t] for y, m, d, t in trades]\n"
            ),
            (
                "def compute_settlement_dates(trades, holidays):\n"
                "    import datetime\n"
                "    out = []\n"
                "    for y, m, d, t in trades:\n"
                "        cur = datetime.date(y, m, d) + datetime.timedelta(days=t)\n"
                "        out.append([cur.year, cur.month, cur.day])\n"
                "    return out\n"
            ),
        ],
        "reference_with_helper": (
            "def compute_settlement_dates(trades, holidays):\n"
            "    out = []\n"
            "    for y, m, d, t_plus in trades:\n"
            "        ymd = [y, m, d]\n"
            "        day = {OP}(ymd, t_plus, holidays)\n"
            "        out.append(day)\n"
            "    return out\n"
        ),
        "public_cases": [
            {
                "label": "leap_year_and_century_holiday_skip",
                "args": [[[2024, 2, 28, 2], [2100, 2, 26, 2], [2025, 1, 1, 0]], [[2025, 1, 1]]],
                "expected": [[2024, 3, 1], [2100, 3, 2], [2025, 1, 2]],
            },
            {
                "label": "backward_shift_across_weekend_and_holiday",
                "args": [[[2025, 1, 6, -2]], [[2025, 1, 3]]],
                "expected": [[2025, 1, 1]],
            },
        ],
        "hidden_cases": [
            {"label": "weekend_zero_snap", "args": [[[2025, 1, 4, 0]], [[2025, 1, 6]]], "expected": [[2025, 1, 7]]},
            {"label": "empty_trades", "args": [[], []], "expected": []},
        ],
    },
    {
        "problem_id": "cal_02_window_endpoints_and_overlap",
        "family": "calendar_business",
        "utility_regime": "repeatedly_useful",
        "helper_name": "shift_business_day",
        "entry_point": "business_window_count",
        "statement": (
            "Write `business_window_count(anchor_ymd, back_days, fwd_days, check_dates, holidays)` "
            "computing `start_day = shift(anchor_ymd, -back_days, holidays)` and "
            "`end_day = shift(anchor_ymd, fwd_days, holidays)`, returning `[start_day, end_day, in_window_count]` "
            "counting how many dates `d` in `check_dates` satisfy `start_day <= d <= end_day` (lexicographic `[y, m, d]`). "
            + _CAL_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def business_window_count(anchor_ymd, back_days, fwd_days, check_dates, holidays):\n"
                "    import datetime\n"
                "    a = datetime.date(*anchor_ymd)\n"
                "    s = a - datetime.timedelta(days=back_days)\n"
                "    e = a + datetime.timedelta(days=fwd_days)\n"
                "    sd, ed = [s.year, s.month, s.day], [e.year, e.month, e.day]\n"
                "    return [sd, ed, sum(1 for d in check_dates if sd <= d <= ed)]\n"
            ),
            (
                "def business_window_count(anchor_ymd, back_days, fwd_days, check_dates, holidays):\n"
                "    import datetime\n"
                "    def move(ymd, delta):\n"
                "        cur = datetime.date(*ymd)\n"
                "        step = 1 if delta >= 0 else -1\n"
                "        rem = abs(delta)\n"
                "        while rem > 0:\n"
                "            cur += datetime.timedelta(days=step)\n"
                "            if cur.weekday() < 5:\n"
                "                rem -= 1\n"
                "        return [cur.year, cur.month, cur.day]\n"
                "    sd, ed = move(anchor_ymd, -back_days), move(anchor_ymd, fwd_days)\n"
                "    return [sd, ed, sum(1 for d in check_dates if sd <= d <= ed)]\n"
            ),
        ],
        "reference_with_helper": (
            "def business_window_count(anchor_ymd, back_days, fwd_days, check_dates, holidays):\n"
            "    start_day = {OP}(anchor_ymd, -back_days, holidays)\n"
            "    end_day = {OP}(anchor_ymd, fwd_days, holidays)\n"
            "    cnt = sum(1 for d in check_dates if start_day <= d <= end_day)\n"
            "    return [start_day, end_day, cnt]\n"
        ),
        "public_cases": [
            {
                "label": "holiday_extended_window_both_sides",
                "args": [[2025, 1, 6], 2, 2, [[2025, 1, 1], [2025, 1, 9], [2025, 1, 10]], [[2025, 1, 3], [2025, 1, 7]]],
                "expected": [[2025, 1, 1], [2025, 1, 9], 2],
            },
            {
                "label": "zero_back_snaps_weekend_anchor",
                "args": [[2025, 1, 4], 0, 1, [[2025, 1, 6], [2025, 1, 7]], []],
                "expected": [[2025, 1, 6], [2025, 1, 6], 1],
            },
        ],
        "hidden_cases": [
            {"label": "leap_year_crossing", "args": [[2024, 2, 29], 1, 1, [[2024, 2, 28], [2024, 3, 1]], []], "expected": [[2024, 2, 28], [2024, 3, 1], 2]},
            {"label": "year_rollover", "args": [[2025, 1, 2], 2, 1, [[2024, 12, 30], [2025, 1, 3]], [[2025, 1, 1]]], "expected": [[2024, 12, 30], [2025, 1, 3], 2]},
        ],
    },
    {
        "problem_id": "cal_03_chained_milestone_dates",
        "family": "calendar_business",
        "utility_regime": "repeatedly_useful",
        "helper_name": "shift_business_day",
        "entry_point": "chained_milestone_review",
        "statement": (
            "Write `chained_milestone_review(start_ymd, phase_offsets, review_lag, holidays)` that first "
            "snaps `cur = shift(start_ymd, 0, holidays)`, then applies each signed offset in `phase_offsets` "
            "sequentially (`cur = shift(cur, off, holidays)`), and finally computes "
            "`review = shift(cur, review_lag, holidays)`, returning `[cur, review]`. " + _CAL_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def chained_milestone_review(start_ymd, phase_offsets, review_lag, holidays):\n"
                "    import datetime\n"
                "    cur = datetime.date(*start_ymd) + datetime.timedelta(days=sum(phase_offsets))\n"
                "    rev = cur + datetime.timedelta(days=review_lag)\n"
                "    return [[cur.year, cur.month, cur.day], [rev.year, rev.month, rev.day]]\n"
            ),
            (
                "def chained_milestone_review(start_ymd, phase_offsets, review_lag, holidays):\n"
                "    import datetime\n"
                "    cur = datetime.date(*start_ymd)\n"
                "    for off in phase_offsets:\n"
                "        cur += datetime.timedelta(days=off)\n"
                "    rev = cur + datetime.timedelta(days=review_lag)\n"
                "    return [[cur.year, cur.month, cur.day], [rev.year, rev.month, rev.day]]\n"
            ),
        ],
        "reference_with_helper": (
            "def chained_milestone_review(start_ymd, phase_offsets, review_lag, holidays):\n"
            "    cur = {OP}(start_ymd, 0, holidays)\n"
            "    for off in phase_offsets:\n"
            "        cur = {OP}(cur, off, holidays)\n"
            "    rev = {OP}(cur, review_lag, holidays)\n"
            "    return [cur, rev]\n"
        ),
        "public_cases": [
            {
                "label": "weekend_start_holiday_chain_and_review",
                "args": [[2025, 1, 4], [2, -1], 2, [[2025, 1, 6]]],
                "expected": [[2025, 1, 8], [2025, 1, 10]],
            },
            {
                "label": "century_boundary_chain",
                "args": [[2100, 2, 26], [1, 1], 1, []],
                "expected": [[2100, 3, 2], [2100, 3, 3]],
            },
        ],
        "hidden_cases": [
            {"label": "empty_phases_snap_only", "args": [[2025, 1, 1], [], 0, [[2025, 1, 1]]], "expected": [[2025, 1, 2], [2025, 1, 2]]},
            {"label": "multi_holiday_cluster", "args": [[2024, 12, 30], [2], 1, [[2024, 12, 31], [2025, 1, 1]]], "expected": [[2025, 1, 3], [2025, 1, 6]]},
        ],
    },
    {
        "problem_id": "cal_04_interval_room_schedule_decoy",
        "family": "calendar_business",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "shift_business_day",
        "entry_point": "min_meeting_rooms",
        "statement": (
            "Write `min_meeting_rooms(meetings)` taking half-open integer timestamp meetings `[start, end)` "
            "(a meeting ending at `t` does NOT conflict with one starting at `t`) and returning the "
            "minimum number of concurrent rooms needed."
        ),
        "failed_attempts": [
            (
                "def min_meeting_rooms(meetings):\n"
                "    events = []\n"
                "    for s, e in meetings:\n"
                "        events.append((s, 1))\n"
                "        events.append((e, -1))\n"
                "    events.sort(key=lambda x: (x[0], -x[1]))\n"
                "    cur = best = 0\n"
                "    for _, d in events:\n"
                "        cur += d\n"
                "        best = max(best, cur)\n"
                "    return best\n"
            ),
            (
                "def min_meeting_rooms(meetings):\n"
                "    if not meetings:\n"
                "        return 0\n"
                "    xs = sorted(meetings)\n"
                "    rooms = 1\n"
                "    for i in range(1, len(xs)):\n"
                "        if xs[i][0] < xs[i - 1][1]:\n"
                "            rooms += 1\n"
                "    return rooms\n"
            ),
        ],
        "reference_with_helper": (
            "def min_meeting_rooms(meetings):\n"
            "    events = []\n"
            "    for s, e in meetings:\n"
            "        events.append((s, 1))\n"
            "        events.append((e, -1))\n"
            "    events.sort(key=lambda x: (x[0], x[1]))\n"
            "    cur = best = 0\n"
            "    for _, d in events:\n"
            "        cur += d\n"
            "        if cur > best:\n"
            "            best = cur\n"
            "    return best\n"
        ),
        "public_cases": [
            {"label": "touching_half_open_tiebreak", "args": [[[0, 10], [10, 20]]], "expected": 1},
            {"label": "disjoint_clusters_no_room_release", "args": [[[1, 4], [2, 5], [10, 14], [11, 15]]], "expected": 2},
        ],
        "hidden_cases": [
            {"label": "empty_meetings", "args": [[]], "expected": 0},
            {"label": "three_concurrent", "args": [[[1, 10], [2, 7], [3, 19], [8, 12], [10, 20]]], "expected": 3},
        ],
    },
    # ------------------------------------------------------------------
    # Validation Family 6: expr_rpn_vm (helper: eval_safe_op)
    # ------------------------------------------------------------------
    {
        "problem_id": "vm_01_eval_program",
        "family": "expr_rpn_vm",
        "utility_regime": "useful_once",
        "helper_name": "eval_safe_op",
        "entry_point": "run_rpn_program",
        "statement": (
            "Write `run_rpn_program(prog, env)` executing RPN token list `prog` against variable dict `env` "
            "starting from an empty stack, returning `[True, stack[-1]]` iff every instruction succeeds and "
            "the final stack has length 1, else `[False, 0]`. " + _VM_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def run_rpn_program(prog, env):\n"
                "    st = []\n"
                "    for t in prog:\n"
                "        if t.lstrip('-').isdigit():\n"
                "            st.append(int(t))\n"
                "        elif t == 'ADD':\n"
                "            st.append(st.pop() + st.pop())\n"
                "        elif t == 'DIV':\n"
                "            b, a = st.pop(), st.pop()\n"
                "            st.append(a // b)\n"
                "        elif t == 'MUL':\n"
                "            st.append(st.pop() * st.pop())\n"
                "    return [len(st) == 1, st[-1] if len(st) == 1 else 0]\n"
            ),
            (
                "def run_rpn_program(prog, env):\n"
                "    st = []\n"
                "    for t in prog:\n"
                "        if t.startswith('$'):\n"
                "            st.append(env.get(t[1:], 0))\n"
                "        elif t.lstrip('-').isdigit():\n"
                "            st.append(int(t))\n"
                "        elif t == 'DIV':\n"
                "            b, a = st.pop(), st.pop()\n"
                "            if b == 0:\n"
                "                return [False, 0]\n"
                "            st.append(a // b)\n"
                "        elif t == 'MUL':\n"
                "            st.append(st.pop() * st.pop())\n"
                "    return [len(st) == 1, st[-1] if len(st) == 1 else 0]\n"
            ),
        ],
        "reference_with_helper": (
            "def run_rpn_program(prog, env):\n"
            "    stack = []\n"
            "    for op_tok in prog:\n"
            "        ok, stack = {OP}(stack, op_tok, env)\n"
            "        if not ok:\n"
            "            return [False, 0]\n"
            "    if len(stack) != 1:\n"
            "        return [False, 0]\n"
            "    return [True, stack[0]]\n"
        ),
        "public_cases": [
            {"label": "negative_truncating_div_and_saturation", "args": [["-7", "2", "DIV", "5000", "MUL"], {}], "expected": [True, -10000]},
            {"label": "missing_var_and_clamp_guard", "args": [["$x", "10", "5", "CLAMP"], {"x": 8}], "expected": [False, 0]},
        ],
        "hidden_cases": [
            {"label": "dup_swap_sub_clamp_valid", "args": [["$a", "DUP", "3", "ADD", "SWAP", "SUB", "0", "100", "CLAMP"], {"a": 10}], "expected": [True, 3]},
            {"label": "div_by_zero_fail", "args": [["9", "0", "DIV"], {}], "expected": [False, 0]},
        ],
    },
    {
        "problem_id": "vm_02_batch_eval_with_fallback",
        "family": "expr_rpn_vm",
        "utility_regime": "repeatedly_useful",
        "helper_name": "eval_safe_op",
        "entry_point": "eval_batch_with_fallback",
        "statement": (
            "Write `eval_batch_with_fallback(primary_prog, fallback_prog, envs)` that for each dict `env` "
            "in `envs` executes `primary_prog` on a fresh stack; if all steps succeed and `len(stack) == 1`, "
            "append `['primary', stack[0]]`; otherwise execute `fallback_prog` on a fresh stack and append "
            "`['fallback', stack[0]]` if all steps succeed with `len(stack) == 1`, else `['error', 0]`. "
            + _VM_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def eval_batch_with_fallback(primary_prog, fallback_prog, envs):\n"
                "    out = []\n"
                "    for env in envs:\n"
                "        st = []\n"
                "        try:\n"
                "            for t in primary_prog:\n"
                "                if t.startswith('$'):\n"
                "                    st.append(env[t[1:]])\n"
                "                elif t == 'DIV':\n"
                "                    b, a = st.pop(), st.pop()\n"
                "                    st.append(a // b)\n"
                "                else:\n"
                "                    st.append(int(t))\n"
                "            out.append(['primary', st[-1]])\n"
                "        except Exception:\n"
                "            out.append(['error', 0])\n"
                "    return out\n"
            ),
            (
                "def eval_batch_with_fallback(primary_prog, fallback_prog, envs):\n"
                "    def run(p, env):\n"
                "        st = []\n"
                "        for t in p:\n"
                "            if t.startswith('$'):\n"
                "                if t[1:] not in env:\n"
                "                    return None\n"
                "                st.append(env[t[1:]])\n"
                "            elif t == 'DIV':\n"
                "                b, a = st.pop(), st.pop()\n"
                "                if b == 0:\n"
                "                    return None\n"
                "                st.append(a // b)\n"
                "            elif t == 'ADD':\n"
                "                st.append(st.pop() + st.pop())\n"
                "            else:\n"
                "                st.append(int(t))\n"
                "        return st[0] if len(st) == 1 else None\n"
                "    out = []\n"
                "    for env in envs:\n"
                "        v = run(primary_prog, env)\n"
                "        if v is not None:\n"
                "            out.append(['primary', v])\n"
                "        else:\n"
                "            v2 = run(fallback_prog, env)\n"
                "            out.append(['fallback', v2] if v2 is not None else ['error', 0])\n"
                "    return out\n"
            ),
        ],
        "reference_with_helper": (
            "def eval_batch_with_fallback(primary_prog, fallback_prog, envs):\n"
            "    out = []\n"
            "    for env in envs:\n"
            "        st = []\n"
            "        ok_all = True\n"
            "        for op_tok in primary_prog:\n"
            "            ok, st = {OP}(st, op_tok, env)\n"
            "            if not ok:\n"
            "                ok_all = False\n"
            "                break\n"
            "        if ok_all and len(st) == 1:\n"
            "            out.append(['primary', st[0]])\n"
            "            continue\n"
            "        st2 = []\n"
            "        ok_fb = True\n"
            "        for op_tok in fallback_prog:\n"
            "            ok, st2 = {OP}(st2, op_tok, env)\n"
            "            if not ok:\n"
            "                ok_fb = False\n"
            "                break\n"
            "        if ok_fb and len(st2) == 1:\n"
            "            out.append(['fallback', st2[0]])\n"
            "        else:\n"
            "            out.append(['error', 0])\n"
            "    return out\n"
        ),
        "public_cases": [
            {
                "label": "primary_trunc_div_fallback_and_error",
                "args": [["$a", "$b", "DIV"], ["$a", "0", "10", "CLAMP"], [{"a": -7, "b": 2}, {"a": 25, "b": 0}, {"b": 0}]],
                "expected": [["primary", -3], ["fallback", 10], ["error", 0]],
            },
            {
                "label": "extra_stack_triggers_fallback",
                "args": [["1", "2"], ["$k", "20000", "ADD"], [{"k": 5}]],
                "expected": [["fallback", 10000]],
            },
        ],
        "hidden_cases": [
            {"label": "empty_envs", "args": [["1"], ["2"], []], "expected": []},
            {"label": "both_error_underflow", "args": [["DROP"], ["SWAP"], [{}]], "expected": [["error", 0]]},
        ],
    },
    {
        "problem_id": "vm_03_prefix_then_branch_eval",
        "family": "expr_rpn_vm",
        "utility_regime": "repeatedly_useful",
        "helper_name": "eval_safe_op",
        "entry_point": "eval_branched_rpn",
        "statement": (
            "Write `eval_branched_rpn(setup_prog, pos_prog, neg_prog, env)` that executes `setup_prog` "
            "starting on an empty stack; if any step fails or the stack is empty afterward return `[False, 0]`; "
            "otherwise inspect top `v = stack[-1]` (without popping it) and continue executing `pos_prog` if "
            "`v >= 0` else `neg_prog` on the SAME stack, returning `[True, stack[-1]]` iff all branch steps "
            "succeed and final `len(stack) >= 1`, else `[False, 0]`. " + _VM_SPEC_TEXT
        ),
        "failed_attempts": [
            (
                "def eval_branched_rpn(setup_prog, pos_prog, neg_prog, env):\n"
                "    st = []\n"
                "    for t in setup_prog:\n"
                "        st.append(env[t[1:]] if t.startswith('$') else int(t))\n"
                "    branch = pos_prog if st[-1] >= 0 else neg_prog\n"
                "    for t in branch:\n"
                "        if t == 'ADD':\n"
                "            st.append(st.pop() + st.pop())\n"
                "    return [True, st[-1]]\n"
            ),
            (
                "def eval_branched_rpn(setup_prog, pos_prog, neg_prog, env):\n"
                "    st = []\n"
                "    for t in setup_prog + pos_prog:\n"
                "        if t.startswith('$') and t[1:] in env:\n"
                "            st.append(env[t[1:]])\n"
                "        elif t.lstrip('-').isdigit():\n"
                "            st.append(int(t))\n"
                "        elif t == 'DIV' and len(st) >= 2:\n"
                "            b, a = st.pop(), st.pop()\n"
                "            st.append(a // b)\n"
                "    return [bool(st), st[-1] if st else 0]\n"
            ),
        ],
        "reference_with_helper": (
            "def eval_branched_rpn(setup_prog, pos_prog, neg_prog, env):\n"
            "    stack = []\n"
            "    for op_tok in setup_prog:\n"
            "        ok, stack = {OP}(stack, op_tok, env)\n"
            "        if not ok:\n"
            "            return [False, 0]\n"
            "    if not stack:\n"
            "        return [False, 0]\n"
            "    branch = pos_prog if stack[-1] >= 0 else neg_prog\n"
            "    for op_tok in branch:\n"
            "        ok, stack = {OP}(stack, op_tok, env)\n"
            "        if not ok:\n"
            "            return [False, 0]\n"
            "    if not stack:\n"
            "        return [False, 0]\n"
            "    return [True, stack[-1]]\n"
        ),
        "public_cases": [
            {"label": "neg_branch_trunc_div_and_clamp", "args": [["$x"], ["2", "MUL"], ["2", "DIV", "-5", "5", "CLAMP"], {"x": -9}], "expected": [True, -4]},
            {"label": "pos_branch_saturating_mul", "args": [["$x", "DUP"], ["5000", "MUL"], ["DROP"], {"x": 4}], "expected": [True, 10000]},
        ],
        "hidden_cases": [
            {"label": "setup_fails_missing_var", "args": [["$z"], ["1"], ["2"], {}], "expected": [False, 0]},
            {"label": "branch_empties_stack", "args": [["5"], ["DROP"], ["1"], {}], "expected": [False, 0]},
        ],
    },
    {
        "problem_id": "vm_04_graph_cycle_detect_decoy",
        "family": "expr_rpn_vm",
        "utility_regime": "irrelevant_decoy",
        "helper_name": "eval_safe_op",
        "entry_point": "has_directed_cycle",
        "statement": (
            "Write `has_directed_cycle(n, edges)` taking directed graph nodes `0..n-1` and directed edges "
            "`[u, v]`, returning `True` iff the graph contains a directed cycle, else `False`."
        ),
        "failed_attempts": [
            (
                "def has_directed_cycle(n, edges):\n"
                "    adj = [[] for _ in range(n)]\n"
                "    for u, v in edges:\n"
                "        adj[u].append(v)\n"
                "    seen = set()\n"
                "    for i in range(n):\n"
                "        if i in seen:\n"
                "            continue\n"
                "        q = [i]\n"
                "        while q:\n"
                "            u = q.pop()\n"
                "            if u in seen:\n"
                "                return True\n"
                "            seen.add(u)\n"
                "            q.extend(adj[u])\n"
                "    return False\n"
            ),
            (
                "def has_directed_cycle(n, edges):\n"
                "    return len(edges) >= n\n"
            ),
        ],
        "reference_with_helper": (
            "def has_directed_cycle(n, edges):\n"
            "    adj = [[] for _ in range(n)]\n"
            "    indeg = [0] * n\n"
            "    for u, v in edges:\n"
            "        adj[u].append(v)\n"
            "        indeg[v] += 1\n"
            "    q = [i for i in range(n) if indeg[i] == 0]\n"
            "    vis = 0\n"
            "    while q:\n"
            "        u = q.pop()\n"
            "        vis += 1\n"
            "        for v in adj[u]:\n"
            "            indeg[v] -= 1\n"
            "            if indeg[v] == 0:\n"
            "                q.append(v)\n"
            "    return vis != n\n"
        ),
        "public_cases": [
            {"label": "diamond_dag_no_directed_cycle", "args": [4, [[0, 1], [0, 2], [1, 3], [2, 3]]], "expected": False},
            {"label": "small_cycle_with_isolated", "args": [5, [[1, 2], [2, 1]]], "expected": True},
        ],
        "hidden_cases": [
            {"label": "self_loop_cycle", "args": [2, [[1, 1]]], "expected": True},
            {"label": "empty_graph", "args": [3, []], "expected": False},
        ],
    },
]


ALL_DEV_PROBLEMS: list[dict[str, Any]] = DEV_PROBLEMS + DEV_VAL_PROBLEMS


def get_dev_split(split_name: str = "train") -> list[dict[str, Any]]:
    if split_name == "train":
        return list(DEV_PROBLEMS)
    if split_name == "val":
        return list(DEV_VAL_PROBLEMS)
    if split_name == "all":
        return list(ALL_DEV_PROBLEMS)
    raise ValueError(f"Unknown dev split: {split_name!r} (expected 'train', 'val', or 'all')")


def get_problem(problem_id: str) -> dict[str, Any]:
    for prob in ALL_DEV_PROBLEMS:
        if prob["problem_id"] == problem_id:
            return prob
    raise KeyError(f"Unknown problem_id: {problem_id}")


def verify_dev_family_suite(
    helper_token_id: int = 259,
    problems: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Verify every dev problem's failed attempts FAIL and references PASS both alias and ordinary arms."""
    target_problems = list(ALL_DEV_PROBLEMS if problems is None else problems)
    rows = []
    for prob in target_problems:
        all_cases = prob["public_cases"] + prob["hidden_cases"]
        # 1. Both saved pre-switch attempts must fail public cases.
        for idx, bad_src in enumerate(prob["failed_attempts"], start=1):
            bad_v = verify_candidate(
                bad_src,
                entry_point=prob["entry_point"],
                cases=prob["public_cases"],
                helper_name=None,
                binding=None,
                arm_uses_alias=False,
            )
            if bad_v["passed"]:
                raise AssertionError(f"{prob['problem_id']} failed_attempt #{idx} unexpectedly passed")

        # 2. Reference solution must pass ALL public + hidden cases under ordinary named helper.
        helper_name = prob["helper_name"]
        ref_ord = prob["reference_with_helper"].replace("{OP}", helper_name)
        v_ord = verify_candidate(
            ref_ord,
            entry_point=prob["entry_point"],
            cases=all_cases,
            helper_name=helper_name,
            binding=None,
            arm_uses_alias=False,
        )
        if not v_ord["passed"]:
            raise AssertionError(f"{prob['problem_id']} ordinary reference failed: {v_ord}")

        # 3. Reference solution must pass ALL public + hidden cases under <H0> single binding.
        reg = SingleBindRegistry()
        binding = reg.bind_once(helper_name, helper_token_id, HELPER_TOKEN_SYMBOL)
        ref_alias = prob["reference_with_helper"].replace("{OP}", HELPER_TOKEN_SYMBOL)
        v_alias = verify_candidate(
            ref_alias,
            entry_point=prob["entry_point"],
            cases=all_cases,
            helper_name=helper_name,
            binding=binding,
            arm_uses_alias=True,
        )
        if not v_alias["passed"]:
            raise AssertionError(f"{prob['problem_id']} alias reference failed: {v_alias}")

        if v_ord["syntax_mask"] and not v_ord["syntax_mask"]["mask_ok"]:
            raise AssertionError(f"{prob['problem_id']} ordinary reference broke syntax mask")
        if v_alias["syntax_mask"] and not v_alias["syntax_mask"]["mask_ok"]:
            raise AssertionError(f"{prob['problem_id']} alias reference broke syntax mask")

        # Confirm helper call multiplicity matches utility regime.
        calls = v_alias["syntactic_helper_calls"]
        if prob["utility_regime"] == "useful_once" and calls != 1:
            raise AssertionError(f"{prob['problem_id']} useful_once should have 1 call site, got {calls}")
        if prob["utility_regime"] == "repeatedly_useful" and calls < 2:
            raise AssertionError(f"{prob['problem_id']} repeatedly_useful should have >=2 call sites, got {calls}")
        if prob["utility_regime"] == "irrelevant_decoy" and calls != 0:
            raise AssertionError(f"{prob['problem_id']} irrelevant_decoy reference should have 0 helper calls, got {calls}")

        rows.append(
            {
                "problem_id": prob["problem_id"],
                "family": prob["family"],
                "utility_regime": prob["utility_regime"],
                "helper_name": helper_name,
                "public_cases": len(prob["public_cases"]),
                "hidden_cases": len(prob["hidden_cases"]),
                "ref_syntactic_helper_calls": calls,
                "ref_runtime_helper_calls": v_alias["runtime_helper_calls"],
                "ordinary_passed": v_ord["passed"],
                "alias_passed": v_alias["passed"],
            }
        )

    families = sorted({r["family"] for r in rows})
    regimes = sorted({r["utility_regime"] for r in rows})
    return {
        "total_problems": len(rows),
        "families": families,
        "utility_regimes": regimes,
        "all_verified": True,
        "problems": rows,
    }
