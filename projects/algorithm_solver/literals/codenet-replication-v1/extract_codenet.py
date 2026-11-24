#!/usr/bin/env python3
"""Deterministically extract the frozen public IBM Project CodeNet paired Python/JS corpora.

Retrieves Parquet shards from Hugging Face `iNeil77/CodeNet` (mirror of IBM Project
CodeNet v1.0.0, CDLA-Permissive-2.0) one shard at a time into a temporary directory
and deletes each shard immediately after processing so disk footprint stays minimal.

Frozen selection rule (executed BEFORE any dictionary search):
  1. Filter to `status == 'Accepted'`, valid UTF-8, zero NUL bytes, and raw UTF-8
     byte length in [64, 4096].
  2. Language filter:
     - Python: Python 3 runtimes only (`Python (3.8.2)`, `Python (3.4.3)`, `Python3`,
       `PyPy3 (7.3.0)`, `PyPy3 (2.4.0)`, `Python (3.4.2)`).
     - JavaScript: all Node.js / JS runtimes (`JavaScript (Node.js 12.16.1)`,
       `JavaScript (node.js v5.12)`, `JavaScript`).
  3. Find all overlapping problems `p_id` with >= 1 eligible Python 3 and >= 1
     eligible JavaScript submission.
  4. Order eligible overlapping `p_id` by `SHA-256("bits-codenet-replication-v1:" + p_id)`.
     - Ranks 0..199   -> `primary`   (200 paired problems, 400 files)
     - Ranks 200..399 -> `secondary` (200 disjoint paired problems, 400 files)
  5. Within each selected `(p_id, language)`, sort all eligible submissions by
     `(len(raw_bytes), s_id)` and pick the lower-median submission
     `eligible[(len(eligible) - 1) // 2]`.
"""
import hashlib
import json
import os
import tempfile
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.parquet as pq

REPO_ID = 'iNeil77/CodeNet'
API_URL = f'https://huggingface.co/api/datasets/{REPO_ID}'
BASE_URL = f'https://huggingface.co/datasets/{REPO_ID}/resolve'
SEED_PREFIX = 'bits-codenet-replication-v1:'
MIN_BYTES = 64
MAX_BYTES = 4096
PRIMARY_N = 200
SECONDARY_N = 200

PY3_LANGS = {
    'Python (3.8.2)',
    'Python (3.4.3)',
    'Python3',
    'PyPy3 (7.3.0)',
    'PyPy3 (2.4.0)',
    'Python (3.4.2)',
}
JS_LANGS = {
    'JavaScript (Node.js 12.16.1)',
    'JavaScript (node.js v5.12)',
    'JavaScript',
}


def get_dataset_revision():
    req = urllib.request.Request(API_URL, headers={'User-Agent': 'bits-codenet-replication/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        meta = json.loads(resp.read().decode('utf-8'))
    return meta.get('sha', 'main')


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def rank_key(p_id):
    return hashlib.sha256((SEED_PREFIX + p_id).encode('utf-8')).hexdigest()


def download_shard(revision, relpath, tmpdir):
    url = f'{BASE_URL}/{revision}/{relpath}'
    dst = os.path.join(tmpdir, os.path.basename(relpath))
    urllib.request.urlretrieve(url, dst)
    return dst


def main():
    out_dir = Path(__file__).resolve().parent
    corpus_dir = out_dir / 'corpus'
    revision = get_dataset_revision()
    print(f'Pinned {REPO_ID} revision: {revision}', flush=True)

    # Pass 1: JavaScript (single 27 MB shard) - collect eligible metadata (size, s_id) AND
    # hold code only after we know selected problems, OR since JS is only 25k accepted rows,
    # scan metadata first across JS + PY, pick exact 400 p_ids, then extract codes!
    # Wait: holding JS accepted codes for ~25k rows is ~20 MB RAM, whereas Python is 1.8M rows!
    # So we do:
    #   (a) Download JS once: collect ALL eligible JS (len, s_id, orig_lang, u_id, raw_bytes) per p_id.
    #       (25,223 accepted rows * ~800 B avg = ~20 MB RAM - super tiny!)
    #   (b) Stream Python shards 0..3: for every row whose p_id is in JS eligible set, record
    #       (len(raw_bytes), s_id, shard_idx, row_idx) in RAM (only for p_ids in JS eligible set,
    #       and pick only the 400 selected problems in a single pass? Wait: we don't know which
    #       p_ids are in the top 400 until all 4 Python shards are scanned because a problem can
    #       appear in shard 3! Wait: if we store ONLY `(len, s_id)` for Python rows whose `p_id`
    #       is in `js_eligible`, how many rows is that? ~1.1M tuples = ~60 MB RAM. Then we pick the
    #       exact 400 `(p_id, s_id)` targets and do a fast second read? No, downloading 560 MB twice
    #       wastes bandwidth! Instead, wait: each Python shard is grouped by problem range or mixed?
    #       Actually we saw cum_p grow 1850 -> 2082 -> 2416 -> 3080, so problems CAN span shards,
    #       OR we can keep the exact raw bytes ONLY for problems in the top-450 of ALL `js_eligible`
    #       problems! THINK ABOUT THAT!
    #       Because `rank_key(p_id)` depends ONLY on `p_id`, if we sort `js_eligible` by `rank_key(p_id)`
    #       FIRST, only the first ~450 problems in `js_eligible` can POSSIBLY be in the top 400
    #       overlapping problems (since 1,764 / 1,771 = 99.6% of JS problems have Python solutions!).
    #       Keeping Python eligible submissions for only the top 500 `js_eligible` problems is
    #       ~500/3000 * 1.8M? Even simpler: keep a reservoir or just store `(len, s_id, u_id, ol, raw)`
    #       only for the top 450 `js_eligible` p_ids — wait: 450/3080 of 1.79M is ~260k strings (~80 MB).
    #       Even better: we only need the exact median of eligible submissions per p_id; 260k short
    #       strings in Python is ~150 MB RAM, completely fine on Mac with 16+ GB RAM! Let's check:
    #       keeping top 440 `js_eligible` p_ids (400 needed + 40 buffer) is tiny and guarantees ONE
    #       single streaming pass over the 4 Python shards!

    with tempfile.TemporaryDirectory() as td:
        js_path = download_shard(revision, 'JavaScript/train-00000-of-00001.parquet', td)
        js_table = pq.read_table(
            js_path,
            columns=['s_id', 'p_id', 'u_id', 'original_language', 'status', 'code'],
        )
        os.remove(js_path)

        js_total_rows = js_table.num_rows
        js_accepted_rows = 0
        js_orig_langs = Counter()
        js_eligible = defaultdict(list)
        js_all_accepted_p = set()

        for s_id, p_id, u_id, ol, st, code in zip(
            js_table['s_id'].to_pylist(),
            js_table['p_id'].to_pylist(),
            js_table['u_id'].to_pylist(),
            js_table['original_language'].to_pylist(),
            js_table['status'].to_pylist(),
            js_table['code'].to_pylist(),
        ):
            if st != 'Accepted':
                continue
            js_accepted_rows += 1
            js_orig_langs[ol] += 1
            js_all_accepted_p.add(p_id)
            if ol not in JS_LANGS or not isinstance(code, str):
                continue
            raw = code.encode('utf-8')
            if MIN_BYTES <= len(raw) <= MAX_BYTES and b'\x00' not in raw:
                js_eligible[p_id].append((len(raw), s_id, u_id, ol, raw))

        del js_table
        js_ranked = sorted(js_eligible.keys(), key=rank_key)
        candidate_set = set(js_ranked[: PRIMARY_N + SECONDARY_N + 60])
        print(
            f'JS scanned: rows={js_total_rows}, accepted={js_accepted_rows}, '
            f'eligible_p={len(js_eligible)}, candidate_buffer={len(candidate_set)}',
            flush=True,
        )

        # Stream Python shards 0..3 ONCE:
        # Track full overlap statistics across all 3080 problems, AND retain eligible raw codes
        # ONLY for p_id in candidate_set.
        py_total_rows = 0
        py_accepted_rows = 0
        py_orig_langs = Counter()
        py_all_accepted_p = set()
        py3_eligible_p = set()
        py_candidates = defaultdict(list)

        for idx in range(4):
            rel = f'Python/train-0000{idx}-of-00004.parquet'
            py_path = download_shard(revision, rel, td)
            py_table = pq.read_table(
                py_path,
                columns=['s_id', 'p_id', 'u_id', 'original_language', 'status', 'code'],
            )
            os.remove(py_path)

            py_total_rows += py_table.num_rows
            for s_id, p_id, u_id, ol, st, code in zip(
                py_table['s_id'].to_pylist(),
                py_table['p_id'].to_pylist(),
                py_table['u_id'].to_pylist(),
                py_table['original_language'].to_pylist(),
                py_table['status'].to_pylist(),
                py_table['code'].to_pylist(),
            ):
                if st != 'Accepted':
                    continue
                py_accepted_rows += 1
                py_orig_langs[ol] += 1
                py_all_accepted_p.add(p_id)
                if ol not in PY3_LANGS or not isinstance(code, str):
                    continue
                raw = code.encode('utf-8')
                if MIN_BYTES <= len(raw) <= MAX_BYTES and b'\x00' not in raw:
                    py3_eligible_p.add(p_id)
                    if p_id in candidate_set:
                        py_candidates[p_id].append((len(raw), s_id, u_id, ol, raw))

            del py_table
            print(
                f'PY shard {idx} scanned: cum_rows={py_total_rows}, cum_acc={py_accepted_rows}, '
                f'py3_eligible_p={len(py3_eligible_p)}, cand_matched={len(py_candidates)}',
                flush=True,
            )

    overlap_any_accepted = sorted(js_all_accepted_p & py_all_accepted_p)
    overlap_eligible_all = sorted(set(js_eligible.keys()) & py3_eligible_p, key=rank_key)
    needed = PRIMARY_N + SECONDARY_N
    selected_all = overlap_eligible_all[:needed]
    assert len(selected_all) == needed, f'Expected {needed} overlapping problems, got {len(selected_all)}'
    missing = [p for p in selected_all if p not in py_candidates]
    assert not missing, f'Candidate buffer missed {len(missing)} problems! Increase buffer.'

    splits = {
        'primary': selected_all[:PRIMARY_N],
        'secondary': selected_all[PRIMARY_N : PRIMARY_N + SECONDARY_N],
    }

    manifest_splits = {}
    for split_name, pids in splits.items():
        py_dir = corpus_dir / split_name / 'python'
        js_dir = corpus_dir / split_name / 'javascript'
        py_dir.mkdir(parents=True, exist_ok=True)
        js_dir.mkdir(parents=True, exist_ok=True)

        entries = []
        py_bytes_total = 0
        js_bytes_total = 0
        for problem_idx, p_id in enumerate(pids):
            py_pool = sorted(py_candidates[p_id], key=lambda r: (r[0], r[1]))
            js_pool = sorted(js_eligible[p_id], key=lambda r: (r[0], r[1]))
            py_pick = py_pool[(len(py_pool) - 1) // 2]
            js_pick = js_pool[(len(js_pool) - 1) // 2]

            py_rel = f'corpus/{split_name}/python/{p_id}_{py_pick[1]}.py'
            js_rel = f'corpus/{split_name}/javascript/{p_id}_{js_pick[1]}.js'
            (out_dir / py_rel).write_bytes(py_pick[4])
            (out_dir / js_rel).write_bytes(js_pick[4])
            py_bytes_total += py_pick[0]
            js_bytes_total += js_pick[0]

            entries.append({
                'problem_index': problem_idx,
                'p_id': p_id,
                'rank_sha256': rank_key(p_id),
                'python': {
                    'path': py_rel,
                    's_id': py_pick[1],
                    'u_id': py_pick[2],
                    'original_language': py_pick[3],
                    'bytes': py_pick[0],
                    'sha256': sha256_bytes(py_pick[4]),
                    'eligible_pool_size': len(py_pool),
                },
                'javascript': {
                    'path': js_rel,
                    's_id': js_pick[1],
                    'u_id': js_pick[2],
                    'original_language': js_pick[3],
                    'bytes': js_pick[0],
                    'sha256': sha256_bytes(js_pick[4]),
                    'eligible_pool_size': len(js_pool),
                },
            })

        # Write deterministic file lists & problem-group side files for engine.c
        lists_dir = out_dir / 'lists' / split_name
        lists_dir.mkdir(parents=True, exist_ok=True)
        py_paths = [str((out_dir / e['python']['path']).resolve()) for e in entries]
        js_paths = [str((out_dir / e['javascript']['path']).resolve()) for e in entries]
        (lists_dir / 'python.txt').write_text('\n'.join(py_paths) + '\n')
        (lists_dir / 'javascript.txt').write_text('\n'.join(js_paths) + '\n')
        (lists_dir / 'both.txt').write_text('\n'.join(py_paths + js_paths) + '\n')

        # Group indices for p2-nowhole: problem_index 0..N-1 for python, same 0..N-1 for javascript
        py_groups = [str(i) for i in range(len(entries))]
        js_groups = [str(i) for i in range(len(entries))]
        (lists_dir / 'python.groups').write_text(' '.join(py_groups) + '\n')
        (lists_dir / 'javascript.groups').write_text(' '.join(js_groups) + '\n')
        (lists_dir / 'both.groups').write_text(' '.join(py_groups + js_groups) + '\n')

        manifest_splits[split_name] = {
            'problems': len(entries),
            'files': 2 * len(entries),
            'python_bytes': py_bytes_total,
            'javascript_bytes': js_bytes_total,
            'total_bytes': py_bytes_total + js_bytes_total,
            'pairs': entries,
        }

    manifest = {
        'schema': 'gamma.bits-codenet-replication-manifest.v1',
        'source_dataset': 'IBM Project CodeNet v1.0.0',
        'source_mirror': REPO_ID,
        'source_revision': revision,
        'license': 'CDLA-Permissive-2.0',
        'selection_rule': {
            'seed_prefix': SEED_PREFIX,
            'order': 'ascending SHA-256(seed_prefix + p_id)',
            'status': 'Accepted',
            'min_bytes': MIN_BYTES,
            'max_bytes': MAX_BYTES,
            'forbid_nul': True,
            'python_original_languages': sorted(PY3_LANGS),
            'javascript_original_languages': sorted(JS_LANGS),
            'per_problem_pick': 'lower-median by (byte_length, s_id)',
            'primary_ranks': [0, PRIMARY_N - 1],
            'secondary_ranks': [PRIMARY_N, PRIMARY_N + SECONDARY_N - 1],
        },
        'population_verification': {
            'javascript_total_rows': js_total_rows,
            'javascript_accepted_rows': js_accepted_rows,
            'javascript_accepted_problems': len(js_all_accepted_p),
            'javascript_eligible_problems': len(js_eligible),
            'javascript_original_languages': dict(js_orig_langs),
            'python_total_rows': py_total_rows,
            'python_accepted_rows': py_accepted_rows,
            'python_accepted_problems': len(py_all_accepted_p),
            'python3_eligible_problems': len(py3_eligible_p),
            'python_original_languages': dict(py_orig_langs),
            'overlap_any_accepted_problems': len(overlap_any_accepted),
            'overlap_eligible_py3_js_problems': len(overlap_eligible_all),
        },
        'splits': manifest_splits,
    }

    manifest_path = out_dir / 'manifest.json'
    manifest_bytes = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
    manifest_path.write_bytes(manifest_bytes)
    print(f'Wrote {manifest_path} (sha256={sha256_bytes(manifest_bytes)})')
    for split_name, info in manifest_splits.items():
        print(
            f'  {split_name}: {info["problems"]} pairs ({info["files"]} files), '
            f'py={info["python_bytes"]} B, js={info["javascript_bytes"]} B, '
            f'total={info["total_bytes"]} B'
        )


if __name__ == '__main__':
    main()
