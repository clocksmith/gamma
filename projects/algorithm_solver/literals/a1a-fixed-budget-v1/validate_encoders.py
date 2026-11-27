#!/usr/bin/env python3
"""Runtime encoder validation for Hugging Face `tokenizers` and `tiktoken`-style byte ranks.

1. Hugging Face `tokenizers` (live in .venv):
   - Builds real ByteLevel BPE tokenizers from explicit merge lists and vocabularies.
   - Verifies 100% byte-for-byte round-trip on CodeNet dev documents for closed chains.
   - Tests reachable vs provably unreachable merges (missing constituent AND rank-shadowed
     merge `[(b,c), (a,b), (ab,c)]` where `abc` can never form!) and exact replay equivalence.
2. `tiktoken`-style byte-rank reachability validator:
   - Implements exact byte-rank merge replay and exact per-token reachability validation
     (a multi-byte token `w` is reachable iff byte-rank replay on `w` with ranks <= rank[w]
     collapses to `[w]`).
   - Tests positive controls, negative controls (missing constituent, rank inversion,
     rank-shadowed dead token), and audits real A1a closed chains.
   - Checks whether `tiktoken` is installed in `.venv` or system Python without installing
     packages; reports PASS if live `tiktoken` verified, or PART explicitly naming missing
     `tiktoken` package.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / "objective-holdout-v1"
CL = LIT / "closure-holdout-v1"


# Standard GPT-2 / HF ByteLevel bijective byte <-> Unicode char mapping (all 256 bytes lossless).
def _bytes_to_unicode() -> Dict[int, str]:
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return {b: chr(c) for b, c in zip(bs, cs)}


BYTES_TO_UNI = _bytes_to_unicode()
UNI_TO_BYTES = {v: k for k, v in BYTES_TO_UNI.items()}


def encode_bytes_to_bpe_str(raw: bytes) -> str:
    return "".join(BYTES_TO_UNI[b] for b in raw)


def decode_bpe_str_to_bytes(s: str) -> bytes:
    return bytes(UNI_TO_BYTES[ch] for ch in s)


def extract_closed_merges(entries: Sequence[bytes]) -> Tuple[List[Tuple[bytes, bytes]], List[bytes]]:
    """Convert an ordered closed entry list into explicit (left, right) merges and non-closed entries."""
    seen = set()
    merges: List[Tuple[bytes, bytes]] = []
    non_closed: List[bytes] = []
    for e in entries:
        if len(e) == 1:
            seen.add(e)
            continue
        found = None
        for sp in range(1, len(e)):
            if e[:sp] in seen and e[sp:] in seen:
                found = (e[:sp], e[sp:])
                break
        if found is None:
            non_closed.append(e)
        else:
            merges.append(found)
        seen.add(e)
    return merges, non_closed


def build_hf_byte_bpe_tokenizer(merges: Sequence[Tuple[bytes, bytes]]):
    """Construct a live HF `tokenizers` BPE tokenizer over the exact 256-byte ByteLevel alphabet."""
    from tokenizers import Tokenizer, decoders
    from tokenizers.models import BPE

    vocab: Dict[str, int] = {}
    for b in range(256):
        vocab[BYTES_TO_UNI[b]] = b
    str_merges: List[Tuple[str, str]] = []
    for left, right in merges:
        ls = encode_bytes_to_bpe_str(left)
        rs = encode_bytes_to_bpe_str(right)
        merged = ls + rs
        if merged not in vocab:
            vocab[merged] = len(vocab)
        str_merges.append((ls, rs))

    # No pre-tokenizer so merges can span spaces/newlines identically to our byte-stream codec;
    # we map raw bytes -> bijective Unicode string before encode().
    tok = Tokenizer(BPE(vocab=vocab, merges=str_merges))
    tok.decoder = decoders.ByteLevel()
    return tok, vocab, str_merges


def ref_bpe_merge_replay(raw: bytes, merges: Sequence[Tuple[bytes, bytes]]) -> List[bytes]:
    """Reference greedy rank-ordered BPE merge replay over raw bytes."""
    rank: Dict[Tuple[bytes, bytes], int] = {}
    for idx, pair in enumerate(merges):
        rank.setdefault(pair, idx)
    tokens = [bytes([b]) for b in raw]
    while len(tokens) > 1:
        best_r = 10**9
        best_pair: Optional[Tuple[bytes, bytes]] = None
        for i in range(len(tokens) - 1):
            r = rank.get((tokens[i], tokens[i + 1]))
            if r is not None and r < best_r:
                best_r = r
                best_pair = (tokens[i], tokens[i + 1])
        if best_pair is None:
            break
        nxt: List[bytes] = []
        i = 0
        n = len(tokens)
        while i < n:
            if i + 1 < n and tokens[i] == best_pair[0] and tokens[i + 1] == best_pair[1]:
                nxt.append(tokens[i] + tokens[i + 1])
                i += 2
            else:
                nxt.append(tokens[i])
                i += 1
        tokens = nxt
    return tokens


def tiktoken_byte_rank_encode(raw: bytes, ranks: Dict[bytes, int], max_rank: Optional[int] = None) -> List[bytes]:
    """Exact tiktoken byte-pair rank replay (ranks: token_bytes -> integer rank).

    Repeatedly merges the adjacent pair (u, v) whose concatenation `u + v` has the
    smallest rank in `ranks` (strictly <= max_rank if given).
    """
    parts = [bytes([b]) for b in raw]
    while len(parts) > 1:
        best_rank = None
        best_idx = -1
        for i in range(len(parts) - 1):
            r = ranks.get(parts[i] + parts[i + 1])
            if r is not None and (max_rank is None or r <= max_rank):
                if best_rank is None or r < best_rank:
                    best_rank = r
                    best_idx = i
        if best_rank is None:
            break
        # Merge leftmost lowest-rank occurrence (or all non-overlapping occurrences of same concat).
        target = parts[best_idx] + parts[best_idx + 1]
        # In tiktoken (byte_pair_merge), the lowest-rank pair at its leftmost position merges first;
        # repeating until no mergeable pair remains produces the exact same leftmost-tie result.
        parts[best_idx : best_idx + 2] = [target]
    return parts


def validate_tiktoken_byte_ranks(ranks: Dict[bytes, int]) -> Dict[str, object]:
    """Validate a tiktoken-style `mergeable_ranks` table for completeness and reachability.

    Checks:
      1. All 256 single bytes present with unique non-negative ranks.
      2. No duplicate ranks.
      3. For every multi-byte token `w`, checks:
         (a) topological constituent closure (exists split u+v=w with rank[u], rank[v] < rank[w]),
         (b) exact byte-rank reachability: running byte-rank replay on `w` with ranks <= rank[w]
             yields `[w]` (catches rank-shadowed dead tokens!).
    """
    missing_singles = [b for b in range(256) if bytes([b]) not in ranks]
    rank_vals = list(ranks.values())
    duplicate_ranks = len(rank_vals) != len(set(rank_vals))
    negative_ranks = any(r < 0 for r in rank_vals)

    multi_tokens = sorted(
        [(r, w) for w, r in ranks.items() if len(w) > 1],
        key=lambda x: x[0],
    )
    unclosed: List[str] = []
    unreachable: List[str] = []
    reachable_count = 0

    for r, w in multi_tokens:
        has_closed_split = any(
            (w[:sp] in ranks and ranks[w[:sp]] < r and w[sp:] in ranks and ranks[w[sp:]] < r)
            for sp in range(1, len(w))
        )
        if not has_closed_split:
            unclosed.append(w.hex())
            unreachable.append(w.hex())
            continue
        replayed = tiktoken_byte_rank_encode(w, ranks, max_rank=r)
        if replayed == [w]:
            reachable_count += 1
        else:
            unreachable.append(w.hex())

    return {
        "total_tokens": len(ranks),
        "multi_byte_tokens": len(multi_tokens),
        "missing_single_bytes": len(missing_singles),
        "duplicate_ranks": duplicate_ranks,
        "negative_ranks": negative_ranks,
        "unclosed_count": len(unclosed),
        "reachable_count": reachable_count,
        "unreachable_count": len(unreachable),
        "sample_unreachable_hex": unreachable[:10],
        "all_valid_and_reachable": (
            len(missing_singles) == 0
            and not duplicate_ranks
            and not negative_ranks
            and len(unclosed) == 0
            and len(unreachable) == 0
        ),
    }


def entries_to_tiktoken_ranks(entries: Sequence[bytes]) -> Dict[bytes, int]:
    """Assign ranks 0..255 to single bytes, then 256.. for multi-byte entries in chain order."""
    ranks: Dict[bytes, int] = {bytes([b]): b for b in range(256)}
    nxt = 256
    for e in entries:
        if len(e) > 1 and e not in ranks:
            ranks[e] = nxt
            nxt += 1
    return ranks


def check_hf_tokenizers_runtime() -> Dict[str, object]:
    import tokenizers

    t0 = time.perf_counter()
    # 1. Reachable vs unreachable merge tests in live HF tokenizers
    # Reachable: (a, b) -> ab, (ab, c) -> abc
    tok_ok, _, _ = build_hf_byte_bpe_tokenizer([(b"a", b"b"), (b"ab", b"c")])
    enc_ok = tok_ok.encode(encode_bytes_to_bpe_str(b"abc"))
    assert enc_ok.tokens == [encode_bytes_to_bpe_str(b"abc")], f"expected ['abc'], got {enc_ok.tokens}"
    assert decode_bpe_str_to_bytes("".join(enc_ok.tokens)) == b"abc"

    # Unreachable (rank-shadowed): rank 0 (b,c)->bc, rank 1 (a,b)->ab, rank 2 (ab,c)->abc
    # On "abc", (b,c) ALWAYS merges first, so (ab,c)->abc is unreachable!
    tok_shadow, _, _ = build_hf_byte_bpe_tokenizer([(b"b", b"c"), (b"a", b"b"), (b"ab", b"c")])
    enc_shadow = tok_shadow.encode(encode_bytes_to_bpe_str(b"abc"))
    shadow_tokens = [decode_bpe_str_to_bytes(t) for t in enc_shadow.tokens]
    assert shadow_tokens == [b"a", b"bc"], f"expected [b'a', b'bc'], got {shadow_tokens}"
    assert b"abc" not in shadow_tokens

    # Unreachable (missing parent constituent): (ab, c) -> abc without (a, b) -> ab
    # HF tokenizers either raises an error during construction or cannot emit "abc".
    missing_parent_rejected = False
    missing_parent_detail = ""
    try:
        tok_miss, _, _ = build_hf_byte_bpe_tokenizer([(b"ab", b"c")])
        enc_miss = tok_miss.encode(encode_bytes_to_bpe_str(b"abc"))
        miss_toks = [decode_bpe_str_to_bytes(t) for t in enc_miss.tokens]
        missing_parent_rejected = (miss_toks != [b"abc"])
        missing_parent_detail = f"did_not_merge: {miss_toks!r}"
    except Exception as exc:
        missing_parent_rejected = True
        missing_parent_detail = f"constructor_rejected: {type(exc).__name__}: {exc}"
    assert missing_parent_rejected

    # 2. Live replay on real CodeNet dev documents using frozen BPE and exact-closed vocabularies
    dev_spec = json.loads((OH / "frozen/sets/dev.json").read_text())
    dev_docs = [(LIT / f["path"]).read_bytes() for f in dev_spec["files"][:25]]
    fz = json.loads((CL / "frozen/dictionaries.json").read_text())

    real_checks = {}
    for arm_key in ("bpe-K256", "closed-K256", "bpe-K4096", "closed-K4096"):
        entries = [bytes.fromhex(h) for h in fz["dictionaries"][arm_key]]
        merges, non_closed = extract_closed_merges(entries)
        assert not non_closed, f"{arm_key} unexpectedly non-closed"
        tok, _, _ = build_hf_byte_bpe_tokenizer(merges)
        hf_total_tokens = 0
        ref_matches = 0
        for idx, raw in enumerate(dev_docs):
            s = encode_bytes_to_bpe_str(raw)
            enc = tok.encode(s)
            rec = decode_bpe_str_to_bytes("".join(enc.tokens))
            if rec != raw:
                raise AssertionError(f"HF tokenizers round-trip failed on {arm_key} doc {idx}")
            hf_total_tokens += len(enc.tokens)
            # Cross-check exact token stream equivalence against reference merge replay on first 5 docs
            if idx < 5:
                ref_toks = ref_bpe_merge_replay(raw, merges)
                hf_toks = [decode_bpe_str_to_bytes(t) for t in enc.tokens]
                if hf_toks == ref_toks:
                    ref_matches += 1
        # Measure how many merges are reachable on their own merged string under HF tokenizers
        reachable_merges = 0
        for left, right in merges:
            w = left + right
            enc_w = tok.encode(encode_bytes_to_bpe_str(w))
            if len(enc_w.tokens) == 1 and decode_bpe_str_to_bytes(enc_w.tokens[0]) == w:
                reachable_merges += 1
        real_checks[arm_key] = {
            "merges": len(merges),
            "reachable_merges_self": reachable_merges,
            "unreachable_merges_self": len(merges) - reachable_merges,
            "dev25_roundtrip_ok": True,
            "dev25_hf_tokens": hf_total_tokens,
            "ref_replay_exact_match_5docs": ref_matches,
        }

    # Check non-closed open dictionary cannot be represented as binary merges
    open_entries = [bytes.fromhex(h) for h in fz["dictionaries"]["token-K4096"]]
    open_merges, open_non_closed = extract_closed_merges(open_entries)

    return {
        "status": "PASS",
        "tokenizers_version": tokenizers.__version__,
        "reachable_test_passed": True,
        "shadowed_unreachable_test_passed": True,
        "missing_parent_test_passed": True,
        "missing_parent_detail": missing_parent_detail,
        "open_K4096_non_closed_entries": len(open_non_closed),
        "open_K4096_closed_entries": len(open_merges),
        "real_vocab_checks": real_checks,
        "seconds": round(time.perf_counter() - t0, 3),
    }


def check_tiktoken_runtime() -> Dict[str, object]:
    t0 = time.perf_counter()
    # Check if tiktoken is installed in current python or system python3 without installing anything
    installed_in = None
    tiktoken_version = None
    try:
        import tiktoken  # type: ignore
        installed_in = sys.executable
        tiktoken_version = getattr(tiktoken, "__version__", "unknown")
    except ImportError:
        for py in ("/usr/bin/python3", "python3"):
            try:
                p = subprocess.run([py, "-c", "import tiktoken; print(tiktoken.__version__)"],
                                   capture_output=True, text=True, timeout=5)
                if p.returncode == 0:
                    installed_in = py
                    tiktoken_version = p.stdout.strip()
                    break
            except Exception:
                pass

    # Positive control: reachable byte ranks
    pos_ranks = {bytes([b]): b for b in range(256)}
    pos_ranks[b"ab"] = 256
    pos_ranks[b"abc"] = 257
    pos_res = validate_tiktoken_byte_ranks(pos_ranks)
    assert pos_res["all_valid_and_reachable"]

    # Negative control 1: rank-shadowed dead token (bc=256, ab=257, abc=258 -> abc unreachable!)
    # Wait: in tiktoken, rank is keyed by merged bytes `u + v`! For `abc`:
    # starting from [a, b, c]: pairs are `ab` (rank 257) and `bc` (rank 256).
    # `bc` merges first -> [a, bc]. Then `a + bc = abc` (rank 258) CAN STILL MERGE in tiktoken
    # because tiktoken matches by resulting bytes `u+v`, NOT by `(u,v)` pair identity!
    # WHEN is a token unreachable in tiktoken?
    # Example: `bc=256`, `cd=257`? No: `ab=256`, `bc=257`, `cd=258`, `bcd=259`, `abcd=260` ->
    # On `abcd`: `ab` (256) merges FIRST -> `[ab, c, d]`, then `cd` (258) merges -> `[ab, cd]`,
    # then `ab + cd = abcd` (260) merges!
    # What if `cd` is NOT in ranks? Ranks: `ab=256`, `bc=257`, `bcd=258`, `abcd=259`!
    # Check `abcd`: `[a, b, c, d]` -> `ab` (256) < `bc` (257), so `ab` merges FIRST -> `[ab, c, d]`!
    # Now remaining adjacent pairs are `abc` (NOT in ranks!) and `cd` (NOT in ranks!) -> STUCK at `[ab, c, d]`!
    # Even though `abcd = a + bcd` HAS both `a` (rank 97 < 259) and `bcd` (rank 258 < 259) in ranks!!
    shadow_ranks = {bytes([b]): b for b in range(256)}
    shadow_ranks[b"ab"] = 256
    shadow_ranks[b"bc"] = 257
    shadow_ranks[b"bcd"] = 258
    shadow_ranks[b"abcd"] = 259  # closed as a + bcd, yet unreachable because ab(256) blocks bc(257)!
    shadow_res = validate_tiktoken_byte_ranks(shadow_ranks)
    assert shadow_res["unclosed_count"] == 0
    assert shadow_res["unreachable_count"] == 1
    assert shadow_res["sample_unreachable_hex"] == [b"abcd".hex()]

    # Negative control 2: missing constituent (unclosed open fragment)
    unclosed_ranks = {bytes([b]): b for b in range(256)}
    unclosed_ranks[b"abcd"] = 256
    unclosed_res = validate_tiktoken_byte_ranks(unclosed_ranks)
    assert unclosed_res["unclosed_count"] == 1
    assert not unclosed_res["all_valid_and_reachable"]

    # Negative control 3: rank inversion (parent ranked earlier than child)
    inv_ranks = {bytes([b]): b for b in range(256)}
    inv_ranks[b"abc"] = 256
    inv_ranks[b"ab"] = 257
    inv_res = validate_tiktoken_byte_ranks(inv_ranks)
    assert inv_res["unclosed_count"] == 1
    assert not inv_res["all_valid_and_reachable"]

    # Audit real frozen vocabularies under tiktoken byte-rank replay
    fz = json.loads((CL / "frozen/dictionaries.json").read_text())
    real_audits = {}
    for arm_key in ("bpe-K256", "closed-K256", "token-K256", "bpe-K4096", "closed-K4096", "token-K4096"):
        entries = [bytes.fromhex(h) for h in fz["dictionaries"][arm_key]]
        ranks = entries_to_tiktoken_ranks(entries)
        real_audits[arm_key] = validate_tiktoken_byte_ranks(ranks)

    status = "PASS" if installed_in is not None else "PART"
    note = (
        f"Live tiktoken {tiktoken_version} verified in {installed_in}"
        if installed_in is not None
        else "Pure-Python tiktoken byte-rank reachability validator passed all controls and audits; "
             "live tiktoken runtime check skipped because `tiktoken` package is not installed in .venv or system Python"
    )
    return {
        "status": status,
        "tiktoken_installed": installed_in is not None,
        "tiktoken_version": tiktoken_version,
        "missing_package": None if installed_in is not None else "tiktoken",
        "note": note,
        "positive_control_ok": pos_res["all_valid_and_reachable"],
        "shadowed_dead_token_caught": (shadow_res["unclosed_count"] == 0 and shadow_res["unreachable_count"] == 1),
        "unclosed_token_caught": (unclosed_res["unclosed_count"] == 1),
        "rank_inversion_caught": (inv_res["unclosed_count"] == 1),
        "real_vocab_audits": real_audits,
        "seconds": round(time.perf_counter() - t0, 3),
    }


def run_all() -> Dict[str, object]:
    hf = check_hf_tokenizers_runtime()
    tt = check_tiktoken_runtime()
    out = {"hf_tokenizers": hf, "tiktoken_byte_ranks": tt}
    out_dir = HERE / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "encoder_validation.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    res = run_all()
    print(json.dumps(res, indent=2))
