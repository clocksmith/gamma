#!/usr/bin/env python3
"""Run the frozen CodeNet paired Python/JavaScript BITS replication (Rung 3 + Rung 4 DCC).

Executes:
  1. Compiles `../fixed-source-v3/engine.c` locally (no source modifications).
  2. Runs all 7 equal-budget dictionary search arms across `both`, `python`, `javascript`,
     policies `s1-whole`, `s2-nowhole`, `p2-nowhole`, and length limits:
       - primary split: L in (8, 16, 32)
       - secondary split (disjoint 200 pairs): L = 16
  3. Scores every legal dictionary prefix under exact fixed-source-v3 accounting
     (dict_bytes + table_bytes + routing_bytes + payload_bytes) with policy floors
     and Design-C union floor.
  4. Runs exact bit-length-minimizing fixed-point DP segmentation (`byte_encode.py`)
     across all candidate arms & prefixes for L=16 cells, checking whether Design B
     dominance and token-min vs byte-min divergence survive byte-optimal segmentation
     and logging every excluded/infeasible cell and any ranking reversal.
  5. Computes the exact KL / Jensen-Shannon mutual-information decomposition of
     Design B vs Design A across K in {128, 256, 512, 1024, 2048, 4096} AND across
     sub-corpus sizes N_pairs in {10, 25, 50, 100, 150, 200} to expose the exact
     table-overhead crossover.
  6. Exports verified headline dictionaries (hex-encoded) and runs real packed
     canonical Huffman bitstream encode/decode throughput benchmarks with exact
     byte-for-byte round-trip verification.
"""
import concurrent.futures
import hashlib
import json
import math
import multiprocessing
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
V3_DIR = HERE.parent / 'fixed-source-v3'
sys.path.insert(0, str(HERE))
import byte_encode as BE

ROUTING = 4
STEP_MAIN = 16
STEP_AUX = 64
SLOTS = (128, 256, 512, 1024, 2048, 4096)
PRIMARY_SLOTS = (256, 1024, 4096)
CAPS = (4096, 8192, 16384, 32768, 65536, None)
POLICIES = ('s1-whole', 's2-nowhole', 'p2-nowhole')
ARMS = ('greedy-entry', 'greedy-byte', 'greedtok', 'freq-occ', 'freq-doc', 'bpe', 'pathpiece')
LIMIT_SECONDS = 300
# The engine reads its own limit only between rounds, and its BPE pair table (2^20 slots) never grows:
# with a full table it never returns. engine.c is pinned by hash in four freeze records and is not
# edited, so the driver bounds every run instead. The longest finished run on record took 84 s.
ENGINE_TIMEOUT_SECONDS = 3 * LIMIT_SECONDS
_WORKER_DOCS = {}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compile_engine(build_dir):
    build_dir.mkdir(parents=True, exist_ok=True)
    engine_bin = build_dir / 'engine'
    engine_src = V3_DIR / 'engine.c'
    cmd = ['cc', '-O3', '-Wall', '-Wno-unused-function', '-o', str(engine_bin), str(engine_src), '-lm']
    subprocess.run(cmd, check=True)
    return engine_bin, sha256_file(engine_src)


def chain_footer(path):
    """The fields of the engine's last line, `D <mode> ... stopped=0 ...`, or None.

    The engine writes its chain in place and that line last, so it is the only sign that a run
    finished. A file without it was interrupted; a file with stopped=1 ran into the time limit and
    is shorter than was asked for."""
    try:
        with open(path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 4096))
            tail = f.read().decode('utf-8', 'replace')
    except OSError:
        return None
    if not tail.endswith('\n'):
        return None
    last = tail.rstrip('\n').rsplit('\n', 1)[-1].split()
    if len(last) < 2 or last[0] != 'D':
        return None
    return dict(tok.split('=', 1) for tok in last[2:] if '=' in tok)


def chain_complete(path):
    footer = chain_footer(path)
    return footer is not None and footer.get('stopped') == '0'


def run_engine(engine_bin, mode, policy, L, kmax, list_path, out_path, env, extra=()):
    """Run one engine job into a temporary name and move it into place only if it finished inside its
    time limit, so that an interrupted or time-limited run can never be taken for a chain."""
    out_path = Path(out_path)
    partial = out_path.with_name(out_path.name + '.partial')
    partial.unlink(missing_ok=True)
    try:
        subprocess.run(
            [str(engine_bin), mode, policy, str(L), str(kmax), str(LIMIT_SECONDS), str(list_path), str(partial), *extra],
            env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=ENGINE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f'{out_path.name}: the engine did not return in {ENGINE_TIMEOUT_SECONDS} s and was killed. '
                           f'Its pair table holds 2^20 pairs and does not grow; the corpus may be too large for it.') from None
    footer = chain_footer(partial)
    if footer is None:
        raise RuntimeError(f'{out_path.name}: the engine exited without its end line')
    if footer.get('stopped') != '0':
        raise RuntimeError(f'{out_path.name}: the engine reached its {LIMIT_SECONDS} s limit (stopped={footer.get("stopped")}); '
                           f'the chain is shorter than the {kmax} entries asked for and is kept as {partial.name}')
    os.replace(partial, out_path)
    return out_path


def read_chain(path):
    """Parse an engine.c chain file into (header_dict, entries_list, merges_list).
    Refuses a chain that was interrupted or ran into the engine's time limit."""
    if not chain_complete(path):
        raise ValueError(f'{path}: not a finished chain (no end line, or stopped=1)')
    entries = []
    merges = []
    header = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            tag = parts[0]
            if tag == 'H':
                for tok in parts[1:]:
                    if '=' in tok:
                        k, v = tok.split('=', 1)
                        header[k] = v
            elif tag == 'M':
                merges.append((bytes.fromhex(parts[1]), bytes.fromhex(parts[2])))
            elif tag == 'E':
                count = int(parts[1])
                stored = int(parts[2])
                emissions = int(parts[3])
                spelled = int(parts[4])
                raw = bytes.fromhex(parts[5])
                entries.append((count, stored, emissions, spelled, raw))
    return header, entries, merges


def check_entries_policy(entry_bytes_list, docs, groups, limit, policy):
    """Independently verify policy legality (length, uniqueness, support, no-whole)."""
    seen = set()
    for e in entry_bytes_list:
        if not e or len(e) > limit or e in seen:
            return False
        seen.add(e)
    if policy == 's1-whole':
        return True
    if policy in ('s2-nowhole', 'p2-nowhole'):
        doc_set = set(docs)
        for e in entry_bytes_list:
            if len(e) == 1:
                continue
            if e in doc_set:
                return False
            if policy == 's2-nowhole':
                hits = sum(1 for d in docs if e in d)
                if hits < 2:
                    return False
            else:
                g_hits = {groups[i] for i, d in enumerate(docs) if e in d}
                if len(g_hits) < 2:
                    return False
    return True


def run_single_engine_job(job):
    engine_bin, split, policy, arm, L, corpus, lists_dir, out_dir, receipt = job
    out_chain = out_dir / split / policy / f'{corpus}-L{L}-{arm}.txt'
    out_chain.parent.mkdir(parents=True, exist_ok=True)
    if chain_complete(out_chain):  # resume only from a run that finished; a non-empty file is not enough
        return str(out_chain), 0.0

    env = os.environ.copy()
    env['FSV3_GROUPS'] = str(lists_dir / f'{corpus}.groups')
    env['FSV3_RECEIPT'] = receipt
    env.pop('FSV3_CUTS', None)

    t0 = time.perf_counter()
    extra = []
    if arm == 'pathpiece':
        v0_path = out_dir / split / 'v0' / f'{policy}-{corpus}-L{L}.txt'
        v0_path.parent.mkdir(parents=True, exist_ok=True)
        seed_path = v0_path.with_suffix('.seed')
        if not (seed_path.exists() and chain_complete(v0_path)):
            run_engine(engine_bin, 'bpe', policy, L, 32768, lists_dir / f'{corpus}.txt', v0_path, env)
            seeds = []
            with open(v0_path, 'r', encoding='utf-8') as f:
                for line in f:
                    p = line.strip().split()
                    if len(p) >= 6 and p[0] == 'E' and len(p[5]) >= 4:
                        seeds.append(p[5])
            seed_tmp = seed_path.with_name(seed_path.name + '.partial')
            seed_tmp.write_text('\n'.join(seeds) + '\n', encoding='utf-8')
            os.replace(seed_tmp, seed_path)
        extra = [str(seed_path)]

    run_engine(engine_bin, arm, policy, L, 4096, lists_dir / f'{corpus}.txt', out_chain, env, extra)
    elapsed = time.perf_counter() - t0
    return str(out_chain), elapsed


def prefix_sizes(entries, step=STEP_MAIN):
    total = len(entries)
    wanted = {s for s in range(step, total + 1, step)} | {total}
    for k in SLOTS:
        if k <= total:
            wanted.add(k)
        for b in CAPS:
            if b is None:
                continue
            best_s = 0
            for idx, row in enumerate(entries, 1):
                if idx <= k and row[1] <= b:
                    best_s = idx
                else:
                    break
            if best_s > 0:
                wanted.add(best_s)
    return sorted(s for s in wanted if 0 < s <= total)


def score_shared_chain_token_min(entries, py_docs, js_docs, arm, policy, step=STEP_MAIN):
    """Score all prefix sizes of a shared chain under token-minimal segmentation."""
    out = []
    root = {}
    at = 0
    for size in prefix_sizes(entries, step=step):
        while at < size:
            BE.insert_trie(root, entries[at][4])
            at += 1
        p_py, c_py, t_py = BE.segment_corpus_tokens(py_docs, root)
        if p_py is None:
            continue
        p_js, c_js, t_js = BE.segment_corpus_tokens(js_docs, root)
        if p_js is None:
            continue
        stored = entries[size - 1][1]
        symbols = size + 1

        c_all = Counter(c_py)
        c_all.update(c_js)
        l_a = BE.canonical_huffman_lengths(c_all)
        bits_a = BE.total_huffman_bits(c_all, l_a)
        pay_a = math.ceil(bits_a / 8)

        l_p = BE.canonical_huffman_lengths(c_py)
        bits_p = BE.total_huffman_bits(c_py, l_p)
        pay_p = math.ceil(bits_p / 8)

        l_j = BE.canonical_huffman_lengths(c_js)
        bits_j = BE.total_huffman_bits(c_js, l_j)
        pay_j = math.ceil(bits_j / 8)

        out.append({
            'arm': arm,
            'source_policy': policy,
            'entries': size,
            'stored': stored,
            'tokens': t_py + t_js,
            'tokens_py': t_py,
            'tokens_js': t_js,
            'table_a': symbols,
            'payload_a': pay_a,
            'A': stored + symbols + pay_a,
            'table_b': 2 * symbols,
            'routing_b': ROUTING,
            'payload_b': pay_p + pay_j,
            'payload_py': pay_p,
            'payload_js': pay_j,
            'B': stored + 2 * symbols + ROUTING + pay_p + pay_j,
        })
    return out


def score_lang_chain_token_min(entries, docs, arm, policy, step=STEP_MAIN):
    out = []
    root = {}
    at = 0
    for size in prefix_sizes(entries, step=step):
        while at < size:
            BE.insert_trie(root, entries[at][4])
            at += 1
        pieces, counts, toks = BE.segment_corpus_tokens(docs, root)
        if pieces is None:
            continue
        stored = entries[size - 1][1]
        symbols = size + 1
        lengths = BE.canonical_huffman_lengths(counts)
        bits = BE.total_huffman_bits(counts, lengths)
        pay = math.ceil(bits / 8)
        out.append({
            'arm': arm,
            'source_policy': policy,
            'entries': size,
            'stored': stored,
            'tokens': toks,
            'table': symbols,
            'payload': pay,
            'cost': stored + symbols + pay,
        })
    return out


def score_shared_entries_exact(entry_bytes_list, py_docs, js_docs, do_bytemin=True):
    """Exact token-min AND byte-min scoring for a specific shared dictionary entry list."""
    root = BE.build_trie(entry_bytes_list)
    stored = sum(1 + len(e) for e in entry_bytes_list)
    size = len(entry_bytes_list)
    symbols = size + 1

    # Token-min
    p_py, c_py, t_py = BE.segment_corpus_tokens(py_docs, root)
    p_js, c_js, t_js = BE.segment_corpus_tokens(js_docs, root)
    if p_py is None or p_js is None:
        return None
    c_all = Counter(c_py)
    c_all.update(c_js)
    la = BE.canonical_huffman_lengths(c_all)
    ba = BE.total_huffman_bits(c_all, la)
    lp = BE.canonical_huffman_lengths(c_py)
    bp = BE.total_huffman_bits(c_py, lp)
    lj = BE.canonical_huffman_lengths(c_js)
    bj = BE.total_huffman_bits(c_js, lj)

    res = {
        'entries': size,
        'stored': stored,
        'token_min': {
            'tokens': t_py + t_js,
            'tokens_py': t_py,
            'tokens_js': t_js,
            'A': {
                'dict_bytes': stored,
                'table_bytes': symbols,
                'routing_bytes': 0,
                'payload_bytes': math.ceil(ba / 8),
                'payload_bits': ba,
                'total_bytes': stored + symbols + math.ceil(ba / 8),
                'active_entries': sum(1 for k in c_all if k != BE.EOF_SYMBOL),
            },
            'B': {
                'dict_bytes': stored,
                'table_bytes': 2 * symbols,
                'routing_bytes': ROUTING,
                'payload_bytes': math.ceil(bp / 8) + math.ceil(bj / 8),
                'payload_py_bytes': math.ceil(bp / 8),
                'payload_js_bytes': math.ceil(bj / 8),
                'payload_bits': bp + bj,
                'total_bytes': stored + 2 * symbols + ROUTING + math.ceil(bp / 8) + math.ceil(bj / 8),
                'active_entries_py': sum(1 for k in c_py if k != BE.EOF_SYMBOL),
                'active_entries_js': sum(1 for k in c_js if k != BE.EOF_SYMBOL),
            },
        },
    }

    if do_bytemin:
        opt_a = BE.optimize_byte_segmentation(py_docs + js_docs, root)
        opt_py = BE.optimize_byte_segmentation(py_docs, root)
        opt_js = BE.optimize_byte_segmentation(js_docs, root)
        bm_a = opt_a['byte_min']
        bm_p = opt_py['byte_min']
        bm_j = opt_js['byte_min']
        res['byte_min'] = {
            'A': {
                'dict_bytes': stored,
                'table_bytes': symbols,
                'routing_bytes': 0,
                'payload_bytes': bm_a['payload_bytes'],
                'payload_bits': bm_a['payload_bits'],
                'total_bytes': stored + symbols + bm_a['payload_bytes'],
                'tokens': bm_a['tokens'],
                'iterations': bm_a['iters'],
                'active_entries': sum(1 for k in bm_a['counts'] if k != BE.EOF_SYMBOL),
            },
            'B': {
                'dict_bytes': stored,
                'table_bytes': 2 * symbols,
                'routing_bytes': ROUTING,
                'payload_bytes': bm_p['payload_bytes'] + bm_j['payload_bytes'],
                'payload_py_bytes': bm_p['payload_bytes'],
                'payload_js_bytes': bm_j['payload_bytes'],
                'payload_bits': bm_p['payload_bits'] + bm_j['payload_bits'],
                'total_bytes': stored + 2 * symbols + ROUTING + bm_p['payload_bytes'] + bm_j['payload_bytes'],
                'tokens': bm_p['tokens'] + bm_j['tokens'],
                'iterations_py': bm_p['iters'],
                'iterations_js': bm_j['iters'],
                'active_entries_py': sum(1 for k in bm_p['counts'] if k != BE.EOF_SYMBOL),
                'active_entries_js': sum(1 for k in bm_j['counts'] if k != BE.EOF_SYMBOL),
            },
        }
    return res


def score_single_lang_entries_exact(entry_bytes_list, docs, do_bytemin=True):
    root = BE.build_trie(entry_bytes_list)
    stored = sum(1 + len(e) for e in entry_bytes_list)
    size = len(entry_bytes_list)
    symbols = size + 1
    p0, c0, t0 = BE.segment_corpus_tokens(docs, root)
    if p0 is None:
        return None
    l0 = BE.canonical_huffman_lengths(c0)
    b0 = BE.total_huffman_bits(c0, l0)
    res = {
        'entries': size,
        'stored': stored,
        'token_min': {
            'dict_bytes': stored,
            'table_bytes': symbols,
            'payload_bytes': math.ceil(b0 / 8),
            'payload_bits': b0,
            'total_bytes': stored + symbols + math.ceil(b0 / 8),
            'tokens': t0,
            'active_entries': sum(1 for k in c0 if k != BE.EOF_SYMBOL),
        },
    }
    if do_bytemin:
        opt = BE.optimize_byte_segmentation(docs, root)
        bm = opt['byte_min']
        res['byte_min'] = {
            'dict_bytes': stored,
            'table_bytes': symbols,
            'payload_bytes': bm['payload_bytes'],
            'payload_bits': bm['payload_bits'],
            'total_bytes': stored + symbols + bm['payload_bytes'],
            'tokens': bm['tokens'],
            'iterations': bm['iters'],
            'active_entries': sum(1 for k in bm['counts'] if k != BE.EOF_SYMBOL),
        }
    return res


def pareto(points, key):
    points = sorted(points, key=lambda p: (p['entries'], p['stored'], p[key]))
    kept, best = [], []
    for p in points:
        if any(s <= p['stored'] and c <= p[key] for s, c in best):
            continue
        kept.append(p)
        best.append((p['stored'], p[key]))
    return kept


def best_shared(points, budget, cap, key):
    routed = ROUTING if key == 'B' else 0
    usable = [p for p in points if p['entries'] <= budget and (cap is None or p['stored'] + routed <= cap)]
    if not usable:
        return None
    return min(usable, key=lambda p: (p[key], p['tokens'], p['arm'], p['entries']))


def best_separate(py_pts, js_pts, budget, cap):
    best = None
    for a in py_pts:
        if a['entries'] >= budget:
            continue
        for b in js_pts:
            if a['entries'] + b['entries'] > budget:
                continue
            stored = a['stored'] + b['stored'] + ROUTING
            if cap is not None and stored > cap:
                continue
            total = a['cost'] + b['cost'] + ROUTING
            row = (
                total, a['tokens'] + b['tokens'], a['arm'], b['arm'],
                a['entries'], b['entries'], stored,
                a['source_policy'], b['source_policy'],
                a['stored'], b['stored'], a['table'], b['table'],
                a['payload'], b['payload'],
            )
            if best is None or row < best:
                best = row
    if best is None:
        return None
    return {
        'total_bytes': best[0],
        'tokens': best[1],
        'python_arm': best[2],
        'javascript_arm': best[3],
        'python_entries': best[4],
        'javascript_entries': best[5],
        'entries': best[4] + best[5],
        'stored': best[6],
        'python_policy': best[7],
        'javascript_policy': best[8],
        'dict_bytes': best[9] + best[10],
        'table_bytes': best[11] + best[12],
        'routing_bytes': ROUTING,
        'payload_bytes': best[13] + best[14],
        'payload_py_bytes': best[13],
        'payload_js_bytes': best[14],
    }


def stricter(policy):
    return {'s1-whole': ('s2-nowhole', 'p2-nowhole'), 's2-nowhole': ('p2-nowhole',)}.get(policy, ())


def load_split_docs(manifest, split_name):
    pairs = manifest['splits'][split_name]['pairs']
    py_docs = [(HERE / p['python']['path']).read_bytes() for p in pairs]
    js_docs = [(HERE / p['javascript']['path']).read_bytes() for p in pairs]
    groups = list(range(len(pairs)))
    return py_docs, js_docs, groups


def _score_chain_worker(job):
    policy, L, corpus, arm, cpath_str = job
    _, entries, _ = read_chain(cpath_str)
    step = STEP_MAIN if L == 16 else STEP_AUX
    if corpus == 'both':
        rows = score_shared_chain_token_min(entries, _WORKER_DOCS['python'], _WORKER_DOCS['javascript'], arm, policy, step=step)
    else:
        rows = score_lang_chain_token_min(entries, _WORKER_DOCS[corpus], arm, policy, step=step)
    return (policy, L, corpus, arm), entries, rows


def kl_decomp_from_docs(py_docs, js_docs, root, num_entries):
    _, c_py, t_py = BE.segment_corpus_tokens(py_docs, root)
    _, c_js, t_js = BE.segment_corpus_tokens(js_docs, root)
    base = BE.compute_kl_js_decomposition(c_py, c_js, num_entries)
    c_all = Counter(c_py)
    c_all.update(c_js)
    la = BE.canonical_huffman_lengths(c_all)
    lp = BE.canonical_huffman_lengths(c_py)
    lj = BE.canonical_huffman_lengths(c_js)
    pay_a = math.ceil(BE.total_huffman_bits(c_all, la) / 8)
    pay_b = math.ceil(BE.total_huffman_bits(c_py, lp) / 8) + math.ceil(BE.total_huffman_bits(c_js, lj) / 8)
    n_tok = sum(c_all.values())
    extra_hdr = (num_entries + 1) + ROUTING
    return {
        **base,
        'tokens_py': t_py,
        'tokens_js': t_js,
        'symbols_emitted_with_eof': n_tok,
        'mutual_info_bits_per_token': base['mutual_info_bits'] / n_tok if n_tok else 0.0,
        'ideal_payload_saving_bytes': base['mutual_info_bits'] / 8.0,
        'actual_huffman_payload_saving_bytes': pay_a - pay_b,
        'actual_net_B_saving_bytes': (pay_a - pay_b) - extra_hdr,
    }


def analyze_split(split_name, lengths, manifest, chains_dir, dict_export_dir=None):
    py_docs, js_docs, groups = load_split_docs(manifest, split_name)
    both_docs = py_docs + js_docs
    both_groups = groups + groups

    _WORKER_DOCS['python'] = py_docs
    _WORKER_DOCS['javascript'] = js_docs

    cache_path = chains_dir / f'cache_{split_name}_own.json'
    # Every arm is part of the comparison. A chain that is missing or unfinished is an error, not a
    # smaller grid: dropping it silently would change which arm wins a cell.
    expected = [(policy, L, corpus, arm, chains_dir / split_name / policy / f'{corpus}-L{L}-{arm}.txt')
                for policy in POLICIES for L in lengths for corpus in ('both', 'python', 'javascript') for arm in ARMS]
    unfinished = [str(p.relative_to(chains_dir)) for *_, p in expected if not chain_complete(p)]
    if unfinished:
        raise SystemExit(f'{len(unfinished)} of {len(expected)} chains of split {split_name} are missing or unfinished, '
                         f'e.g. {unfinished[:3]}; run the engine jobs again before scoring')
    chain_cache = {}
    for policy, L, corpus, arm, cpath in expected:
        _, entries, _ = read_chain(cpath)
        chain_cache[(policy, L, corpus, arm)] = entries

    # The prefix-score cache is valid only for the chains it was computed from.
    fingerprint = hashlib.sha256(json.dumps(
        [[str(p.relative_to(chains_dir)), sha256_file(p)] for *_, p in expected] + [list(lengths), STEP_MAIN, STEP_AUX]).encode()).hexdigest()
    cached = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else None
    if isinstance(cached, dict) and cached.get('chains_fingerprint') == fingerprint:
        own = {tuple(k.split('|'))[:1] + (int(k.split('|')[1]), k.split('|')[2]): v for k, v in cached['rows'].items()}
        print(f'  Loaded cached prefix scores from {cache_path.name} (chains unchanged)', flush=True)
    else:
        if cached is not None:
            print(f'  Ignoring {cache_path.name}: it was not computed from these chains', flush=True)
        score_jobs = [(policy, L, corpus, arm, str(cpath)) for policy, L, corpus, arm, cpath in expected]
        own = {(policy, L, corpus): [] for policy in POLICIES for L in lengths for corpus in ('both', 'python', 'javascript')}
        workers = min(8, os.cpu_count() or 4)
        with multiprocessing.get_context('fork').Pool(workers) as pool:
            # In job order, so that the rows do not depend on which worker finishes first.
            for key, entries, rows in pool.imap(_score_chain_worker, score_jobs, chunksize=1):
                policy, L, corpus, arm = key
                chain_cache[key] = entries
                own[(policy, L, corpus)].extend(rows)
        ser_own = {f'{p}|{L}|{c}': rows for (p, L, c), rows in own.items()}
        cache_tmp = cache_path.with_name(cache_path.name + '.partial')
        cache_tmp.write_text(json.dumps({'chains_fingerprint': fingerprint, 'rows': ser_own}), encoding='utf-8')
        os.replace(cache_tmp, cache_path)
        print(f'  Saved prefix score cache to {cache_path.name}', flush=True)

    # Apply monotonicity floors (looser policy includes stricter policies' legal chains)
    points = {}
    for (policy, L, corpus), rows in own.items():
        combined = list(rows)
        for src in stricter(policy):
            combined.extend(own.get((src, L, corpus), []))
        points[(policy, L, corpus)] = combined

    def get_shared_entries(cand, L):
        if cand['arm'] == 'union':
            return cand['_union_entries']
        return [r[4] for r in chain_cache[(cand['source_policy'], L, 'both', cand['arm'])][: cand['entries']]]

    def build_union_entries(policy, L, c_row, budget):
        seen, order = set(), []
        for corpus, arm, sz, src_p in (
            ('python', c_row['python_arm'], c_row['python_entries'], c_row['python_policy']),
            ('javascript', c_row['javascript_arm'], c_row['javascript_entries'], c_row['javascript_policy']),
        ):
            for r in chain_cache[(src_p, L, corpus, arm)][:sz]:
                if r[4] not in seen:
                    seen.add(r[4])
                    order.append(r[4])
        if len(order) > budget:
            return None
        if not check_entries_policy(order, both_docs, both_groups, L, policy):
            return None
        sc = score_shared_entries_exact(order, py_docs, js_docs, do_bytemin=False)
        if sc is None:
            return None
        tm = sc['token_min']
        return {
            'arm': 'union',
            'source_policy': policy,
            'entries': sc['entries'],
            'stored': sc['stored'],
            'tokens': tm['tokens'],
            'tokens_py': tm['tokens_py'],
            'tokens_js': tm['tokens_js'],
            'table_a': tm['A']['table_bytes'],
            'payload_a': tm['A']['payload_bytes'],
            'A': tm['A']['total_bytes'],
            'table_b': tm['B']['table_bytes'],
            'routing_b': ROUTING,
            'payload_b': tm['B']['payload_bytes'],
            'payload_py': tm['B']['payload_py_bytes'],
            'payload_js': tm['B']['payload_js_bytes'],
            'B': tm['B']['total_bytes'],
            '_union_entries': order,
        }

    # Memoize expensive byte-min evaluations by (tuple_of_entries_sha256, mode)
    bm_shared_cache = {}
    bm_lang_cache = {}

    def eval_shared_bm(entry_list):
        key = hashlib.sha256(b'\x00'.join(entry_list)).hexdigest()
        if key not in bm_shared_cache:
            bm_shared_cache[key] = score_shared_entries_exact(entry_list, py_docs, js_docs, do_bytemin=True)
        return bm_shared_cache[key]

    def eval_lang_bm(corpus_name, entry_list):
        key = (corpus_name, hashlib.sha256(b'\x00'.join(entry_list)).hexdigest())
        if key not in bm_lang_cache:
            docs = py_docs if corpus_name == 'python' else js_docs
            bm_lang_cache[key] = score_single_lang_entries_exact(entry_list, docs, do_bytemin=True)
        return bm_lang_cache[key]

    cells = []
    exported_dicts = {}

    for policy in POLICIES:
        for L in lengths:
            both_pts = points[(policy, L, 'both')]
            py_pts = pareto(points[(policy, L, 'python')], 'cost')
            js_pts = pareto(points[(policy, L, 'javascript')], 'cost')
            for K in SLOTS:
                for B in CAPS:
                    c_row = best_separate(py_pts, js_pts, K, B)
                    pool = list(both_pts)
                    union_pt = None
                    if c_row is not None:
                        union_pt = build_union_entries(policy, L, c_row, K)
                        if union_pt is not None and (B is None or union_pt['stored'] <= B):
                            pool.append(union_pt)
                    a_row = best_shared(pool, K, B, 'A')
                    b_row = best_shared(pool, K, B, 'B')
                    tok_row = best_shared(both_pts, K, B, 'tokens')

                    # Per-arm best Design A and Design B at equal budget
                    by_arm = {}
                    for arm in ARMS:
                        arm_pts = [p for p in both_pts if p['arm'] == arm]
                        fa = best_shared(arm_pts, K, B, 'A')
                        fb = best_shared(arm_pts, K, B, 'B')
                        ft = best_shared(arm_pts, K, B, 'tokens')
                        if fa or fb:
                            by_arm[arm] = {
                                'A': None if not fa else {
                                    'total_bytes': fa['A'], 'dict_bytes': fa['stored'],
                                    'table_bytes': fa['table_a'], 'payload_bytes': fa['payload_a'],
                                    'entries': fa['entries'], 'tokens': fa['tokens'],
                                    'source_policy': fa['source_policy'],
                                },
                                'B': None if not fb else {
                                    'total_bytes': fb['B'], 'dict_bytes': fb['stored'],
                                    'table_bytes': fb['table_b'], 'routing_bytes': ROUTING,
                                    'payload_bytes': fb['payload_b'],
                                    'entries': fb['entries'], 'tokens': fb['tokens'],
                                    'source_policy': fb['source_policy'],
                                },
                                'token_best_A': None if not ft else {
                                    'total_bytes': ft['A'], 'entries': ft['entries'], 'tokens': ft['tokens'],
                                },
                            }

                    cell = {
                        'split': split_name,
                        'policy': policy,
                        'L': L,
                        'K': K,
                        'B': B,
                        'feasible': all(x is not None for x in (a_row, b_row, c_row, tok_row)),
                        'excluded_reason': None,
                        'A': None if a_row is None else {
                            'arm': a_row['arm'], 'source_policy': a_row['source_policy'],
                            'entries': a_row['entries'], 'dict_bytes': a_row['stored'],
                            'table_bytes': a_row['table_a'], 'routing_bytes': 0,
                            'payload_bytes': a_row['payload_a'], 'total_bytes': a_row['A'],
                            'tokens': a_row['tokens'],
                        },
                        'B_design': None if b_row is None else {
                            'arm': b_row['arm'], 'source_policy': b_row['source_policy'],
                            'entries': b_row['entries'], 'dict_bytes': b_row['stored'],
                            'table_bytes': b_row['table_b'], 'routing_bytes': ROUTING,
                            'payload_bytes': b_row['payload_b'],
                            'payload_py_bytes': b_row['payload_py'],
                            'payload_js_bytes': b_row['payload_js'],
                            'total_bytes': b_row['B'], 'tokens': b_row['tokens'],
                        },
                        'C': c_row,
                        'token_best': None if tok_row is None else {
                            'arm': tok_row['arm'], 'source_policy': tok_row['source_policy'],
                            'entries': tok_row['entries'], 'dict_bytes': tok_row['stored'],
                            'table_bytes': tok_row['table_a'], 'routing_bytes': 0,
                            'payload_bytes': tok_row['payload_a'], 'total_bytes': tok_row['A'],
                            'tokens': tok_row['tokens'],
                        },
                        'by_arm': by_arm,
                        'byte_min': None,
                    }
                    if not cell['feasible']:
                        missing = [name for name, val in (('A', a_row), ('B', b_row), ('C', c_row), ('token_best', tok_row)) if val is None]
                        cell['excluded_reason'] = 'infeasible_for_' + '+'.join(missing)

                    # Exact byte-optimal segmentation for ALL L=16 cells where shared designs A & B are feasible
                    # (including K=256 where A & B are feasible even though C is structurally infeasible due to
                    # 167+166=333 > 256 UTF-8 single-byte alphabet overlap!).
                    if L == 16 and a_row is not None and b_row is not None and tok_row is not None:
                        # Candidate pool for A and B under byte-min:
                        cand_A_list = [a_row, b_row, tok_row]
                        cand_B_list = [b_row, a_row, tok_row]
                        if B is None:
                            for arm in ARMS:
                                arm_pts = [p for p in both_pts if p['arm'] == arm]
                                for key in ('A', 'B', 'tokens'):
                                    fa = best_shared(arm_pts, K, B, key)
                                    if fa is not None:
                                        cand_A_list.append(fa)
                                        cand_B_list.append(fa)
                            if union_pt is not None:
                                cand_A_list.append(union_pt)
                                cand_B_list.append(union_pt)

                        best_bm_A = None
                        seen_a = set()
                        for cand in cand_A_list:
                            cid = (cand['arm'], cand['source_policy'], cand['entries'])
                            if cid in seen_a:
                                continue
                            seen_a.add(cid)
                            if cand['entries'] > K or (B is not None and cand['stored'] > B):
                                continue
                            entries_list = get_shared_entries(cand, L)
                            sc = eval_shared_bm(entries_list)
                            bm_a = sc['byte_min']['A']
                            rec = {**bm_a, 'arm': cand['arm'], 'source_policy': cand['source_policy'], 'entries': cand['entries']}
                            if best_bm_A is None or rec['total_bytes'] < best_bm_A['total_bytes']:
                                best_bm_A = rec

                        best_bm_B = None
                        seen_b = set()
                        for cand in cand_B_list:
                            cid = (cand['arm'], cand['source_policy'], cand['entries'])
                            if cid in seen_b:
                                continue
                            seen_b.add(cid)
                            if cand['entries'] > K or (B is not None and cand['stored'] + ROUTING > B):
                                continue
                            entries_list = get_shared_entries(cand, L)
                            sc = eval_shared_bm(entries_list)
                            bm_b = sc['byte_min']['B']
                            rec = {**bm_b, 'arm': cand['arm'], 'source_policy': cand['source_policy'], 'entries': cand['entries']}
                            if best_bm_B is None or rec['total_bytes'] < best_bm_B['total_bytes']:
                                best_bm_B = rec

                        # Token-best dictionary re-segmented with byte-min:
                        tok_entries = get_shared_entries(tok_row, L)
                        sc_tok = eval_shared_bm(tok_entries)
                        bm_tok = {
                            **sc_tok['byte_min']['A'],
                            'arm': tok_row['arm'],
                            'source_policy': tok_row['source_policy'],
                            'entries': tok_row['entries'],
                        }

                        # Design C under byte-min (only when C is feasible):
                        best_bm_C = None
                        if c_row is not None:
                            c_pairs_to_check = [(
                                c_row['python_arm'], c_row['python_policy'], c_row['python_entries'],
                                c_row['javascript_arm'], c_row['javascript_policy'], c_row['javascript_entries'],
                            )]
                            if B is None:
                                scored_pairs = []
                                for a in py_pts:
                                    if a['entries'] >= K:
                                        continue
                                    for b in js_pts:
                                        if a['entries'] + b['entries'] <= K:
                                            scored_pairs.append((a['cost'] + b['cost'] + ROUTING, a, b))
                                scored_pairs.sort(key=lambda x: x[0])
                                for _, a, b in scored_pairs[:6]:
                                    c_pairs_to_check.append((
                                        a['arm'], a['source_policy'], a['entries'],
                                        b['arm'], b['source_policy'], b['entries'],
                                    ))

                            seen_c = set()
                            for pa, pp, pe, ja, jp, je in c_pairs_to_check:
                                if (pa, pp, pe, ja, jp, je) in seen_c:
                                    continue
                                seen_c.add((pa, pp, pe, ja, jp, je))
                                py_el = [r[4] for r in chain_cache[(pp, L, 'python', pa)][:pe]]
                                js_el = [r[4] for r in chain_cache[(jp, L, 'javascript', ja)][:je]]
                                sp = eval_lang_bm('python', py_el)['byte_min']
                                sj = eval_lang_bm('javascript', js_el)['byte_min']
                                tot = sp['total_bytes'] + sj['total_bytes'] + ROUTING
                                rec = {
                                    'total_bytes': tot,
                                    'dict_bytes': sp['dict_bytes'] + sj['dict_bytes'],
                                    'table_bytes': sp['table_bytes'] + sj['table_bytes'],
                                    'routing_bytes': ROUTING,
                                    'payload_bytes': sp['payload_bytes'] + sj['payload_bytes'],
                                    'payload_py_bytes': sp['payload_bytes'],
                                    'payload_js_bytes': sj['payload_bytes'],
                                    'tokens': sp['tokens'] + sj['tokens'],
                                    'python_arm': pa, 'javascript_arm': ja,
                                    'python_policy': pp, 'javascript_policy': jp,
                                    'python_entries': pe, 'javascript_entries': je,
                                    'entries': pe + je,
                                }
                                if best_bm_C is None or rec['total_bytes'] < best_bm_C['total_bytes']:
                                    best_bm_C = rec

                        tm_cands = [('A', cell['A']['total_bytes']), ('B', cell['B_design']['total_bytes'])]
                        bm_cands = [('A', best_bm_A['total_bytes']), ('B', best_bm_B['total_bytes'])]
                        if cell['C'] is not None and best_bm_C is not None:
                            tm_cands.append(('C', cell['C']['total_bytes']))
                            bm_cands.append(('C', best_bm_C['total_bytes']))
                        tm_winner = min(tm_cands, key=lambda x: x[1])[0]
                        bm_winner = min(bm_cands, key=lambda x: x[1])[0]
                        cell['byte_min'] = {
                            'A': best_bm_A,
                            'B_design': best_bm_B,
                            'C': best_bm_C,
                            'token_best': bm_tok,
                            'token_min_winner': tm_winner,
                            'byte_min_winner': bm_winner,
                            'winner_reversed': tm_winner != bm_winner,
                            'B_beats_A': best_bm_B['total_bytes'] < best_bm_A['total_bytes'],
                            'B_beats_C': None if best_bm_C is None else (best_bm_B['total_bytes'] < best_bm_C['total_bytes']),
                            'A_delta_bytes': best_bm_A['total_bytes'] - cell['A']['total_bytes'],
                            'B_delta_bytes': best_bm_B['total_bytes'] - cell['B_design']['total_bytes'],
                            'C_delta_bytes': None if best_bm_C is None else (best_bm_C['total_bytes'] - cell['C']['total_bytes']),
                            'token_best_delta_bytes': bm_tok['total_bytes'] - cell['token_best']['total_bytes'],
                        }

                        # Export headline verified dictionaries for primary/secondary s1-whole L=16 uncapped K in {256, 1024, 4096}
                        if dict_export_dir is not None and policy == 's1-whole' and B is None and K in PRIMARY_SLOTS:
                            dict_export_dir.mkdir(parents=True, exist_ok=True)
                            to_export = {
                                f'{split_name}_K{K}_A_tm': get_shared_entries(a_row, L),
                                f'{split_name}_K{K}_B_tm': get_shared_entries(b_row, L),
                                f'{split_name}_K{K}_tokbest': get_shared_entries(tok_row, L),
                            }
                            if c_row is not None:
                                to_export[f'{split_name}_K{K}_C_py_tm'] = [r[4] for r in chain_cache[(c_row['python_policy'], L, 'python', c_row['python_arm'])][: c_row['python_entries']]]
                                to_export[f'{split_name}_K{K}_C_js_tm'] = [r[4] for r in chain_cache[(c_row['javascript_policy'], L, 'javascript', c_row['javascript_arm'])][: c_row['javascript_entries']]]
                            if best_bm_A['arm'] != a_row['arm'] or best_bm_A['entries'] != a_row['entries']:
                                if best_bm_A['arm'] == 'union':
                                    to_export[f'{split_name}_K{K}_A_bm'] = union_pt['_union_entries']
                                else:
                                    to_export[f'{split_name}_K{K}_A_bm'] = [r[4] for r in chain_cache[(best_bm_A['source_policy'], L, 'both', best_bm_A['arm'])][: best_bm_A['entries']]]
                            if best_bm_B['arm'] != b_row['arm'] or best_bm_B['entries'] != b_row['entries']:
                                if best_bm_B['arm'] == 'union':
                                    to_export[f'{split_name}_K{K}_B_bm'] = union_pt['_union_entries']
                                else:
                                    to_export[f'{split_name}_K{K}_B_bm'] = [r[4] for r in chain_cache[(best_bm_B['source_policy'], L, 'both', best_bm_B['arm'])][: best_bm_B['entries']]]

                            for name, elist in to_export.items():
                                p = dict_export_dir / f'{name}.hex'
                                content = '\n'.join(e.hex() for e in elist) + '\n'
                                p.write_text(content, encoding='utf-8')
                                exported_dicts[name] = {
                                    'path': str(p.relative_to(HERE)),
                                    'entries': len(elist),
                                    'dict_bytes': sum(1 + len(e) for e in elist),
                                    'sha256': hashlib.sha256(content.encode('utf-8')).hexdigest(),
                                }

                    cells.append(cell)

    # Information-theoretic KL / Jensen-Shannon decomposition across feasible K in SLOTS (s1-whole, L=16, uncapped)
    kl_by_k = []
    for K in SLOTS:
        cell_k = next(c for c in cells if c['policy'] == 's1-whole' and c['L'] == 16 and c['K'] == K and c['B'] is None)
        b_meta = cell_k['B_design']
        if b_meta is None:
            continue
        if b_meta['arm'] == 'union':
            c_row = cell_k['C']
            union_pt = build_union_entries('s1-whole', 16, c_row, K)
            elist = union_pt['_union_entries']
        else:
            elist = [r[4] for r in chain_cache[(b_meta['source_policy'], 16, 'both', b_meta['arm'])][: b_meta['entries']]]
        root = BE.build_trie(elist)
        decomp = kl_decomp_from_docs(py_docs, js_docs, root, len(elist))
        decomp['K'] = K
        decomp['arm'] = b_meta['arm']
        decomp['entries'] = len(elist)
        kl_by_k.append(decomp)

    # Corpus-size crossover curve at K=4096 (using the winning K=4096 Design B dictionary across
    # nested prefixes of N_pairs in {5, 10, 20, 40, 60, 100, 150, 200} problems, showing exact
    # crossover where I(Symbol; Language)/8 crosses |D| + 5!)
    kl_crossover_n = []
    cell_4096 = next(c for c in cells if c['policy'] == 's1-whole' and c['L'] == 16 and c['K'] == 4096 and c['B'] is None)
    b4096 = cell_4096['B_design']
    if b4096['arm'] == 'union':
        u4096 = build_union_entries('s1-whole', 16, cell_4096['C'], 4096)
        elist_4096 = u4096['_union_entries']
    else:
        elist_4096 = [r[4] for r in chain_cache[(b4096['source_policy'], 16, 'both', b4096['arm'])][: b4096['entries']]]
    root_4096 = BE.build_trie(elist_4096)
    for n_pairs in (5, 10, 20, 40, 60, 100, 150, len(py_docs)):
        d = kl_decomp_from_docs(py_docs[:n_pairs], js_docs[:n_pairs], root_4096, len(elist_4096))
        d['n_pairs'] = n_pairs
        d['raw_bytes'] = sum(len(x) for x in py_docs[:n_pairs]) + sum(len(x) for x in js_docs[:n_pairs])
        kl_crossover_n.append(d)

    # Real wall-clock encode/decode benchmarks on headline K in {256, 1024, 4096}
    runtime_benchmarks = []
    if split_name == 'primary':
        for K in PRIMARY_SLOTS:
            cell_k = next(c for c in cells if c['policy'] == 's1-whole' and c['L'] == 16 and c['K'] == K and c['B'] is None)
            b_meta = cell_k['B_design']
            a_meta = cell_k['A']
            c_meta = cell_k['C']
            if b_meta['arm'] == 'union':
                elist_b = build_union_entries('s1-whole', 16, c_meta, K)['_union_entries']
            else:
                elist_b = [r[4] for r in chain_cache[(b_meta['source_policy'], 16, 'both', b_meta['arm'])][: b_meta['entries']]]
            if a_meta['arm'] == 'union':
                elist_a = build_union_entries('s1-whole', 16, c_meta, K)['_union_entries']
            else:
                elist_a = [r[4] for r in chain_cache[(a_meta['source_policy'], 16, 'both', a_meta['arm'])][: a_meta['entries']]]

            ba_tm = BE.benchmark_encode_decode(both_docs, elist_a, mode='token_min', repeats=5)
            ba_bm = BE.benchmark_encode_decode(both_docs, elist_a, mode='byte_min', repeats=5)
            bp_tm = BE.benchmark_encode_decode(py_docs, elist_b, mode='token_min', repeats=5)
            bj_tm = BE.benchmark_encode_decode(js_docs, elist_b, mode='token_min', repeats=5)
            bp_bm = BE.benchmark_encode_decode(py_docs, elist_b, mode='byte_min', repeats=5)
            bj_bm = BE.benchmark_encode_decode(js_docs, elist_b, mode='byte_min', repeats=5)
            raw_total = ba_tm['raw_bytes']
            b_enc_tm = bp_tm['encode_median_ms'] + bj_tm['encode_median_ms']
            b_enc_bm = bp_bm['encode_median_ms'] + bj_bm['encode_median_ms']
            b_dec_tm = bp_tm['decode_median_ms'] + bj_tm['decode_median_ms']
            b_dec_bm = bp_bm['decode_median_ms'] + bj_bm['decode_median_ms']
            runtime_benchmarks.append({
                'K': K,
                'raw_bytes': raw_total,
                'A': {
                    'raw_bytes': raw_total,
                    'encode_token_min_ms': ba_tm['encode_median_ms'],
                    'encode_token_min_MB_s': ba_tm['encode_mb_per_s'],
                    'encode_byte_min_ms': ba_bm['encode_median_ms'],
                    'encode_byte_min_MB_s': ba_bm['encode_mb_per_s'],
                    'decode_token_min_ms': ba_tm['decode_median_ms'],
                    'decode_token_min_MB_s': ba_tm['decode_mb_per_s'],
                    'decode_byte_min_ms': ba_bm['decode_median_ms'],
                    'decode_byte_min_MB_s': ba_bm['decode_mb_per_s'],
                    'payload_token_min_bytes': ba_tm['payload_bytes'],
                    'payload_byte_min_bytes': ba_bm['payload_bytes'],
                    'roundtrip_verified': ba_tm['verified_exact'] and ba_bm['verified_exact'],
                },
                'B': {
                    'raw_bytes': raw_total,
                    'encode_token_min_ms': b_enc_tm,
                    'encode_token_min_MB_s': (raw_total / 1e6) / (b_enc_tm / 1000.0),
                    'encode_byte_min_ms': b_enc_bm,
                    'encode_byte_min_MB_s': (raw_total / 1e6) / (b_enc_bm / 1000.0),
                    'decode_token_min_ms': b_dec_tm,
                    'decode_token_min_MB_s': (raw_total / 1e6) / (b_dec_tm / 1000.0),
                    'decode_byte_min_ms': b_dec_bm,
                    'decode_byte_min_MB_s': (raw_total / 1e6) / (b_dec_bm / 1000.0),
                    'payload_token_min_bytes': bp_tm['payload_bytes'] + bj_tm['payload_bytes'],
                    'payload_byte_min_bytes': bp_bm['payload_bytes'] + bj_bm['payload_bytes'],
                    'roundtrip_verified': bp_tm['verified_exact'] and bj_tm['verified_exact'] and bp_bm['verified_exact'] and bj_bm['verified_exact'],
                },
            })

    return {
        'split': split_name,
        'lengths': list(lengths),
        'cells': cells,
        'kl_by_k': kl_by_k,
        'kl_crossover_n': kl_crossover_n,
        'runtime_benchmarks': runtime_benchmarks,
        'exported_dictionaries': exported_dicts,
    }


def main():
    manifest_path = HERE / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest_sha = sha256_file(manifest_path)

    build_dir = HERE / 'build'
    chains_dir = HERE / 'chains'
    results_dir = HERE / 'results'
    dict_dir = HERE / 'dictionaries'
    results_dir.mkdir(parents=True, exist_ok=True)

    engine_bin, engine_sha = compile_engine(build_dir)
    print(f'Compiled engine.c (sha256={engine_sha[:12]}...)', flush=True)

    jobs = []
    # Primary split: L in (8, 16, 32); Secondary split: L = 16
    split_specs = [('primary', (16, 8, 32)), ('secondary', (16,))]
    for split, lengths in split_specs:
        lists_dir = HERE / 'lists' / split
        for L in lengths:
            for policy in POLICIES:
                for corpus in ('both', 'python', 'javascript'):
                    receipt = f'manifest={manifest_sha} split={split} pool={corpus} cuts=none impl={engine_sha} run=codenet-v1'
                    for arm in ARMS:
                        jobs.append((engine_bin, split, policy, arm, L, corpus, lists_dir, chains_dir, receipt))

    print(f'Launching {len(jobs)} equal-budget engine jobs...', flush=True)
    t0 = time.perf_counter()
    workers = min(8, os.cpu_count() or 4)
    total_cpu_s = 0.0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for path, dt in ex.map(run_single_engine_job, jobs):
            total_cpu_s += dt
    print(f'Completed {len(jobs)} engine jobs in {time.perf_counter() - t0:.1f}s wall ({total_cpu_s:.1f}s sum)', flush=True)

    out = {
        'schema': 'gamma.bits-codenet-replication-results.v1',
        'manifest_sha256': manifest_sha,
        'engine_c_sha256': engine_sha,
        'splits': {},
    }
    for split, lengths in split_specs:
        ts = time.perf_counter()
        print(f'Scoring split={split} (lengths={lengths}) including byte-min DP & KL/JS decomposition...', flush=True)
        out['splits'][split] = analyze_split(split, lengths, manifest, chains_dir, dict_export_dir=dict_dir)
        print(f'Finished scoring {split} in {time.perf_counter() - ts:.1f}s', flush=True)

    out_path = results_dir / 'codenet_results.json'
    out_path.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {out_path}', flush=True)

    # Print concise headline verification summary
    for split in ('primary', 'secondary'):
        print(f'\n=== HEADLINE {split.upper()} (s1-whole, L=16, uncapped) ===')
        for K in PRIMARY_SLOTS:
            c = next(x for x in out['splits'][split]['cells'] if x['policy'] == 's1-whole' and x['L'] == 16 and x['K'] == K and x['B'] is None)
            bm = c['byte_min']
            c_tm_str = f"{c['C']['total_bytes']:7d}" if c['C'] else ' INFEAS'
            c_bm_str = f"{bm['C']['total_bytes']:7d}" if bm['C'] else ' INFEAS'
            print(
                f"K={K:4d} [tok-min] A={c['A']['total_bytes']:7d} ({c['A']['arm']}:{c['A']['entries']}) | "
                f"B={c['B_design']['total_bytes']:7d} ({c['B_design']['arm']}:{c['B_design']['entries']}) | "
                f"C={c_tm_str} | tokbest={c['token_best']['total_bytes']:7d}"
            )
            print(
                f"K={K:4d} [byt-min] A={bm['A']['total_bytes']:7d} ({bm['A']['arm']}:{bm['A']['entries']}) | "
                f"B={bm['B_design']['total_bytes']:7d} ({bm['B_design']['arm']}:{bm['B_design']['entries']}) | "
                f"C={c_bm_str} | tokbest={bm['token_best']['total_bytes']:7d} | rev={bm['winner_reversed']}"
            )


if __name__ == '__main__':
    main()
