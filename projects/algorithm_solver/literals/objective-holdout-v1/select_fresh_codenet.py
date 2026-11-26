#!/usr/bin/env python3
"""Select the fresh CodeNet test problems. Run by the scorer, never by the trainer.

    python3 -I select_fresh_codenet.py --python-clusters FILE --work WORKDIR

The rule is the frozen codenet-replication-v1 rule continued past rank 399,
with three exclusions decided before any file is read:

  1. a problem in the same IBM identical-problem cluster as any problem of
     `primary` or `secondary`, or as a fresh problem already taken;
  2. a problem whose chosen Python or JavaScript file equals a `primary`,
     `secondary` or earlier fresh file exactly or after removing all
     whitespace;
  3. a problem whose chosen Python submission shares an IBM near-duplicate
     cluster with a `primary` or `secondary` Python submission. IBM publishes
     no JavaScript clusters, so JavaScript has rules 1 and 2 only.

Needs `pyarrow`. Writes corpus/codenet-fresh/ and sets/fresh.json.
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
LITERALS = HERE.parent
CODENET = LITERALS / 'codenet-replication-v1'

REPO_ID = 'iNeil77/CodeNet'
REVISION = '1e28cfa9f8eb2df763ad2514af11afd6e92dd07a'
BASE_URL = f'https://huggingface.co/datasets/{REPO_ID}/resolve/{REVISION}'
SEED_PREFIX = 'bits-codenet-replication-v1:'
MIN_BYTES, MAX_BYTES = 64, 4096
PRIOR_RANKS = 400
FRESH_PROBLEMS = 200
BUFFER_PROBLEMS = 900
SHINGLE = 8
PY3_LANGS = {'Python (3.8.2)', 'Python (3.4.3)', 'Python3', 'PyPy3 (7.3.0)', 'PyPy3 (2.4.0)', 'Python (3.4.2)'}
JS_LANGS = {'JavaScript (Node.js 12.16.1)', 'JavaScript (node.js v5.12)', 'JavaScript'}
CLUSTERS_FILE = HERE / 'metadata' / 'ibm-identical-problem-clusters.txt'
CLUSTERS_SHA256 = 'd4731781ef6314502446b6f365ba3f83e16c54ec888e214c5426e84835553520'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def rank_key(p_id):
    return sha256((SEED_PREFIX + p_id).encode())


def squeezed(raw):
    return sha256(b''.join(raw.split()))


def shingles(raw):
    return {raw[i:i + SHINGLE] for i in range(len(raw) - SHINGLE + 1)}


def fetch(rel, work):
    dst = work / rel.replace('/', '_')
    if not dst.exists():
        req = urllib.request.Request(f'{BASE_URL}/{rel}', headers={'User-Agent': 'generic-client/1.0'})
        tmp = dst.with_suffix('.part')
        with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, 'wb') as out:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
        os.replace(tmp, dst)
    return dst


def rows(path):
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(path)
    for batch in pf.iter_batches(batch_size=20000,
                                 columns=['s_id', 'p_id', 'u_id', 'original_language', 'status', 'code']):
        cols = [batch.column(i).to_pylist() for i in range(6)]
        yield from zip(*cols)


def eligible(code):
    if not isinstance(code, str):
        return None
    try:
        raw = code.encode('utf-8')
    except UnicodeEncodeError:
        return None
    if MIN_BYTES <= len(raw) <= MAX_BYTES and b'\x00' not in raw:
        return raw
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--python-clusters', required=True, help='IBM derived/duplicates/Python/Project_CodeNet-Python.clusters')
    ap.add_argument('--work', required=True)
    args = ap.parse_args()
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    if sha256(CLUSTERS_FILE.read_bytes()) != CLUSTERS_SHA256:
        raise SystemExit('identical-problem cluster file changed')
    cluster_of = {}
    for line in CLUSTERS_FILE.read_text().split():
        members = frozenset(line.split(','))
        for p in members:
            cluster_of[p] = members

    manifest = json.loads((CODENET / 'manifest.json').read_text())
    prior_pairs = manifest['splits']['primary']['pairs'] + manifest['splits']['secondary']['pairs']
    prior_problems = [p['p_id'] for p in prior_pairs]
    prior_files = {}
    for pair in prior_pairs:
        for lang in ('python', 'javascript'):
            raw = (CODENET / pair[lang]['path']).read_bytes()
            if sha256(raw) != pair[lang]['sha256']:
                raise SystemExit('prior corpus hash mismatch')
            prior_files[(pair['p_id'], lang)] = raw
    prior_python_sids = {pair['python']['s_id'] for pair in prior_pairs}

    # JavaScript first: it is one small shard and bounds the candidate problems.
    js = defaultdict(list)
    for s_id, p_id, u_id, ol, st, code in rows(fetch('JavaScript/train-00000-of-00001.parquet', work)):
        if st == 'Accepted' and ol in JS_LANGS:
            raw = eligible(code)
            if raw is not None:
                js[p_id].append((len(raw), s_id, u_id, ol, raw))
    js_ranked = sorted(js, key=rank_key)
    buffer = set(js_ranked[:BUFFER_PROBLEMS])
    py = defaultdict(list)
    py_eligible = set()
    for idx in range(4):
        for s_id, p_id, u_id, ol, st, code in rows(fetch(f'Python/train-0000{idx}-of-00004.parquet', work)):
            if st == 'Accepted' and ol in PY3_LANGS:
                raw = eligible(code)
                if raw is not None:
                    py_eligible.add(p_id)
                    if p_id in buffer:
                        py[p_id].append((len(raw), s_id, u_id, ol, raw))
        print(f'python shard {idx} read, {len(py)} buffered problems', flush=True)
    ranked = sorted(set(js) & py_eligible, key=rank_key)
    if any(p not in py for p in ranked[:PRIOR_RANKS]):
        raise SystemExit('candidate buffer too small')

    def pick(p_id, lang):
        pool = sorted(py[p_id] if lang == 'python' else js[p_id], key=lambda r: (r[0], r[1]))
        return pool[(len(pool) - 1) // 2], len(pool)

    # The rule must reproduce the frozen splits before it is trusted for new ranks.
    if ranked[:PRIOR_RANKS] != prior_problems:
        raise SystemExit('ranks 0..399 do not reproduce the frozen primary and secondary problems')
    for pair in prior_pairs:
        for lang in ('python', 'javascript'):
            (_, s_id, _, _, raw), _ = pick(pair['p_id'], lang)
            if s_id != pair[lang]['s_id'] or sha256(raw) != pair[lang]['sha256']:
                raise SystemExit(f'{pair["p_id"]} {lang}: frozen pick not reproduced')
    print('ranks 0..399 reproduce the frozen manifest exactly', flush=True)

    # IBM near-duplicate clusters for Python: keep only clusters that contain a prior submission.
    near_prior = set()
    group = []

    def flush():
        ids = {line.rsplit('/', 1)[-1].split('.', 1)[0] for line in group}
        if ids & prior_python_sids:
            near_prior.update(ids)

    with open(args.python_clusters, 'r', errors='replace') as fh:
        for line in fh:
            line = line.strip()
            if line:
                group.append(line.split(':', 1)[0])
            elif group:
                flush()
                group = []
        if group:
            flush()
    near_prior -= prior_python_sids

    blocked = set()
    for p in prior_problems:
        blocked |= cluster_of.get(p, frozenset([p]))
    seen_exact = {sha256(raw) for raw in prior_files.values()}
    seen_squeezed = {squeezed(raw) for raw in prior_files.values()}
    chosen = []
    skipped = []
    rank = PRIOR_RANKS
    while len(chosen) < FRESH_PROBLEMS:
        if rank >= len(ranked):
            raise SystemExit('ran out of eligible problems')
        p_id = ranked[rank]
        rank += 1
        if p_id not in py:
            raise SystemExit('candidate buffer too small; raise BUFFER_PROBLEMS')
        if p_id in blocked:
            skipped.append({'rank': rank - 1, 'p_id': p_id, 'reason': 'identical-problem cluster of a prior or fresh problem'})
            continue
        picks = {lang: pick(p_id, lang) for lang in ('python', 'javascript')}
        raws = [picks[lang][0][4] for lang in ('python', 'javascript')]
        if any(sha256(r) in seen_exact for r in raws):
            skipped.append({'rank': rank - 1, 'p_id': p_id, 'reason': 'exact duplicate of a prior or fresh file'})
            continue
        if any(squeezed(r) in seen_squeezed for r in raws):
            skipped.append({'rank': rank - 1, 'p_id': p_id, 'reason': 'duplicate of a prior or fresh file after removing whitespace'})
            continue
        if picks['python'][0][1] in near_prior:
            skipped.append({'rank': rank - 1, 'p_id': p_id, 'reason': 'IBM near-duplicate cluster of a prior Python submission'})
            continue
        blocked |= cluster_of.get(p_id, frozenset([p_id]))
        for r in raws:
            seen_exact.add(sha256(r))
            seen_squeezed.add(squeezed(r))
        chosen.append((rank - 1, p_id, picks))

    files = []
    for lang, ext in (('python', 'py'), ('javascript', 'js')):
        out_dir = HERE / 'corpus' / 'codenet-fresh' / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        for rk, p_id, picks in chosen:
            (size, s_id, u_id, ol, raw), pool = picks[lang]
            rel = f'corpus/codenet-fresh/{lang}/{p_id}_{s_id}.{ext}'
            (HERE / rel).write_bytes(raw)
            files.append({'path': rel, 'unit': p_id, 'lang': lang, 'bytes': size, 'sha256': sha256(raw),
                          's_id': s_id, 'u_id': u_id, 'original_language': ol, 'rank': rk, 'eligible_pool_size': pool})

    # Reported, not used for exclusion: closest training file by 8-byte shingle overlap.
    near = {}
    train = {(p['p_id'], lang): prior_files[(p['p_id'], lang)]
             for p in manifest['splits']['primary']['pairs'] for lang in ('python', 'javascript')}
    for lang in ('python', 'javascript'):
        train_sh = [shingles(raw) for (p, l), raw in train.items() if l == lang]
        best = []
        for f in files:
            if f['lang'] != lang:
                continue
            a = shingles((HERE / f['path']).read_bytes())
            best.append(max((len(a & b) / len(a | b) if a | b else 0.0) for b in train_sh))
        best.sort()
        near[lang] = {'median': round(best[len(best) // 2], 4), 'p95': round(best[int(0.95 * (len(best) - 1))], 4),
                      'max': round(best[-1], 4), 'files_at_or_above_0.8': sum(1 for x in best if x >= 0.8)}

    out = {
        'set': 'fresh',
        'source': 'IBM Project CodeNet v1.0.0 (CDLA-Permissive-2.0), mirror ' + REPO_ID + ' at ' + REVISION,
        'unit': 'CodeNet problem id; one problem per IBM identical-problem cluster',
        'selection': {
            'rule': 'codenet-replication-v1 ranking continued from rank 400, with the three exclusions in this file',
            'ranks_0_399_reproduce_frozen_manifest': True,
            'identical_problem_clusters_sha256': CLUSTERS_SHA256,
            'python_near_duplicate_clusters_sha256': sha256(Path(args.python_clusters).read_bytes()),
            'javascript_near_duplicate_clusters': 'not published by IBM',
            'eligible_overlap_problems': len(ranked),
            'first_rank': chosen[0][0],
            'last_rank': chosen[-1][0],
            'skipped': skipped,
            'closest_training_file_shingle_jaccard': near,
        },
        'files': files,
    }
    (HERE / 'sets').mkdir(exist_ok=True)
    (HERE / 'sets' / 'fresh.json').write_text(json.dumps(out, indent=1) + '\n')
    print(f'fresh: {len(chosen)} problems, {len(files)} files, {sum(f["bytes"] for f in files)} bytes, '
          f'ranks {chosen[0][0]}..{chosen[-1][0]}, skipped {len(skipped)}')
    print(json.dumps(near))


if __name__ == '__main__':
    main()
