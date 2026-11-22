#!/usr/bin/env python3
"""Phase 4 Lossless Encoding & Press-Count Bake-Off (strictly separate from capacity certification).

Evaluates 5 byte-exact lossless encoding regimes across all 21 already-frozen real code corpora
(9 from independent-eval + 12 from capacity-race-v1) under W2 (max_bytes = 160, whole excluded):
  1. literal_utf8:      raw UTF-8 bytes (8 bits/byte, 1 press/char, 0 dict bytes)
  2. bits6_no_escape:   64-slot 6-bit fixed-width dictionary with 0 escapes (only when FEASIBLE at K=64)
                        using minimum-press exact DP parsing; fills any spare slots (<64) with top W2 fragments
  3. bits6_escape:      63-slot + 1 escape (6 bits/token, 6+8=14 bits & 2 presses per escaped UTF-8 byte)
  4. bits7_128:         128-slot 7-bit fixed-width W2 dictionary (7 bits/token, 0 escapes when |Sigma|<=128)
  5. bits8_256:         256-slot 8-bit fixed-width W2 dictionary (8 bits/token, 0 escapes when |Sigma|<=256)

Every encoded file is independently round-trip decoded and checked for exact UTF-8 byte identity.
Reports presses, payload bytes, dictionary bytes, escape bytes, and total package bytes separately.
Press counts are token/key counts only and do NOT claim human typing speed.
"""
from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
DIAG_DIR = HERE.parent / "capacity-diagnostic-v1"
sys.path.insert(0, str(DIAG_DIR))

from diagnostic import (  # noqa: E402
    diagnose_full_corpus,
    is_token_eligible,
    suffix_shared_lengths,
)

MAX_BYTES = 160
RULE_K = 2


def serialize_dictionary_bytes(dictionary: list[str]) -> int:
    """Explicit lossless dictionary framing: 2-byte count + per entry (1-byte byte-len + UTF-8 bytes)."""
    return 2 + sum(1 + len(tok.encode("utf-8")) for tok in dictionary)


def optimal_parse_dp(
    source: str,
    vocab: list[str],
    token_bits: int,
    allow_escape: bool = False,
    escape_overhead_bits: int = 6,
) -> tuple[list[tuple[str, str]], int, int, int]:
    """Exact minimum-bit (tie-break minimum-press) DP parse of `source`.

    Returns (ops, total_bits, total_presses, escape_bytes) where each op is ('tok', s) or ('esc', ch).
    """
    by_first: dict[str, list[str]] = defaultdict(list)
    for tok in vocab:
        if tok:
            by_first[tok[0]].append(tok)
    n = len(source)
    INF = 10**18
    dp_bits = [INF] * (n + 1)
    dp_press = [INF] * (n + 1)
    parent: list[tuple[int, str, str] | None] = [None] * (n + 1)
    dp_bits[0] = 0
    dp_press[0] = 0

    for i in range(n):
        bi = dp_bits[i]
        if bi >= INF:
            continue
        pi = dp_press[i]
        ch = source[i]
        for tok in by_first.get(ch, ()):
            end = i + len(tok)
            if end <= n and source.startswith(tok, i):
                nb = bi + token_bits
                np_ = pi + 1
                if nb < dp_bits[end] or (nb == dp_bits[end] and np_ < dp_press[end]):
                    dp_bits[end] = nb
                    dp_press[end] = np_
                    parent[end] = (i, "tok", tok)
        if allow_escape:
            ch_bytes = len(ch.encode("utf-8"))
            nb = bi + escape_overhead_bits + 8 * ch_bytes
            np_ = pi + 1 + ch_bytes  # 1 escape press + raw byte/char entry
            end = i + 1
            if nb < dp_bits[end] or (nb == dp_bits[end] and np_ < dp_press[end]):
                dp_bits[end] = nb
                dp_press[end] = np_
                parent[end] = (i, "esc", ch)

    if dp_bits[n] >= INF:
        raise ValueError("Source is not parseable under the supplied vocabulary")

    ops: list[tuple[str, str]] = []
    esc_bytes = 0
    cur = n
    while cur > 0:
        prev, kind, text = parent[cur]  # type: ignore[misc]
        ops.append((kind, text))
        if kind == "esc":
            esc_bytes += len(text.encode("utf-8"))
        cur = prev
    ops.reverse()
    # Exact round-trip decode check
    decoded = "".join(text for _kind, text in ops)
    if decoded.encode("utf-8") != source.encode("utf-8"):
        raise RuntimeError("Round-trip byte decode mismatch")
    return ops, dp_bits[n], dp_press[n], esc_bytes


def candidate_w2_fragments(programs: list[str], max_bytes: int = 160, limit: int = 600) -> list[str]:
    """Collect high-value eligible W2 multi-char fragments via suffix_shared_lengths (no bloat)."""
    whole = set(programs)
    wit = suffix_shared_lengths(programs, k=2, max_bytes=max_bytes)
    # Count non-overlapping-ish occurrence score for left-maximal shared spans and short frequent spans
    freq: dict[str, int] = defaultdict(int)
    docs: dict[str, set[int]] = defaultdict(set)
    for pidx, s in enumerate(programs):
        row = wit[pidx]
        for a, w in enumerate(row):
            if w < 2:
                continue
            is_left_max = (a == 0) or (row[a - 1] < w + 1)
            # Sample lengths: 2, 3, 4, 6, 8, 12, 16, 24, 32, and full maximal w
            lens = {2, 3, 4, 6, 8, 12, 16, 24, 32, w}
            for L in lens:
                if 2 <= L <= w and (is_left_max or L <= 8):
                    sub = s[a : a + L]
                    if sub not in whole:
                        freq[sub] += 1
                        docs[sub].add(pidx)

    scored = []
    for sub, cnt in freq.items():
        if len(docs[sub]) >= 2:
            # Approximate net bit savings: (len-1)*cnt occurrences minus dict framing
            saving = (len(sub) - 1) * cnt - (1 + len(sub.encode("utf-8")))
            scored.append((saving, len(sub), sub))
    scored.sort(reverse=True)
    out = [sub for _, _, sub in scored[:limit]]
    return out


def fill_dictionary_slots(
    programs: list[str],
    base_vocab: list[str],
    max_slots: int,
    token_bits: int,
    allow_escape: bool = False,
    candidates: list[str] | None = None,
) -> list[str]:
    """Greedily fill spare dictionary slots up to `max_slots` maximizing exact bit reduction."""
    vocab = list(dict.fromkeys(base_vocab))
    if len(vocab) >= max_slots:
        return vocab[:max_slots]
    if candidates is None:
        candidates = candidate_w2_fragments(programs, max_bytes=MAX_BYTES)
    vocab_set = set(vocab)
    # Fast greedy selection using real parse-gain on concatenated stream / programs
    # Track current total payload bits + dict bytes, add best non-overlapping candidate iteratively
    # To keep runtime fast (<1s per corpus), use marginal saving estimate on current parse!
    for _ in range(max_slots - len(vocab)):
        # Parse once with current vocab
        cur_ops_all = []
        for s in programs:
            ops, _, _, _ = optimal_parse_dp(s, vocab, token_bits, allow_escape=allow_escape)
            cur_ops_all.append(ops)
        # Estimate gain of adding each unused candidate by counting consecutive literal/token runs it replaces
        # Faster exact proxy: count non-overlapping occurrences in each program of candidates not yet in vocab,
        # weighted by current bits spent on those spans!
        best_cand = None
        best_gain = 0
        # Build per-program cumulative bit arrays from current parse
        cum_bits_all = []
        for s, ops in zip(programs, cur_ops_all):
            cb = [0] * (len(s) + 1)
            pos = 0
            acc = 0
            for kind, text in ops:
                if kind == "tok":
                    acc += token_bits
                else:
                    acc += 6 + 8 * len(text.encode("utf-8"))
                nxt = pos + len(text)
                for p in range(pos + 1, nxt + 1):
                    cb[p] = acc
                pos = nxt
            cum_bits_all.append(cb)

        for cand in candidates:
            if cand in vocab_set:
                continue
            clen = len(cand)
            gain_bits = 0
            for s, cb in zip(programs, cum_bits_all):
                st = 0
                while True:
                    idx = s.find(cand, st)
                    if idx == -1:
                        break
                    span_bits = cb[idx + clen] - cb[idx]
                    if span_bits > token_bits:
                        gain_bits += span_bits - token_bits
                    st = idx + clen  # non-overlapping count
            # Subtract dictionary entry cost in bits (for fair end-to-end selection)
            net_bits = gain_bits - 8 * (1 + len(cand.encode("utf-8")))
            if net_bits > best_gain:
                best_gain = net_bits
                best_cand = cand
        if best_cand is None:
            break
        vocab.append(best_cand)
        vocab_set.add(best_cand)
    return vocab


def build_6bit_escape_vocab(programs: list[str], candidates: list[str]) -> list[str]:
    """Build a 63-slot dictionary (+ 1 reserved escape slot = 64 codes) maximizing exact savings."""
    whole = set(programs)
    char_freq: dict[str, int] = defaultdict(int)
    for s in programs:
        for ch in s:
            if ch not in whole:
                char_freq[ch] += 1
    # Keep top characters by frequency up to 63 slots, leaving room if frequent multi-char tokens beat rare chars
    ranked_chars = sorted(char_freq, key=lambda c: (-char_freq[c], c))
    if len(ranked_chars) <= 63:
        return fill_dictionary_slots(programs, ranked_chars, max_slots=63, token_bits=6, allow_escape=True, candidates=candidates)
    # When |Sigma| > 63: start with top 63 characters (minimizing escapes), then test swapping rarest chars for high-gain fragments
    vocab = ranked_chars[:63]
    # Also allow swapping any char with freq <= 3 if a W2 fragment saves strictly more bits than escaping that char
    base_vocab = list(vocab)
    # Keep it clean & reproducible: top 55 chars + greedy fill up to 63, or top 63 chars — pick whichever gives smaller total payload+dict bits!
    cand_a = list(ranked_chars[:63])
    cand_b = fill_dictionary_slots(programs, ranked_chars[:55], max_slots=63, token_bits=6, allow_escape=True, candidates=candidates)
    def score_v(v):
        tb = sum(optimal_parse_dp(s, v, 6, allow_escape=True)[1] for s in programs)
        return math.ceil(tb / 8) + serialize_dictionary_bytes(v)
    return cand_b if score_v(cand_b) < score_v(cand_a) else cand_a


def evaluate_regime(programs: list[str], vocab: list[str], token_bits: int, allow_escape: bool) -> dict:
    whole = set(programs)
    for tok in vocab:
        if not is_token_eligible(tok, programs, RULE_K, whole=whole, max_bytes=MAX_BYTES):
            raise ValueError(f"Ineligible token in bake-off vocab: {tok!r}")
    total_bits = 0
    total_presses = 0
    total_esc_bytes = 0
    for s in programs:
        _ops, bits, presses, esc_b = optimal_parse_dp(s, vocab, token_bits, allow_escape=allow_escape)
        total_bits += bits
        total_presses += presses
        total_esc_bytes += esc_b
    payload_bytes = math.ceil(total_bits / 8)
    dict_bytes = serialize_dictionary_bytes(vocab)
    return {
        "slotsUsed": len(vocab) + (1 if allow_escape else 0),
        "dictEntries": len(vocab),
        "multiEntries": sum(1 for t in vocab if len(t) > 1),
        "presses": total_presses,
        "escapeBytes": total_esc_bytes,
        "payloadBits": total_bits,
        "payloadBytes": payload_bytes,
        "dictBytes": dict_bytes,
        "totalPackageBytes": payload_bytes + dict_bytes,
        "byteExactVerified": True,
    }


def main() -> None:
    t_all = time.perf_counter()
    ind = json.loads((DIAG_DIR / "independent-eval" / "independent-instances.json").read_text(encoding="utf-8"))
    race = json.loads((HERE.parent / "capacity-race-v1" / "boundary-instances.json").read_text(encoding="utf-8"))

    corpora = []
    for cid, obj in ind["corpora"].items():
        corpora.append((f"IND-{cid}", obj.get("language", "?"), obj["programs"]))
    for cid, obj in race["corpora"].items():
        corpora.append((f"RACE-{cid}", obj.get("language", "?"), obj["programs"]))

    results = []
    for cid, lang, programs in corpora:
        raw_bytes = sum(len(s.encode("utf-8")) for s in programs)
        raw_chars = sum(len(s) for s in programs)
        alpha = sorted(set("".join(programs)))
        diag64 = diagnose_full_corpus(programs, k=RULE_K, budget=64, max_bytes=MAX_BYTES, measure_memory=False)
        cands = candidate_w2_fragments(programs, max_bytes=MAX_BYTES, limit=400)

        # 1. Literal UTF-8
        lit = {
            "slotsUsed": len(alpha),
            "presses": raw_chars,
            "escapeBytes": 0,
            "payloadBytes": raw_bytes,
            "dictBytes": 0,
            "totalPackageBytes": raw_bytes,
        }

        # 2. 6-bit no-escape (ONLY when BITS certifies FEASIBLE at K=64)
        bits6_noesc = None
        if diag64["status"] == "FEASIBLE":
            base64 = diag64["construction"]["dictionary"]
            # Fill any spare slots up to 64 with highest-saving W2 fragments
            vocab64 = fill_dictionary_slots(programs, base64, max_slots=64, token_bits=6, allow_escape=False, candidates=cands)
            bits6_noesc = evaluate_regime(programs, vocab64, token_bits=6, allow_escape=False)

        # 3. 6-bit + 1 escape (63 slots + escape)
        vocab6e = build_6bit_escape_vocab(programs, cands)
        bits6_esc = evaluate_regime(programs, vocab6e, token_bits=6, allow_escape=True)

        # 4. 7-bit (128 slots, 0 escapes)
        vocab7 = fill_dictionary_slots(programs, alpha, max_slots=128, token_bits=7, allow_escape=False, candidates=cands)
        bits7 = evaluate_regime(programs, vocab7, token_bits=7, allow_escape=False)

        # 5. 8-bit (256 slots, 0 escapes)
        vocab8 = fill_dictionary_slots(programs, alpha, max_slots=256, token_bits=8, allow_escape=False, candidates=cands)
        bits8 = evaluate_regime(programs, vocab8, token_bits=8, allow_escape=False)

        row = {
            "id": cid,
            "language": lang,
            "rawBytes": raw_bytes,
            "rawChars": raw_chars,
            "alphabetSize": len(alpha),
            "bitsK64Status": diag64["status"],
            "bitsK64LB": diag64["certifiedLowerBound"],
            "literalUtf8": lit,
            "bits6NoEscape": bits6_noesc,
            "bits6Escape": bits6_esc,
            "bits7_128": bits7,
            "bits8_256": bits8,
        }
        results.append(row)
        b6_str = f"{bits6_noesc['presses']:5d}p / {bits6_noesc['payloadBytes']:5d}+{bits6_noesc['dictBytes']:3d}={bits6_noesc['totalPackageBytes']:5d}B" if bits6_noesc else "   N/A (IMPOSSIBLE)     "
        print(
            f"{cid:9s} |S|={len(alpha):2d} K64={diag64['status']:10s} raw={raw_bytes:5d}B | "
            f"6b-noesc: {b6_str} | "
            f"6b+esc: {bits6_esc['presses']:5d}p {bits6_esc['totalPackageBytes']:5d}B (esc={bits6_esc['escapeBytes']:3d}B) | "
            f"7b: {bits7['presses']:5d}p {bits7['totalPackageBytes']:5d}B | "
            f"8b: {bits8['presses']:5d}p {bits8['totalPackageBytes']:5d}B",
            flush=True,
        )

    out_json = HERE / "bakeoff-results.json"
    out_json.write_text(json.dumps({"schema": "bits-lossless-bakeoff/v1", "rows": results}, indent=2) + "\n", encoding="utf-8")

    # Summarize honest winners across all 21 corpora and across the K=64 FEASIBLE subset
    feas_rows = [r for r in results if r["bits6NoEscape"] is not None]
    lines = [
        "# Phase 4 Lossless Encoding & Press-Count Bake-Off (21 Frozen Real Code Corpora)",
        "",
        "Strictly separate from capacity certification. Every file in every regime passed independent round-trip UTF-8 byte decode verification (`decode(encode(s)) == s`). **Press counts measure token/key operations only and do NOT claim human typing speed.**",
        "",
        "## 1. Per-Corpus Results (`presses` | `payload + dict = total bytes`)",
        "",
        "| ID | Lang | `|Sigma|` | Raw B | `K=64` | 6-bit No-Esc (`p` / `tot B`) | 6-bit+Esc (`p` / `tot B` / `esc B`) | 7-bit 128 (`p` / `tot B`) | 8-bit 256 (`p` / `tot B`) | Best Total B | Best Presses |",
        "| --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    win_total = defaultdict(int)
    win_press = defaultdict(int)
    feas_6b_beats_6e_total = 0
    feas_6b_beats_7b_total = 0
    feas_6b_beats_7b_payload = 0
    for r in results:
        cands_tot = [
            ("literal", r["literalUtf8"]["totalPackageBytes"]),
            ("6b+esc", r["bits6Escape"]["totalPackageBytes"]),
            ("7b-128", r["bits7_128"]["totalPackageBytes"]),
            ("8b-256", r["bits8_256"]["totalPackageBytes"]),
        ]
        cands_p = [
            ("literal", r["literalUtf8"]["presses"]),
            ("6b+esc", r["bits6Escape"]["presses"]),
            ("7b-128", r["bits7_128"]["presses"]),
            ("8b-256", r["bits8_256"]["presses"]),
        ]
        if r["bits6NoEscape"] is not None:
            cands_tot.append(("6b-noesc", r["bits6NoEscape"]["totalPackageBytes"]))
            cands_p.append(("6b-noesc", r["bits6NoEscape"]["presses"]))
            if r["bits6NoEscape"]["totalPackageBytes"] < r["bits6Escape"]["totalPackageBytes"]:
                feas_6b_beats_6e_total += 1
            if r["bits6NoEscape"]["totalPackageBytes"] < r["bits7_128"]["totalPackageBytes"]:
                feas_6b_beats_7b_total += 1
            if r["bits6NoEscape"]["payloadBytes"] < r["bits7_128"]["payloadBytes"]:
                feas_6b_beats_7b_payload += 1
        bt = min(cands_tot, key=lambda x: x[1])[0]
        bp = min(cands_p, key=lambda x: x[1])[0]
        win_total[bt] += 1
        win_press[bp] += 1
        b6 = f"{r['bits6NoEscape']['presses']} / {r['bits6NoEscape']['totalPackageBytes']}" if r["bits6NoEscape"] else "N/A"
        lines.append(
            f"| {r['id']} | {r['language']} | {r['alphabetSize']} | {r['rawBytes']} | `{r['bitsK64Status']}` | "
            f"{b6} | {r['bits6Escape']['presses']} / {r['bits6Escape']['totalPackageBytes']} / {r['bits6Escape']['escapeBytes']} | "
            f"{r['bits7_128']['presses']} / {r['bits7_128']['totalPackageBytes']} | "
            f"{r['bits8_256']['presses']} / {r['bits8_256']['totalPackageBytes']} | `{bt}` | `{bp}` |"
        )

    lines += [
        "",
        "## 2. Honest Summary",
        "",
        f"- **Total corpora evaluated:** `{len(results)}` (`{len(feas_rows)}` certified `FEASIBLE` at `K=64` without escapes, `{len(results) - len(feas_rows)}` `IMPOSSIBLE`).",
        f"- **Best total lossless package bytes (`payload + dict`) across all 21 corpora:** `{dict(win_total)}`.",
        f"- **Fewest presses across all 21 corpora:** `{dict(win_press)}`.",
        f"- **On the `{len(feas_rows)}` `K=64` `FEASIBLE` corpora:**",
        f"  - `6-bit no-escape` beat `6-bit + escape` on total bytes in `{feas_6b_beats_6e_total}/{len(feas_rows)}` corpora.",
        f"  - `6-bit no-escape` beat `7-bit (128)` on total bytes in `{feas_6b_beats_7b_total}/{len(feas_rows)}` corpora (and on payload bytes alone in `{feas_6b_beats_7b_payload}/{len(feas_rows)}`).",
        f"- **Elapsed wall time:** `{time.perf_counter() - t_all:.1f} s`.",
        "",
    ]
    (HERE / "RESULTS-BAKEOFF.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nDone in {time.perf_counter() - t_all:.1f}s! Winners totalB={dict(win_total)}, presses={dict(win_press)}")


if __name__ == "__main__":
    main()
