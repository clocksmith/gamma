#!/usr/bin/env python3
"""Exact canonical Huffman coding, byte-optimal DP segmentation, KL/JS Design-B
decomposition, and real bitstream encode/decode benchmarking for BITS Rung 3/4.

Zero external dependencies (Python 3 standard library only).
"""
import heapq
import math
import time
from collections import Counter

ROUTING_BYTES = 4
EOF_SYMBOL = b'\x00__BITS_EOF__'


def insert_trie(root, entry):
    node = root
    for byte in entry:
        nxt = node.get(byte)
        if nxt is None:
            nxt = {}
            node[byte] = nxt
        node = nxt
    node[-1] = entry


def build_trie(entries):
    root = {}
    for entry in entries:
        insert_trie(root, entry)
    return root


def canonical_huffman_lengths(counts):
    """Exact optimal prefix-code bit lengths for all symbols with count > 0.

    Returns dict[symbol -> bit_length] and verifies the exact Kraft inequality.
    """
    items = [(c, i, sym) for i, (sym, c) in enumerate(sorted(counts.items())) if c > 0]
    if not items:
        return {}
    if len(items) == 1:
        return {items[0][2]: 1}
    heap = [(c, i, (sym,)) for c, i, sym in items]
    heapq.heapify(heap)
    next_id = len(items)
    while len(heap) > 1:
        c1, _, t1 = heapq.heappop(heap)
        c2, _, t2 = heapq.heappop(heap)
        heapq.heappush(heap, (c1 + c2, next_id, (t1, t2)))
        next_id += 1
    lengths = {}

    def walk(node, depth):
        if len(node) == 1:
            lengths[node[0]] = depth
            return
        walk(node[0], depth + 1)
        walk(node[1], depth + 1)

    walk(heap[0][2], 0)
    max_len = max(lengths.values())
    kraft_num = sum(1 << (max_len - l) for l in lengths.values())
    if kraft_num > (1 << max_len):
        raise AssertionError('Kraft inequality violated')
    return lengths


def total_huffman_bits(counts, lengths):
    return sum(c * lengths[sym] for sym, c in counts.items() if c > 0)


def assign_canonical_codes(lengths):
    """Assigns standard canonical Huffman codes (code_int, bit_len) per symbol."""
    ordered = sorted(lengths.items(), key=lambda kv: (kv[1], kv[0]))
    codes = {}
    code = 0
    prev_len = 0
    for sym, bit_len in ordered:
        code <<= (bit_len - prev_len)
        codes[sym] = (code, bit_len)
        code += 1
        prev_len = bit_len
    return codes


def build_decode_tree(codes):
    root = {}
    for sym, (code, bit_len) in codes.items():
        node = root
        for shift in range(bit_len - 1, -1, -1):
            bit = (code >> shift) & 1
            nxt = node.get(bit)
            if nxt is None:
                nxt = {}
                node[bit] = nxt
            node = nxt
        node['sym'] = sym
    return root


def encode_bitstream(doc_pieces, codes):
    """Packs canonical Huffman codewords + EOF per document into an exact byte stream."""
    out = bytearray()
    acc = 0
    nbits = 0
    eof_code, eof_len = codes[EOF_SYMBOL]
    for pieces in doc_pieces:
        for piece in pieces:
            code, bit_len = codes[piece]
            acc = (acc << bit_len) | code
            nbits += bit_len
            while nbits >= 8:
                nbits -= 8
                out.append((acc >> nbits) & 0xFF)
                acc &= (1 << nbits) - 1
        acc = (acc << eof_len) | eof_code
        nbits += eof_len
        while nbits >= 8:
            nbits -= 8
            out.append((acc >> nbits) & 0xFF)
            acc &= (1 << nbits) - 1
    total_bits = len(out) * 8 + nbits
    if nbits > 0:
        out.append((acc << (8 - nbits)) & 0xFF)
    return bytes(out), total_bits


def decode_bitstream(payload, num_docs, decode_tree):
    """Decodes an exact byte stream back into a list of raw document byte strings."""
    docs = []
    cur = []
    node = decode_tree
    for byte in payload:
        for shift in range(7, -1, -1):
            bit = (byte >> shift) & 1
            node = node[bit]
            sym = node.get('sym')
            if sym is not None:
                if sym == EOF_SYMBOL:
                    docs.append(b''.join(cur))
                    cur = []
                    if len(docs) == num_docs:
                        return docs
                else:
                    cur.append(sym)
                node = decode_tree
    raise ValueError(f'truncated bitstream: decoded {len(docs)} of {num_docs} docs')


def parse_min_tokens(raw, root):
    """Exact minimum-token shortest-path DP segmentation."""
    n = len(raw)
    dp = [n + 1] * (n + 1)
    prev = [None] * (n + 1)
    dp[0] = 0
    for i in range(n):
        base = dp[i]
        if base > n:
            continue
        node = root
        j = i
        while j < n:
            node = node.get(raw[j])
            if node is None:
                break
            j += 1
            entry = node.get(-1)
            if entry is not None and base + 1 < dp[j]:
                dp[j] = base + 1
                prev[j] = (i, entry)
    if dp[n] > n:
        return None
    out = []
    at = n
    while at > 0:
        at, entry = prev[at]
        out.append(entry)
    out.reverse()
    if b''.join(out) != raw:
        raise AssertionError('token parse failed reconstruction')
    return out


def parse_min_bits(raw, root, bit_lengths, unused_cost):
    """Exact minimum-bit-length shortest-path DP segmentation for fixed code lengths."""
    n = len(raw)
    inf = 1 << 60
    dp_bits = [inf] * (n + 1)
    dp_toks = [n + 1] * (n + 1)
    prev = [None] * (n + 1)
    dp_bits[0] = 0
    dp_toks[0] = 0
    for i in range(n):
        b0 = dp_bits[i]
        if b0 >= inf:
            continue
        t0 = dp_toks[i]
        node = root
        j = i
        while j < n:
            node = node.get(raw[j])
            if node is None:
                break
            j += 1
            entry = node.get(-1)
            if entry is not None:
                cand_bits = b0 + bit_lengths.get(entry, unused_cost)
                cand_toks = t0 + 1
                if cand_bits < dp_bits[j] or (cand_bits == dp_bits[j] and cand_toks < dp_toks[j]):
                    dp_bits[j] = cand_bits
                    dp_toks[j] = cand_toks
                    prev[j] = (i, entry)
    if dp_bits[n] >= inf:
        return None
    out = []
    at = n
    while at > 0:
        at, entry = prev[at]
        out.append(entry)
    out.reverse()
    if b''.join(out) != raw:
        raise AssertionError('bit parse failed reconstruction')
    return out


def segment_corpus_tokens(docs, root):
    parsed, counts, tokens = [], Counter(), 0
    for raw in docs:
        pieces = parse_min_tokens(raw, root)
        if pieces is None:
            return None, None, None
        parsed.append(pieces)
        counts.update(pieces)
        tokens += len(pieces)
    counts[EOF_SYMBOL] = len(docs)
    return parsed, counts, tokens


def segment_corpus_bits(docs, root, bit_lengths, unused_cost):
    parsed, counts, tokens = [], Counter(), 0
    for raw in docs:
        pieces = parse_min_bits(raw, root, bit_lengths, unused_cost)
        if pieces is None:
            return None, None, None
        parsed.append(pieces)
        counts.update(pieces)
        tokens += len(pieces)
    counts[EOF_SYMBOL] = len(docs)
    return parsed, counts, tokens


def optimize_byte_segmentation(docs, root, max_iters=15):
    """Exact coordinate descent from token-optimal parse to byte-optimal fixed point.

    Returns dict with pass0 (token-min), pass1 (1-step DP), and fixed_point results,
    including verified bit lengths, counts, and parsed pieces.
    """
    p0, c0, t0 = segment_corpus_tokens(docs, root)
    if p0 is None:
        return None
    l0 = canonical_huffman_lengths(c0)
    b0 = total_huffman_bits(c0, l0)

    cur_p, cur_c, cur_t, cur_l, cur_b = p0, c0, t0, l0, b0
    pass1 = None
    iters = 0
    for step in range(1, max_iters + 1):
        unused_cost = max(cur_l.values()) + 1
        np, nc, nt = segment_corpus_bits(docs, root, cur_l, unused_cost)
        if np is None:
            break
        nl = canonical_huffman_lengths(nc)
        nb = total_huffman_bits(nc, nl)
        if step == 1:
            pass1 = {'tokens': nt, 'payload_bits': nb, 'payload_bytes': math.ceil(nb / 8)}
        if nb < cur_b:
            cur_p, cur_c, cur_t, cur_l, cur_b = np, nc, nt, nl, nb
            iters = step
        else:
            break

    return {
        'token_min': {
            'tokens': t0,
            'payload_bits': b0,
            'payload_bytes': math.ceil(b0 / 8),
            'counts': c0,
            'lengths': l0,
            'pieces': p0,
        },
        'byte_min_pass1': pass1,
        'byte_min': {
            'tokens': cur_t,
            'payload_bits': cur_b,
            'payload_bytes': math.ceil(cur_b / 8),
            'iters': iters,
            'counts': cur_c,
            'lengths': cur_l,
            'pieces': cur_p,
        },
    }


def compute_kl_js_decomposition(counts_py, counts_js, num_entries):
    """Computes exact weighted Jensen-Shannon divergence (I(Symbol; Language) in bits)
    explaining when Design B's extra language code table pays for itself over Design A.
    """
    n_py = sum(counts_py.values())
    n_js = sum(counts_js.values())
    n_tot = n_py + n_js
    all_syms = set(counts_py) | set(counts_js)
    kl_py = 0.0
    kl_js = 0.0
    for sym in all_syms:
        cp = counts_py.get(sym, 0)
        cj = counts_js.get(sym, 0)
        cm = cp + cj
        if cm == 0:
            continue
        p_mix = cm / n_tot
        if cp > 0:
            p_py = cp / n_py
            kl_py += cp * math.log2(p_py / p_mix)
        if cj > 0:
            p_js = cj / n_js
            kl_js += cj * math.log2(p_js / p_mix)
    mi_bits = kl_py + kl_js
    table_overhead_bytes = (num_entries + 1) + ROUTING_BYTES
    return {
        'kl_py_bits': round(kl_py, 2),
        'kl_js_bits': round(kl_js, 2),
        'mutual_info_bits': round(mi_bits, 2),
        'theoretical_payload_saving_bytes': round(mi_bits / 8.0, 2),
        'extra_table_and_routing_bytes': table_overhead_bytes,
        'theoretical_net_saving_bytes': round(mi_bits / 8.0 - table_overhead_bytes, 2),
    }


def benchmark_encode_decode(docs, entries, mode='token_min', repeats=3):
    """Measures real bitstream encode + canonical Huffman decode time and verifies exact bytes."""
    root = build_trie(entries)
    res = optimize_byte_segmentation(docs, root)
    if res is None:
        return None
    seg = res[mode]
    lengths = seg['lengths']
    codes = assign_canonical_codes(lengths)
    decode_tree = build_decode_tree(codes)
    unused_cost = max(lengths.values()) + 1
    raw_bytes = sum(len(d) for d in docs)

    enc_times = []
    payload = None
    total_bits = 0
    for _ in range(repeats):
        t0 = time.perf_counter()
        if mode == 'token_min':
            pieces = [parse_min_tokens(d, root) for d in docs]
        else:
            pieces = [parse_min_bits(d, root, lengths, unused_cost) for d in docs]
        payload, total_bits = encode_bitstream(pieces, codes)
        enc_times.append((time.perf_counter() - t0) * 1000.0)

    dec_times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        rebuilt = decode_bitstream(payload, len(docs), decode_tree)
        dec_times.append((time.perf_counter() - t0) * 1000.0)
        if rebuilt != docs:
            raise AssertionError('bitstream decode mismatch!')

    enc_ms = sorted(enc_times)[len(enc_times) // 2]
    dec_ms = sorted(dec_times)[len(dec_times) // 2]
    return {
        'mode': mode,
        'raw_bytes': raw_bytes,
        'payload_bits': total_bits,
        'payload_bytes': len(payload),
        'encode_median_ms': round(enc_ms, 2),
        'decode_median_ms': round(dec_ms, 2),
        'encode_mb_per_s': round((raw_bytes / 1e6) / (enc_ms / 1000.0), 3) if enc_ms > 0 else None,
        'decode_mb_per_s': round((raw_bytes / 1e6) / (dec_ms / 1000.0), 3) if dec_ms > 0 else None,
        'verified_exact': True,
    }
