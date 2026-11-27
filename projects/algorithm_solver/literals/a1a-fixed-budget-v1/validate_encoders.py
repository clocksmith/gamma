#!/usr/bin/env python3
"""Runtime encoder validation for Hugging Face `tokenizers` and `tiktoken` byte ranks.

1. Hugging Face `tokenizers` (live in .venv):
   - Builds real ByteLevel BPE tokenizers from explicit merge lists and vocabularies.
   - Verifies 100% byte-for-byte round-trip on CodeNet dev documents for closed chains.
   - Tests reachable vs provably unreachable merges (missing constituent AND rank-shadowed
     merge `[(b,c), (a,b), (ab,c)]` where `abc` can never form!) and exact replay equivalence.
2. `tiktoken` byte-rank reachability validator & live `tiktoken.Encoding` runtime validation:
   - Implements exact byte-rank merge replay and exact per-token reachability validation
     (a multi-byte token `w` is reachable under `byte_pair_merge` iff byte-rank replay on `w`
     with ranks <= rank[w] collapses to `[w]`).
   - Auto-probes `--tiktoken-python` / `TIKTOKEN_PYTHON` env var / current interpreter /
     `/Users/xyz/deco/gamma/.venv-tiktoken/bin/python` / system Python.
   - When a Python with `tiktoken` is available, executes real live `tiktoken.Encoding`
     validation: encode/decode byte-exact round-trip on CodeNet `dev`, exact token-stream
     parity with the pure-Python validator, and live rank-shadowing reachability verification
     on synthetic controls and frozen `closure-holdout-v1` vocabularies (`bpe-K256/K4096`,
     `closed-K256/K4096`). Returns `PASS` when live `tiktoken` passes, or graceful `PART`
     only if run on a host without a `tiktoken`-equipped environment.

Read-only check functions (`check_hf_tokenizers_runtime`, `check_tiktoken_runtime`) write
no files. Running this module as a script writes `out/encoder_validation.json` unless
`--no-write` is passed.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / "objective-holdout-v1"
CL = LIT / "closure-holdout-v1"
DEFAULT_TIKTOKEN_VENV_PY = Path("/Users/xyz/deco/gamma/.venv-tiktoken/bin/python")


def _bytes_to_unicode() -> Dict[int, str]:
    bs = (
        list(range(ord("!"), ord("~") + 1))
        + list(range(ord("¡"), ord("¬") + 1))
        + list(range(ord("®"), ord("ÿ") + 1))
    )
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
    """Exact tiktoken `byte_pair_merge` rank replay (ranks: token_bytes -> integer rank).

    Repeatedly merges the leftmost adjacent pair (u, v) whose concatenation `u + v` has the
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
        parts[best_idx : best_idx + 2] = [parts[best_idx] + parts[best_idx + 1]]
    return parts


def validate_tiktoken_byte_ranks(ranks: Dict[bytes, int]) -> Dict[str, object]:
    """Validate a tiktoken-style `mergeable_ranks` table for completeness and reachability."""
    missing_singles = [b for b in range(256) if bytes([b]) not in ranks]
    rank_vals = list(ranks.values())
    duplicate_ranks = len(rank_vals) != len(set(rank_vals))
    negative_ranks = any(r < 0 for r in rank_vals)

    multi_tokens = sorted(
        [(r, w) for w, r in ranks.items() if len(w) > 1],
        key=lambda x: x[0],
    )
    unclosed: List[str] = []
    prefix_unreachable: List[str] = []
    full_table_unreachable: List[str] = []
    full_table_utf8_unreachable = 0
    reachable_prefix = 0
    reachable_full = 0

    for r, w in multi_tokens:
        has_closed_split = any(
            (w[:sp] in ranks and ranks[w[:sp]] < r and w[sp:] in ranks and ranks[w[sp:]] < r)
            for sp in range(1, len(w))
        )
        if not has_closed_split:
            unclosed.append(w.hex())
            prefix_unreachable.append(w.hex())
        else:
            if tiktoken_byte_rank_encode(w, ranks, max_rank=r) == [w]:
                reachable_prefix += 1
            else:
                prefix_unreachable.append(w.hex())

        if tiktoken_byte_rank_encode(w, ranks, max_rank=None) == [w]:
            reachable_full += 1
        else:
            full_table_unreachable.append(w.hex())
            try:
                w.decode("utf-8", errors="strict")
                full_table_utf8_unreachable += 1
            except UnicodeDecodeError:
                pass

    return {
        "total_tokens": len(ranks),
        "multi_byte_tokens": len(multi_tokens),
        "missing_single_bytes": len(missing_singles),
        "duplicate_ranks": duplicate_ranks,
        "negative_ranks": negative_ranks,
        "unclosed_count": len(unclosed),
        "reachable_count": reachable_full,
        "unreachable_count": len(full_table_unreachable),
        "utf8_unreachable_count": full_table_utf8_unreachable,
        "prefix_monotone_reachable_count": reachable_prefix,
        "prefix_monotone_unreachable_count": len(prefix_unreachable),
        "sample_unreachable_hex": full_table_unreachable[:10],
        "all_valid_and_reachable": (
            len(missing_singles) == 0
            and not duplicate_ranks
            and not negative_ranks
            and len(unclosed) == 0
            and len(full_table_unreachable) == 0
            and len(prefix_unreachable) == 0
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
    tok_ok, _, _ = build_hf_byte_bpe_tokenizer([(b"a", b"b"), (b"ab", b"c")])
    enc_ok = tok_ok.encode(encode_bytes_to_bpe_str(b"abc"))
    assert enc_ok.tokens == [encode_bytes_to_bpe_str(b"abc")], f"expected ['abc'], got {enc_ok.tokens}"
    assert decode_bpe_str_to_bytes("".join(enc_ok.tokens)) == b"abc"

    tok_shadow, _, _ = build_hf_byte_bpe_tokenizer([(b"b", b"c"), (b"a", b"b"), (b"ab", b"c")])
    enc_shadow = tok_shadow.encode(encode_bytes_to_bpe_str(b"abc"))
    shadow_tokens = [decode_bpe_str_to_bytes(t) for t in enc_shadow.tokens]
    assert shadow_tokens == [b"a", b"bc"], f"expected [b'a', b'bc'], got {shadow_tokens}"
    assert b"abc" not in shadow_tokens

    missing_parent_rejected = False
    missing_parent_detail = ""
    try:
        tok_miss, _, _ = build_hf_byte_bpe_tokenizer([(b"ab", b"c")])
        enc_miss = tok_miss.encode(encode_bytes_to_bpe_str(b"abc"))
        miss_toks = [decode_bpe_str_to_bytes(t) for t in enc_miss.tokens]
        missing_parent_rejected = miss_toks != [b"abc"]
        missing_parent_detail = f"did_not_merge: {miss_toks!r}"
    except Exception as exc:
        missing_parent_rejected = True
        missing_parent_detail = f"constructor_rejected: {type(exc).__name__}: {exc}"
    assert missing_parent_rejected

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
            if idx < 5:
                ref_toks = ref_bpe_merge_replay(raw, merges)
                hf_toks = [decode_bpe_str_to_bytes(t) for t in enc.tokens]
                if hf_toks == ref_toks:
                    ref_matches += 1
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


def _discover_tiktoken_python(explicit_python: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Probe candidate Python interpreters for an installed `tiktoken` package."""
    candidates: List[str] = []
    if explicit_python:
        candidates.append(explicit_python)
    env_py = os.environ.get("TIKTOKEN_PYTHON")
    if env_py:
        candidates.append(env_py)
    candidates.append(sys.executable)
    if DEFAULT_TIKTOKEN_VENV_PY.exists():
        candidates.append(str(DEFAULT_TIKTOKEN_VENV_PY))
    # Also check sibling .venv-tiktoken relative to gamma repo root if worktree is nested
    rel_venv = HERE.parents[3] / ".venv-tiktoken" / "bin" / "python"
    if rel_venv.exists():
        candidates.append(str(rel_venv))
    candidates.extend(["/usr/bin/python3", "python3"])

    seen = set()
    for py in candidates:
        if not py or py in seen:
            continue
        seen.add(py)
        try:
            p = subprocess.run(
                [py, "-c", "import tiktoken; print(tiktoken.__version__)"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if p.returncode == 0 and p.stdout.strip():
                return py, p.stdout.strip()
        except Exception:
            continue
    return None, None


_LIVE_TIKTOKEN_WORKER = r"""
import json, sys
from pathlib import Path
import tiktoken

payload = json.loads(sys.stdin.read())
lit = Path(payload["lit"])
oh = Path(payload["oh"])
cl = Path(payload["cl"])

# 1. Synthetic positive control (ab=256, abc=257) using NUL sentinel to force Rust byte_pair_merge
pos_ranks = {bytes([b]): b for b in range(256)}
pos_ranks[b"ab"] = 256
pos_ranks[b"abc"] = 257
enc_pos = tiktoken.Encoding(name="pos", pat_str=r"(?s).+", mergeable_ranks=pos_ranks, special_tokens={})
pos_ids = enc_pos.encode("\x00abc\x00")
assert pos_ids == [0, 257, 0], f"pos live fail: {pos_ids}"
assert enc_pos.decode_bytes(pos_ids) == b"\x00abc\x00"

# 2. Synthetic rank-shadowing control (ab=256, bc=257, bcd=258, abcd=259)
#    Proves tiktoken whole-piece fast-path emits [259] on isolated "abcd", while Rust byte_pair_merge
#    inside "\x00abcd\x00" is blocked by ab(256) and produces [0, 256, 99, 100, 0] (NEVER 259!).
sh_ranks = {bytes([b]): b for b in range(256)}
sh_ranks[b"ab"] = 256
sh_ranks[b"bc"] = 257
sh_ranks[b"bcd"] = 258
sh_ranks[b"abcd"] = 259
enc_sh = tiktoken.Encoding(name="shadow", pat_str=r"(?s).+", mergeable_ranks=sh_ranks, special_tokens={})
assert enc_sh.encode("abcd") == [259]
sh_ids = enc_sh.encode("\x00abcd\x00")
assert sh_ids == [0, 256, 99, 100, 0], f"shadow live fail: {sh_ids}"
assert 259 not in sh_ids
assert enc_sh.decode_bytes(sh_ids) == b"\x00abcd\x00"

# 3. Live tiktoken.Encoding validation against frozen closure-holdout-v1 vocabularies and CodeNet dev
dev_spec = json.loads((oh / "frozen/sets/dev.json").read_text())
dev_docs = [(lit / f["path"]).read_bytes() for f in dev_spec["files"][:25]]
utf8_docs = []
for raw in dev_docs:
    try:
        utf8_docs.append((raw, raw.decode("utf-8", errors="strict")))
    except UnicodeDecodeError:
        pass

fz = json.loads((cl / "frozen/dictionaries.json").read_text())
expected_parity = payload["expected_dev5_tokens"]
live_vocabs = {}

for arm_key in ("bpe-K256", "closed-K256", "bpe-K4096", "closed-K4096"):
    entries = [bytes.fromhex(h) for h in fz["dictionaries"][arm_key]]
    ranks = {bytes([b]): b for b in range(256)}
    nxt = 256
    for e in entries:
        if len(e) > 1 and e not in ranks:
            ranks[e] = nxt
            nxt += 1
    assert all(0 not in t for t in ranks if len(t) > 1), "unexpected NUL in multi-byte token"
    enc = tiktoken.Encoding(name=arm_key, pat_str=r"(?s).+", mergeable_ranks=ranks, special_tokens={})

    # 3a. Round-trip byte-for-byte on all UTF-8 dev docs + exact token-stream parity with pure-Python replay
    total_toks = 0
    parity_matches = 0
    for idx, (raw, txt) in enumerate(utf8_docs):
        ids = enc.encode(txt)
        dec = enc.decode_bytes(ids)
        assert dec == raw, f"live tiktoken roundtrip failed on {arm_key} doc {idx}"
        total_toks += len(ids)
        if idx < len(expected_parity[arm_key]):
            live_toks_hex = [enc.decode_single_token_bytes(i).hex() for i in ids]
            if live_toks_hex == expected_parity[arm_key][idx]:
                parity_matches += 1

    # 3b. Live byte_pair_merge reachability on every UTF-8 multi-byte token via "\x00" + token + "\x00"
    utf8_multi = 0
    live_reachable = 0
    live_shadowed = 0
    sample_shadowed = []
    for e in entries:
        if len(e) <= 1:
            continue
        try:
            s = e.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            continue
        utf8_multi += 1
        tok_id = ranks[e]
        ids = enc.encode("\x00" + s + "\x00")
        if ids == [0, tok_id, 0]:
            live_reachable += 1
        else:
            live_shadowed += 1
            if len(sample_shadowed) < 6:
                sample_shadowed.append(e.hex())

    live_vocabs[arm_key] = {
        "utf8_dev_docs_roundtrip_ok": len(utf8_docs),
        "dev_utf8_total_tokens": total_toks,
        "pure_python_parity_5docs": f"{parity_matches}/{len(expected_parity[arm_key])}",
        "pure_python_parity_all_match": parity_matches == len(expected_parity[arm_key]),
        "utf8_multi_tokens_checked": utf8_multi,
        "live_byte_pair_merge_reachable": live_reachable,
        "live_byte_pair_merge_shadowed": live_shadowed,
        "sample_live_shadowed_hex": sample_shadowed,
    }

print(json.dumps({
    "tiktoken_version": tiktoken.__version__,
    "positive_live_ok": True,
    "shadowing_live_ok": True,
    "shadowing_whole_piece_short_circuit_observed": True,
    "utf8_dev_docs_checked": len(utf8_docs),
    "live_vocabs": live_vocabs,
}))
"""


def check_tiktoken_runtime(tiktoken_python: Optional[str] = None) -> Dict[str, object]:
    t0 = time.perf_counter()

    # Pure-Python byte-rank reachability validator controls
    pos_ranks = {bytes([b]): b for b in range(256)}
    pos_ranks[b"ab"] = 256
    pos_ranks[b"abc"] = 257
    pos_res = validate_tiktoken_byte_ranks(pos_ranks)
    assert pos_res["all_valid_and_reachable"]

    shadow_ranks = {bytes([b]): b for b in range(256)}
    shadow_ranks[b"ab"] = 256
    shadow_ranks[b"bc"] = 257
    shadow_ranks[b"bcd"] = 258
    shadow_ranks[b"abcd"] = 259
    shadow_res = validate_tiktoken_byte_ranks(shadow_ranks)
    assert shadow_res["unclosed_count"] == 0
    assert shadow_res["unreachable_count"] == 1
    assert shadow_res["sample_unreachable_hex"] == [b"abcd".hex()]

    unclosed_ranks = {bytes([b]): b for b in range(256)}
    unclosed_ranks[b"abcd"] = 256
    unclosed_res = validate_tiktoken_byte_ranks(unclosed_ranks)
    assert unclosed_res["unclosed_count"] == 1
    assert not unclosed_res["all_valid_and_reachable"]

    inv_ranks = {bytes([b]): b for b in range(256)}
    inv_ranks[b"abc"] = 256
    inv_ranks[b"ab"] = 257
    inv_res = validate_tiktoken_byte_ranks(inv_ranks)
    assert inv_res["unclosed_count"] == 1
    assert not inv_res["all_valid_and_reachable"]

    # Audit real frozen vocabularies with pure-Python byte-rank validator
    fz = json.loads((CL / "frozen/dictionaries.json").read_text())
    real_audits = {}
    ranks_map: Dict[str, Dict[bytes, int]] = {}
    for arm_key in ("bpe-K256", "closed-K256", "token-K256", "bpe-K4096", "closed-K4096", "token-K4096"):
        entries = [bytes.fromhex(h) for h in fz["dictionaries"][arm_key]]
        ranks = entries_to_tiktoken_ranks(entries)
        ranks_map[arm_key] = ranks
        real_audits[arm_key] = validate_tiktoken_byte_ranks(ranks)

    # Discover live tiktoken runtime
    found_py, tiktoken_version = _discover_tiktoken_python(tiktoken_python)
    live_receipt: Optional[Dict[str, object]] = None
    if found_py is not None:
        dev_spec = json.loads((OH / "frozen/sets/dev.json").read_text())
        dev_docs = [(LIT / f["path"]).read_bytes() for f in dev_spec["files"][:25]]
        utf8_first5 = []
        for raw in dev_docs:
            try:
                raw.decode("utf-8", errors="strict")
                utf8_first5.append(raw)
                if len(utf8_first5) == 5:
                    break
            except UnicodeDecodeError:
                pass
        expected_dev5 = {
            arm_key: [
                [t.hex() for t in tiktoken_byte_rank_encode(raw, ranks_map[arm_key])]
                for raw in utf8_first5
            ]
            for arm_key in ("bpe-K256", "closed-K256", "bpe-K4096", "closed-K4096")
        }
        worker_in = json.dumps({
            "lit": str(LIT),
            "oh": str(OH),
            "cl": str(CL),
            "expected_dev5_tokens": expected_dev5,
        })
        proc = subprocess.run(
            [found_py, "-c", _LIVE_TIKTOKEN_WORKER],
            input=worker_in,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            raise AssertionError(f"live tiktoken validation failed in {found_py}: {proc.stderr.strip()}")
        live_receipt = json.loads(proc.stdout)
        # Assert exact token-stream parity and exact live vs pure-Python shadowing count equality!
        for arm_key, vres in live_receipt["live_vocabs"].items():
            assert vres["pure_python_parity_all_match"], f"live tiktoken parity mismatch on {arm_key}"
            want_utf8_shad = real_audits[arm_key]["utf8_unreachable_count"]
            got_live_shad = vres["live_byte_pair_merge_shadowed"]
            assert got_live_shad == want_utf8_shad, (
                f"live tiktoken shadowed count mismatch on {arm_key}: live={got_live_shad} vs py={want_utf8_shad}"
            )
        assert live_receipt["live_vocabs"]["bpe-K256"]["live_byte_pair_merge_shadowed"] == 0
        assert live_receipt["live_vocabs"]["bpe-K4096"]["live_byte_pair_merge_shadowed"] == 0
        assert live_receipt["live_vocabs"]["closed-K256"]["live_byte_pair_merge_shadowed"] == 2
        assert live_receipt["live_vocabs"]["closed-K4096"]["live_byte_pair_merge_shadowed"] == 236

    status = "PASS" if live_receipt is not None else "PART"
    note = (
        f"Live tiktoken {tiktoken_version} verified via {found_py}: encode/decode byte-exact round-trip on "
        f"{live_receipt['utf8_dev_docs_checked']} CodeNet dev docs, 100% token-stream parity with pure-Python "
        f"validator, and live byte_pair_merge rank-shadowing verified on synthetic + frozen vocabularies."
        if live_receipt is not None
        else "Pure-Python tiktoken byte-rank reachability validator passed all controls and audits; "
             "live tiktoken runtime check skipped because `tiktoken` package is not installed in .venv, "
             "/Users/xyz/deco/gamma/.venv-tiktoken, or system Python"
    )
    return {
        "status": status,
        "tiktoken_installed": live_receipt is not None,
        "tiktoken_python": found_py,
        "tiktoken_version": tiktoken_version,
        "missing_package": None if live_receipt is not None else "tiktoken",
        "note": note,
        "positive_control_ok": pos_res["all_valid_and_reachable"],
        "shadowed_dead_token_caught": (shadow_res["unclosed_count"] == 0 and shadow_res["unreachable_count"] == 1),
        "unclosed_token_caught": (unclosed_res["unclosed_count"] == 1),
        "rank_inversion_caught": (inv_res["unclosed_count"] == 1),
        "real_vocab_audits": real_audits,
        "live_tiktoken_receipt": live_receipt,
        "seconds": round(time.perf_counter() - t0, 3),
    }


def run_all(tiktoken_python: Optional[str] = None, write_output: bool = True) -> Dict[str, object]:
    hf = check_hf_tokenizers_runtime()
    tt = check_tiktoken_runtime(tiktoken_python=tiktoken_python)
    out = {"hf_tokenizers": hf, "tiktoken_byte_ranks": tt}
    if write_output:
        out_dir = HERE / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "encoder_validation.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate HF tokenizers and tiktoken byte-rank encoders")
    ap.add_argument("--tiktoken-python", default=None, help="optional path to Python with tiktoken installed")
    ap.add_argument("--no-write", action="store_true", help="do not write out/encoder_validation.json")
    args = ap.parse_args()
    res = run_all(tiktoken_python=args.tiktoken_python, write_output=not args.no_write)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
