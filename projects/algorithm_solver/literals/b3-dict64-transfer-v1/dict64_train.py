"""Witnessed <=64-entry dictionary trainer, flat tiler, joint optimizer, and BPE-256 baseline.

Strict constraints enforced throughout:
- Witnessed eligibility: every multi-character entry (len >= 2) MUST occur in >= 2
  distinct fit programs. Single-character entries must occur in >= 1 fit program.
- Whole-answer prohibition: no entry may equal any fit program or exceed MAX_ENTRY_BYTES (48).
- Zero escapes on covered programs (exact shortest-path DP segmentation).
- Deterministic tie-breaking everywhere (no RNG).
"""
from __future__ import annotations

import collections
import re
import time
from typing import Any

import package_codec as pc

MAX_ENTRY_BYTES = 48
INF = 10**9

CORE_CHAR_SET = set("abcde0123456789!%&'()*+,-./:;<=?[]{}|")


class TrieNode:
    __slots__ = ("children", "entry_id")

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.entry_id: int = -1


def build_trie(vocab: list[str]) -> TrieNode:
    root = TrieNode()
    for idx, entry in enumerate(vocab):
        node = root
        for ch in entry:
            nxt = node.children.get(ch)
            if nxt is None:
                nxt = TrieNode()
                node.children[ch] = nxt
            node = nxt
        node.entry_id = idx
    return root


def dp_segment(text: str, trie: TrieNode, vocab: list[str]) -> list[int] | None:
    """Exact minimum-token zero-escape segmentation via backward DAG DP."""
    n = len(text)
    costs = [INF] * (n + 1)
    choice = [-1] * (n + 1)
    costs[n] = 0
    for i in range(n - 1, -1, -1):
        node = trie
        best_c = INF
        best_id = -1
        j = i
        while j < n:
            nxt = node.children.get(text[j])
            if nxt is None:
                break
            node = nxt
            j += 1
            eid = node.entry_id
            if eid >= 0:
                c = costs[j] + 1
                if c < best_c or (c == best_c and eid < best_id):
                    best_c = c
                    best_id = eid
        costs[i] = best_c
        choice[i] = best_id
    if costs[0] >= INF:
        return None
    out: list[int] = []
    pos = 0
    while pos < n:
        eid = choice[pos]
        out.append(eid)
        pos += len(vocab[eid])
    return out


def dp_segment_bits(text: str, trie: TrieNode, vocab: list[str], lengths: list[int]) -> list[int] | None:
    """Exact minimum-bit zero-escape segmentation for fixed canonical Huffman lengths."""
    n = len(text)
    costs = [INF] * (n + 1)
    toks = [INF] * (n + 1)
    choice = [-1] * (n + 1)
    costs[n] = 0
    toks[n] = 0
    for i in range(n - 1, -1, -1):
        node = trie
        bc = INF
        bt = INF
        bi = -1
        j = i
        while j < n:
            nxt = node.children.get(text[j])
            if nxt is None:
                break
            node = nxt
            j += 1
            eid = node.entry_id
            if eid >= 0:
                c = costs[j] + lengths[eid]
                t1 = toks[j] + 1
                if c < bc or (c == bc and (t1 < bt or (t1 == bt and eid < bi))):
                    bc = c
                    bt = t1
                    bi = eid
        costs[i] = bc
        toks[i] = bt
        choice[i] = bi
    if costs[0] >= INF:
        return None
    out: list[int] = []
    pos = 0
    while pos < n:
        eid = choice[pos]
        out.append(eid)
        pos += len(vocab[eid])
    return out


def fit_huffman_and_reparse(
    vocab: list[str],
    texts: dict[int, str],
    max_passes: int = 5,
) -> tuple[list[int], dict[int, list[int]], int]:
    """Fit canonical Huffman lengths + bit-optimal DP reparse (matches B3H1 exact bits)."""
    trie = build_trie(vocab)
    seqs = {pid: dp_segment(t, trie, vocab) for pid, t in texts.items()}
    assert all(s is not None for s in seqs.values())
    seqs_ok: dict[int, list[int]] = {pid: s for pid, s in seqs.items() if s is not None}
    n = len(vocab)

    def make_lengths(sq: dict[int, list[int]]) -> tuple[list[int], int]:
        counts = [0] * (n + 1)
        for s in sq.values():
            for tok in s:
                counts[tok] += 1
        counts[n] = len(sq)
        lens = pc.huffman_lengths(counts)
        pay = sum(c * l for c, l in zip(counts, lens))
        return lens, pay

    lengths, best_pay = make_lengths(seqs_ok)
    for _ in range(max_passes):
        s2_raw = {pid: dp_segment_bits(t, trie, vocab, lengths) for pid, t in texts.items()}
        assert all(s is not None for s in s2_raw.values())
        s2: dict[int, list[int]] = {pid: s for pid, s in s2_raw.items() if s is not None}
        l2, p2 = make_lengths(s2)
        if p2 < best_pay:
            lengths, best_pay, seqs_ok = l2, p2, s2
        else:
            break

    hdr_bytes = 5 + len(pc.encode_varint(n))
    for e in vocab:
        eb = len(e.encode("utf-8"))
        hdr_bytes += len(pc.encode_varint(eb)) + eb
    hdr_bytes += n + 1  # code lengths table
    stream_bytes = len(pc.encode_varint(len(seqs_ok))) + (best_pay + 7) // 8
    return lengths, seqs_ok, (hdr_bytes + stream_bytes) * 8


def varint_len(n: int) -> int:
    ln = 1
    while n >= 0x80:
        n >>= 7
        ln += 1
    return ln


def package_bits_fixed(vocab: list[str], seqs: dict[int, list[int]], width: int) -> int:
    header_bytes = 5 + varint_len(len(vocab))
    for e in vocab:
        eb = len(e.encode("utf-8"))
        header_bytes += varint_len(eb) + eb
    stream_bytes = varint_len(len(seqs))
    for seq in seqs.values():
        nt = len(seq)
        stream_bytes += varint_len(nt) + (nt * width + 7) // 8
    return (header_bytes + stream_bytes) * 8


def check_witnessed_eligibility(vocab: list[str], texts: dict[int, str]) -> tuple[bool, list[str]]:
    """Verify every multi-char entry occurs in >= 2 distinct fit programs, no whole programs."""
    whole = set(texts.values())
    values = list(texts.values())
    errors: list[str] = []
    if len(set(vocab)) != len(vocab):
        errors.append("duplicate entries")
    for idx, entry in enumerate(vocab):
        if not entry:
            errors.append(f"entry {idx} empty")
            continue
        if entry in whole:
            errors.append(f"entry {idx} ({entry!r}) is a whole program")
        if len(entry.encode("utf-8")) > MAX_ENTRY_BYTES:
            errors.append(f"entry {idx} exceeds {MAX_ENTRY_BYTES} bytes")
        support = sum(entry in t for t in values)
        if len(entry) >= 2 and support < 2:
            errors.append(f"multi-char entry {idx} ({entry!r}) support={support} < 2")
        elif len(entry) == 1 and support < 1:
            errors.append(f"single-char entry {idx} ({entry!r}) support=0")
    return len(errors) == 0, errors


def _reclaim_unused(vocab: list[str], seqs: dict[int, list[int]]) -> tuple[list[str], dict[int, list[int]]]:
    used = sorted({i for seq in seqs.values() for i in seq})
    if len(used) == len(vocab):
        return vocab, seqs
    remap = {old: new for new, old in enumerate(used)}
    new_vocab = [vocab[i] for i in used]
    new_seqs = {pid: [remap[i] for i in seq] for pid, seq in seqs.items()}
    return new_vocab, new_seqs


def mine_witnessed_spans(
    texts: dict[int, str],
    vocab: list[str],
    seqs: dict[int, list[int]],
    max_candidates: int = 80,
) -> list[str]:
    """Propose witnessed multi-char substrings (>=2 fit programs) directly from current DP parses."""
    present = set(vocab)
    whole = set(texts.values())
    counts: collections.Counter[str] = collections.Counter()
    owners: dict[str, set[int]] = collections.defaultdict(set)
    for pid, seq in seqs.items():
        pieces = [vocab[i] for i in seq]
        m = len(pieces)
        for i in range(m):
            acc = pieces[i]
            for span in range(2, 5):
                if i + span > m:
                    break
                acc += pieces[i + span - 1]
                if len(acc.encode("utf-8")) <= MAX_ENTRY_BYTES and acc not in whole:
                    counts[acc] += span - 1
                    owners[acc].add(pid)
    eligible = [s for s, ps in owners.items() if len(ps) >= 2 and len(s) >= 2 and s not in present]
    eligible.sort(key=lambda s: (-counts[s], len(s.encode("utf-8")), s))
    return eligible[:max_candidates]


def _seed_keyword_cover(texts: dict[int, str], budget: int) -> tuple[list[str], dict[int, list[int]], list[str]]:
    """Data-driven initialization: replace non-core letters with witnessed multi-char JS keywords/built-ins."""
    vals = list(texts.values())
    whole = set(vals)
    all_chars = sorted(set("".join(vals)))
    core_present = [c for c in all_chars if c in CORE_CHAR_SET]
    non_core = set(all_chars) - CORE_CHAR_SET

    # Mine maximal witnessed spans containing non-core characters (keywords, built-in names, spaces)
    token_pat = re.compile(
        r"String\.fromCharCode\(|Math\.floor\(|function solve\(|"
        r" (?:of|in) |(?:\.[A-Za-z]+|\b[A-Za-z]+)(?:\(| |;)?"
    )
    owners: dict[str, set[int]] = collections.defaultdict(set)
    occs: collections.Counter[str] = collections.Counter()
    for pid, t in texts.items():
        for m in token_pat.finditer(t):
            s = m.group(0)
            if len(s) >= 2 and len(s.encode("utf-8")) <= MAX_ENTRY_BYTES and s not in whole and any(c in non_core for c in s):
                owners[s].add(pid)
                occs[s] += 1
            if not s.startswith(" ") and not s.endswith(" "):
                bare = s.rstrip("(;")
                if len(bare) >= 2 and len(bare.encode("utf-8")) <= MAX_ENTRY_BYTES and bare not in whole and any(c in non_core for c in bare):
                    owners[bare].add(pid)
                    occs[bare] += 1
        # Explicitly check ` of ` and ` in ` with leading/trailing spaces so space is reclaimed cleanly
        for sp_kw in (" of ", " in "):
            if sp_kw in t and sp_kw not in whole:
                owners[sp_kw].add(pid)
                occs[sp_kw] += t.count(sp_kw)

    witnessed = [s for s, ps in owners.items() if len(ps) >= 2]
    witnessed.sort(key=lambda s: (-(occs[s] * (len(s) - 1)), -len(s), s))

    # Build a clean minimal cover: core single chars + witnessed multi-char tokens
    trial = list(core_present)
    for w in witnessed:
        if w not in trial:
            trial.append(w)
    # Include any non-core single char that couldn't be covered (safety fallback)
    trie = build_trie(trial)
    if any(dp_segment(t, trie, trial) is None for t in vals):
        for c in sorted(non_core):
            if c not in trial:
                trial.append(c)
        trie = build_trie(trial)

    seqs = {pid: dp_segment(t, trie, texts_vocab := trial) for pid, t in texts.items()}
    assert all(s is not None for s in seqs.values())
    seqs_ok = {pid: s for pid, s in seqs.items() if s is not None}
    vocab, seqs_ok = _reclaim_unused(trial, seqs_ok)

    # Prune redundant multi-char entries if > budget (preferring to keep non-core single chars eliminated)
    while len(vocab) > budget:
        best_drop = None
        for idx, e in enumerate(vocab):
            if len(e) == 1 and e in CORE_CHAR_SET:
                continue
            cand_v = [x for k, x in enumerate(vocab) if k != idx]
            ctrie = build_trie(cand_v)
            cseqs = {pid: dp_segment(t, ctrie, cand_v) for pid, t in texts.items()}
            if any(s is None for s in cseqs.values()):
                continue
            pv, ps = _reclaim_unused(cand_v, {p: s for p, s in cseqs.items() if s is not None})
            bits = package_bits_fixed(pv, ps, 6)
            if best_drop is None or (bits, len(pv)) < (best_drop[0], best_drop[1]):
                best_drop = (bits, len(pv), pv, ps)
        if best_drop is None:
            break
        _, _, vocab, seqs_ok = best_drop

    reclaimed = sorted(c for c in all_chars if c not in vocab)
    return vocab, seqs_ok, reclaimed


def _eval_add(
    texts: dict[int, str],
    vocab: list[str],
    cur_seqs: dict[int, list[int]],
    frag: str,
    width: int,
) -> tuple[int, list[str], dict[int, list[int]]]:
    ext = vocab + [frag]
    trie = build_trie(ext)
    nxt = dict(cur_seqs)
    for pid, t in texts.items():
        if frag in t:
            seg = dp_segment(t, trie, ext)
            assert seg is not None
            nxt[pid] = seg
    pv, ps = _reclaim_unused(ext, nxt)
    return package_bits_fixed(pv, ps, width), pv, ps


def train_witnessed_flat_tiler(
    texts: dict[int, str],
    budget: int = 64,
    width: int = 6,
    shortlist_size: int = 24,
    max_swap_rounds: int = 12,
    initial_vocab: list[str] | None = None,
    use_keyword_seed: bool = True,
) -> dict[str, Any]:
    """Train witnessed <=budget dictionary minimizing exact bits (fixed + Huffman reparse)."""
    t0 = time.monotonic()
    observed_chars = sorted(set("".join(texts.values())))
    reclaimed_singles: list[str] = []

    if initial_vocab is not None:
        vocab = list(initial_vocab)
        trie = build_trie(vocab)
        raw_seqs = {pid: dp_segment(t, trie, vocab) for pid, t in texts.items()}
        if any(s is None for s in raw_seqs.values()):
            return {
                "feasible_all": False,
                "reason": "initial_vocab_cannot_cover_all",
                "observed_alphabet": len(observed_chars),
                "budget": budget,
                "elapsed_seconds": time.monotonic() - t0,
            }
        seqs: dict[int, list[int]] = {pid: s for pid, s in raw_seqs.items() if s is not None}
        vocab, seqs = _reclaim_unused(vocab, seqs)
        reclaimed_singles = sorted(c for c in observed_chars if c not in vocab)
    elif use_keyword_seed and budget <= 64:
        vocab, seqs, reclaimed_singles = _seed_keyword_cover(texts, budget)
        if len(vocab) > budget:
            return {
                "feasible_all": False,
                "reason": f"seed_cover_{len(vocab)}_exceeds_budget_{budget}",
                "observed_alphabet": len(observed_chars),
                "budget": budget,
                "elapsed_seconds": time.monotonic() - t0,
            }
    else:
        if len(observed_chars) > budget:
            return {
                "feasible_all": False,
                "reason": f"observed_alphabet_{len(observed_chars)}_exceeds_budget_{budget}",
                "observed_alphabet": len(observed_chars),
                "budget": budget,
                "elapsed_seconds": time.monotonic() - t0,
            }
        vocab = list(observed_chars)
        trie = build_trie(vocab)
        seqs = {pid: dp_segment(t, trie, vocab) for pid, t in texts.items()}
        assert all(s is not None for s in seqs.values())
        seqs = {pid: s for pid, s in seqs.items() if s is not None}

    cur_bits = package_bits_fixed(vocab, seqs, width)
    trials = 0
    retired: set[str] = set()

    # Phase 1: Exact marginal bit-gain growth up to budget
    while len(vocab) < budget:
        cands = [c for c in mine_witnessed_spans(texts, vocab, seqs, max_candidates=100) if c not in retired]
        shortlist = cands[:shortlist_size]
        best = None
        for frag in shortlist:
            bits, pv, ps = _eval_add(texts, vocab, seqs, frag, width)
            trials += 1
            if len(pv) <= budget and bits < cur_bits:
                key = (bits, len(pv), frag)
                if best is None or key < (best[0], best[1], best[2]):
                    best = (bits, len(pv), frag, pv, ps)
        if best is None:
            break
        old_set = set(vocab)
        cur_bits, _, _, vocab, seqs = best
        for lost in old_set - set(vocab):
            if len(lost) > 1:
                retired.add(lost)
            else:
                reclaimed_singles.append(lost)

    # Phase 2: Exact remove/add swap refinement optimizing actual B3H1 Huffman bits (when budget<=64)
    swaps_accepted = 0
    if budget <= 64:
        _, h_seqs, cur_huff_bits = fit_huffman_and_reparse(vocab, texts, max_passes=2)
    else:
        cur_huff_bits = cur_bits

    for _round in range(max_swap_rounds):
        freq = collections.Counter(i for seq in seqs.values() for i in seq)
        multi_ids = [i for i, e in enumerate(vocab) if len(e) >= 2]
        multi_ids.sort(key=lambda i: (freq[i] * (len(vocab[i]) - 1), -len(vocab[i]), vocab[i]))
        removals = multi_ids[:10]
        additions = mine_witnessed_spans(texts, vocab, seqs, max_candidates=80)[:14]
        best_swap = None

        for rem_idx in removals:
            base_v = [e for k, e in enumerate(vocab) if k != rem_idx]
            btrie = build_trie(base_v)
            bseqs = {pid: dp_segment(t, btrie, base_v) for pid, t in texts.items()}
            trials += 1
            if all(s is not None for s in bseqs.values()):
                pv, ps = _reclaim_unused(base_v, {p: s for p, s in bseqs.items() if s is not None})
                if budget <= 64:
                    _, _, score_bits = fit_huffman_and_reparse(pv, texts, max_passes=2)
                else:
                    score_bits = package_bits_fixed(pv, ps, width)
                if score_bits < cur_huff_bits and (best_swap is None or score_bits < best_swap[0]):
                    best_swap = (score_bits, pv, ps)
            for add_frag in additions[:10]:
                if add_frag in base_v:
                    continue
                cand_v = base_v + [add_frag]
                ctrie = build_trie(cand_v)
                cseqs = {pid: dp_segment(t, ctrie, cand_v) for pid, t in texts.items()}
                trials += 1
                if any(s is None for s in cseqs.values()):
                    continue
                pv, ps = _reclaim_unused(cand_v, {p: s for p, s in cseqs.items() if s is not None})
                if len(pv) > budget:
                    continue
                if budget <= 64:
                    _, _, score_bits = fit_huffman_and_reparse(pv, texts, max_passes=2)
                else:
                    score_bits = package_bits_fixed(pv, ps, width)
                if score_bits < cur_huff_bits and (best_swap is None or score_bits < best_swap[0]):
                    best_swap = (score_bits, pv, ps)

        if best_swap is None:
            break
        cur_huff_bits, vocab, seqs = best_swap
        cur_bits = package_bits_fixed(vocab, seqs, width)
        swaps_accepted += 1

        while len(vocab) < budget:
            cands = mine_witnessed_spans(texts, vocab, seqs, max_candidates=60)[:14]
            best_add = None
            for frag in cands:
                bits_f, pv, ps = _eval_add(texts, vocab, seqs, frag, width)
                trials += 1
                if len(pv) <= budget:
                    if budget <= 64:
                        _, _, sb = fit_huffman_and_reparse(pv, texts, max_passes=2)
                    else:
                        sb = bits_f
                    if sb < cur_huff_bits and (best_add is None or sb < best_add[0]):
                        best_add = (sb, pv, ps)
            if best_add is None:
                break
            cur_huff_bits, vocab, seqs = best_add
            cur_bits = package_bits_fixed(vocab, seqs, width)

    # Canonical deterministic ID ordering: singles first, then multi-char by (-freq, len, lex)
    final_freq = collections.Counter(i for seq in seqs.values() for i in seq)
    order = sorted(
        range(len(vocab)),
        key=lambda i: (0 if len(vocab[i]) == 1 else 1, -final_freq[i], len(vocab[i]), vocab[i]),
    )
    vocab = [vocab[i] for i in order]
    trie = build_trie(vocab)
    seqs = {pid: dp_segment(t, trie, vocab) for pid, t in texts.items()}
    assert all(s is not None for s in seqs.values())
    seqs_ok = {pid: s for pid, s in seqs.items() if s is not None}

    ok_elig, elig_errs = check_witnessed_eligibility(vocab, texts)
    assert ok_elig, f"Witnessed eligibility violation: {elig_errs}"

    fixed_bits = package_bits_fixed(vocab, seqs_ok, width)
    huff_lengths, huff_seqs, huff_bits = fit_huffman_and_reparse(vocab, texts)

    return {
        "feasible_all": True,
        "budget": budget,
        "width": width,
        "entries": len(vocab),
        "single_char_entries": sum(len(e) == 1 for e in vocab),
        "multi_char_entries": sum(len(e) >= 2 for e in vocab),
        "observed_alphabet": len(observed_chars),
        "available_learned_slots_baseline": max(0, budget - len(observed_chars)),
        "reclaimed_single_chars": sorted(set(reclaimed_singles)),
        "vocab": vocab,
        "sequences": seqs_ok,
        "huffman_lengths": huff_lengths,
        "huffman_sequences": huff_seqs,
        "total_tokens": sum(len(s) for s in seqs_ok.values()),
        "huffman_total_tokens": sum(len(s) for s in huff_seqs.values()),
        "package_bits_fixed_excluding_decoder": fixed_bits,
        "package_bits_huffman_excluding_decoder": huff_bits,
        "trials": trials,
        "swaps_accepted": swaps_accepted,
        "elapsed_seconds": time.monotonic() - t0,
    }


def train_raw_max_coverage_64(texts: dict[int, str], budget: int = 64) -> dict[str, Any]:
    """Arm 1a diagnostic: max zero-escape coverage achievable on raw matched80 at budget=64."""
    t0 = time.monotonic()
    char_sets = {pid: set(t) for pid, t in texts.items()}
    all_chars = sorted(set().union(*char_sets.values()))
    chosen: set[str] = set()
    covered: list[int] = []
    remaining = set(texts.keys())
    while remaining:
        best_pid = min(remaining, key=lambda pid: (len(char_sets[pid] - chosen), len(texts[pid]), pid))
        need = char_sets[best_pid] - chosen
        if len(chosen) + len(need) > budget:
            break
        chosen |= need
        remaining.remove(best_pid)
        newly = [pid for pid in list(remaining) if char_sets[pid] <= chosen]
        for pid in newly:
            remaining.remove(pid)
        covered.append(best_pid)
        covered.extend(newly)
    covered = sorted(set(covered))
    uncovered = sorted(set(texts.keys()) - set(covered))
    return {
        "budget": budget,
        "observed_alphabet": len(all_chars),
        "available_learned_slots": max(0, budget - len(all_chars)),
        "covered_programs": len(covered),
        "total_programs": len(texts),
        "uncovered_programs": uncovered,
        "feasible_all": len(uncovered) == 0,
        "elapsed_seconds": time.monotonic() - t0,
    }


def train_joint_rewrite_dict64(
    candidates_by_id: dict[int, dict[str, str]],
    initial_choices: dict[int, str],
    initial_vocab: list[str],
    budget: int = 64,
    width: int = 6,
    max_outer_rounds: int = 4,
) -> dict[str, Any]:
    """Arm 3: Jointly optimize legal verified canonical rewrite choices + <=64 witnessed dictionary."""
    t0 = time.monotonic()
    choices = dict(initial_choices)
    vocab = list(initial_vocab)
    texts = {pid: candidates_by_id[pid][choices[pid]] for pid in sorted(choices)}
    huff_lengths, huff_seqs, best_huff_bits = fit_huffman_and_reparse(vocab, texts)
    trie = build_trie(vocab)
    seqs = {pid: dp_segment(t, trie, vocab) for pid, t in texts.items()}
    seqs_ok = {pid: s for pid, s in seqs.items() if s is not None}
    best_fixed_bits = package_bits_fixed(vocab, seqs_ok, width)

    history: list[dict[str, Any]] = []
    total_trials = 0

    for outer in range(max_outer_rounds):
        # 1. Source-choice step: pick minimum Huffman-bit zero-escape verified rewrite per problem!
        trie = build_trie(vocab)
        switches = 0
        proposed_choices = dict(choices)
        proposed_texts = dict(texts)
        for pid in sorted(candidates_by_id):
            cur_v = proposed_choices[pid]
            cur_seg = dp_segment_bits(candidates_by_id[pid][cur_v], trie, vocab, huff_lengths)
            assert cur_seg is not None
            cur_cost = sum(huff_lengths[t] for t in cur_seg)
            best_v = cur_v
            best_cost = cur_cost
            for vname, vcode in sorted(candidates_by_id[pid].items()):
                if vname == cur_v:
                    continue
                seg = dp_segment_bits(vcode, trie, vocab, huff_lengths)
                if seg is not None:
                    c = sum(huff_lengths[t] for t in seg)
                    if c < best_cost or (c == best_cost and len(vcode) < len(candidates_by_id[pid][best_v])):
                        best_v = vname
                        best_cost = c
            if best_v != cur_v:
                proposed_choices[pid] = best_v
                proposed_texts[pid] = candidates_by_id[pid][best_v]
                switches += 1

        # Verify witnessed eligibility after switches; prune ineligible entries if safe
        ok_elig, _ = check_witnessed_eligibility(vocab, proposed_texts)
        seed_v = list(vocab)
        if not ok_elig:
            whole = set(proposed_texts.values())
            vals = list(proposed_texts.values())
            kept = [e for e in vocab if e not in whole and (len(e) == 1 or sum(e in t for t in vals) >= 2)]
            ktrie = build_trie(kept)
            if all(dp_segment(t, ktrie, kept) is not None for t in proposed_texts.values()):
                seed_v = kept
            else:
                proposed_choices = dict(choices)
                proposed_texts = dict(texts)
                switches = 0

        # 2. Dictionary refinement on updated sources
        refined = train_witnessed_flat_tiler(
            proposed_texts,
            budget=budget,
            width=width,
            shortlist_size=24,
            max_swap_rounds=10,
            initial_vocab=seed_v,
        )
        total_trials += refined["trials"]
        new_huff = refined["package_bits_huffman_excluding_decoder"]
        new_fixed = refined["package_bits_fixed_excluding_decoder"]

        accepted = new_huff < best_huff_bits or (new_huff == best_huff_bits and new_fixed < best_fixed_bits)
        history.append({
            "round": outer,
            "source_switches": switches,
            "before_huff_bits": best_huff_bits,
            "after_huff_bits": new_huff,
            "before_fixed_bits": best_fixed_bits,
            "after_fixed_bits": new_fixed,
            "entries": refined["entries"],
            "accepted": accepted,
        })
        if accepted:
            choices = proposed_choices
            texts = proposed_texts
            vocab = refined["vocab"]
            seqs_ok = refined["sequences"]
            huff_lengths = refined["huffman_lengths"]
            huff_seqs = refined["huffman_sequences"]
            best_huff_bits = new_huff
            best_fixed_bits = new_fixed
        else:
            break

    ok_elig, elig_errs = check_witnessed_eligibility(vocab, texts)
    assert ok_elig, f"Arm 3 witnessed eligibility failed: {elig_errs}"

    return {
        "feasible_all": True,
        "budget": budget,
        "width": width,
        "entries": len(vocab),
        "single_char_entries": sum(len(e) == 1 for e in vocab),
        "multi_char_entries": sum(len(e) >= 2 for e in vocab),
        "vocab": vocab,
        "choices": choices,
        "texts": texts,
        "sequences": seqs_ok,
        "huffman_lengths": huff_lengths,
        "huffman_sequences": huff_seqs,
        "total_tokens": sum(len(s) for s in seqs_ok.values()),
        "huffman_total_tokens": sum(len(s) for s in huff_seqs.values()),
        "package_bits_fixed_excluding_decoder": best_fixed_bits,
        "package_bits_huffman_excluding_decoder": best_huff_bits,
        "rounds": history,
        "trials": total_trials,
        "elapsed_seconds": time.monotonic() - t0,
    }


def train_bpe_256(texts_bytes: list[bytes], max_vocab: int = 256) -> dict[str, Any]:
    """Frozen deterministic byte-level BPE up to `max_vocab` entries."""
    t0 = time.monotonic()
    base_alphabet = sorted(set(b"".join(texts_bytes)))
    vocab = [bytes([b]) for b in base_alphabet]
    sym_of = {b: i for i, b in enumerate(base_alphabet)}
    seqs = [[sym_of[b] for b in raw] for raw in texts_bytes]
    merges: list[tuple[int, int]] = []

    while len(vocab) < max_vocab:
        pair_counts: collections.Counter[tuple[int, int]] = collections.Counter()
        for seq in seqs:
            for a, b in zip(seq, seq[1:]):
                pair_counts[(a, b)] += 1
        if not pair_counts:
            break
        best_pair, best_cnt = min(pair_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        if best_cnt < 2:
            break
        new_id = len(vocab)
        vocab.append(vocab[best_pair[0]] + vocab[best_pair[1]])
        merges.append(best_pair)
        a0, b0 = best_pair
        new_seqs = []
        for seq in seqs:
            out: list[int] = []
            i = 0
            n = len(seq)
            while i < n:
                if i + 1 < n and seq[i] == a0 and seq[i + 1] == b0:
                    out.append(new_id)
                    i += 2
                else:
                    out.append(seq[i])
                    i += 1
            new_seqs.append(out)
        seqs = new_seqs

    encoded_seqs = [[(sym, None) for sym in seq] for seq in seqs]
    return {
        "base_alphabet": base_alphabet,
        "merges": merges,
        "vocab": vocab,
        "sequences": encoded_seqs,
        "total_tokens": sum(len(s) for s in seqs),
        "elapsed_seconds": time.monotonic() - t0,
    }


def apply_frozen_bpe(
    raw: bytes,
    base_alphabet: list[int],
    merges: list[tuple[int, int]],
) -> list[tuple[int, int | None]]:
    """Apply frozen BPE merge table to an unseen byte sequence with escape for unseen bytes."""
    sym_of = {b: i for i, b in enumerate(base_alphabet)}
    esc_sym = len(base_alphabet) + len(merges)
    seq: list[tuple[int, int | None]] = [
        (sym_of[b], None) if b in sym_of else (esc_sym, b) for b in raw
    ]
    for merge_idx, (a0, b0) in enumerate(merges):
        new_id = len(base_alphabet) + merge_idx
        out: list[tuple[int, int | None]] = []
        i = 0
        n = len(seq)
        while i < n:
            if i + 1 < n and seq[i][0] == a0 and seq[i + 1][0] == b0:
                out.append((new_id, None))
                i += 2
            else:
                out.append(seq[i])
                i += 1
        seq = out
    return seq
