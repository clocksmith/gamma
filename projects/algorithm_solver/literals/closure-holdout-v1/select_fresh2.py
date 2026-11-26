#!/usr/bin/env python3
"""Select `fresh2`: 200 CodeNet problems that no earlier BITS set has used.
Run by the scorer after the dictionaries are frozen, never by the trainer.

    python3 -I select_fresh2.py --work WORKDIR

The rule is the objective-holdout-v1 `fresh` rule (imported unchanged from
select_fresh_codenet.py) continued past the last `fresh` rank, with priors
widened to primary, secondary and fresh:
  1. skip a problem in the same IBM identical-problem cluster as any prior or
     already-taken problem;
  2. skip a problem whose chosen Python or JavaScript file equals a prior or
     already-taken file exactly or after removing all whitespace;
  3. skip a problem whose chosen file, in either language, has 8-byte shingle
     Jaccard >= 0.8 with any prior file of that language. (This replaces the
     IBM Python near-duplicate list, which is not in the repository; it applies
     the same screen to both languages.)
Needs pyarrow and network access to the pinned Hugging Face mirror.
Writes corpus/codenet-fresh2/ and sets/fresh2.json.
"""
import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LITERALS = HERE.parent
OH = LITERALS / 'objective-holdout-v1'
sys.path.insert(0, str(OH))
import select_fresh_codenet as F  # noqa: E402

FRESH2_PROBLEMS = 200
BUFFER_PROBLEMS = 2000
NEAR = 0.8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    args = ap.parse_args()
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    if F.sha256(F.CLUSTERS_FILE.read_bytes()) != F.CLUSTERS_SHA256:
        raise SystemExit('identical-problem cluster file changed')
    cluster_of = {}
    for line in F.CLUSTERS_FILE.read_text().split():
        members = frozenset(line.split(','))
        for p in members:
            cluster_of[p] = members

    manifest = json.loads((F.CODENET / 'manifest.json').read_text())
    prior_pairs = manifest['splits']['primary']['pairs'] + manifest['splits']['secondary']['pairs']
    prior = []  # (p_id, lang, raw)
    for pair in prior_pairs:
        for lang in ('python', 'javascript'):
            raw = (F.CODENET / pair[lang]['path']).read_bytes()
            if F.sha256(raw) != pair[lang]['sha256']:
                raise SystemExit('prior corpus hash mismatch')
            prior.append((pair['p_id'], lang, raw))
    fresh = json.loads((OH / 'sets' / 'fresh.json').read_text())
    for f in fresh['files']:
        raw = (OH / f['path']).read_bytes()
        if F.sha256(raw) != f['sha256']:
            raise SystemExit('fresh corpus hash mismatch')
        prior.append((f['unit'], f['lang'], raw))
    prior_problems = list(dict.fromkeys(p for p, _, _ in prior))
    start_rank = fresh['selection']['last_rank'] + 1

    js = defaultdict(list)
    for s_id, p_id, u_id, ol, st, code in F.rows(F.fetch('JavaScript/train-00000-of-00001.parquet', work)):
        if st == 'Accepted' and ol in F.JS_LANGS:
            raw = F.eligible(code)
            if raw is not None:
                js[p_id].append((len(raw), s_id, u_id, ol, raw))
    js_ranked = sorted(js, key=F.rank_key)
    buffer = set(js_ranked[:BUFFER_PROBLEMS])
    py = defaultdict(list)
    py_eligible = set()
    for idx in range(4):
        for s_id, p_id, u_id, ol, st, code in F.rows(F.fetch(f'Python/train-0000{idx}-of-00004.parquet', work)):
            if st == 'Accepted' and ol in F.PY3_LANGS:
                raw = F.eligible(code)
                if raw is not None:
                    py_eligible.add(p_id)
                    if p_id in buffer:
                        py[p_id].append((len(raw), s_id, u_id, ol, raw))
        print(f'python shard {idx} read, {len(py)} buffered problems', flush=True)
    ranked = sorted(set(js) & py_eligible, key=F.rank_key)

    def pick(p_id, lang):
        pool = sorted(py[p_id] if lang == 'python' else js[p_id], key=lambda r: (r[0], r[1]))
        return pool[(len(pool) - 1) // 2], len(pool)

    # The ranking must reproduce every earlier selection before it is trusted.
    if ranked[:F.PRIOR_RANKS] != [p['p_id'] for p in prior_pairs]:
        raise SystemExit('ranks 0..399 do not reproduce the frozen primary and secondary problems')
    for f in fresh['files']:
        if ranked[f['rank']] != f['unit']:
            raise SystemExit('fresh ranks do not reproduce')
    print('primary, secondary and fresh ranks reproduce', flush=True)

    blocked = set()
    for p in prior_problems:
        blocked |= cluster_of.get(p, frozenset([p]))
    seen_exact = {F.sha256(raw) for _, _, raw in prior}
    seen_squeezed = {F.squeezed(raw) for _, _, raw in prior}
    prior_sh = {lang: [F.shingles(raw) for _, l, raw in prior if l == lang] for lang in ('python', 'javascript')}

    def near(raw, lang):
        a = F.shingles(raw)
        best = 0.0
        for b in prior_sh[lang]:
            u = len(a | b)
            if u:
                best = max(best, len(a & b) / u)
        return best

    chosen, skipped = [], []
    rank = start_rank
    while len(chosen) < FRESH2_PROBLEMS:
        if rank >= len(ranked):
            raise SystemExit('ran out of eligible problems')
        p_id = ranked[rank]
        rank += 1
        if p_id not in py:
            raise SystemExit('candidate buffer too small; raise BUFFER_PROBLEMS')
        if p_id in blocked:
            skipped.append({'rank': rank - 1, 'p_id': p_id, 'reason': 'identical-problem cluster'})
            continue
        picks = {lang: pick(p_id, lang) for lang in ('python', 'javascript')}
        raws = {lang: picks[lang][0][4] for lang in ('python', 'javascript')}
        if any(F.sha256(r) in seen_exact for r in raws.values()):
            skipped.append({'rank': rank - 1, 'p_id': p_id, 'reason': 'exact duplicate'})
            continue
        if any(F.squeezed(r) in seen_squeezed for r in raws.values()):
            skipped.append({'rank': rank - 1, 'p_id': p_id, 'reason': 'duplicate after removing whitespace'})
            continue
        sims = {lang: near(raws[lang], lang) for lang in raws}
        if any(s >= NEAR for s in sims.values()):
            skipped.append({'rank': rank - 1, 'p_id': p_id, 'reason': 'shingle Jaccard >= 0.8 with a prior file',
                            'jaccard': {k: round(v, 4) for k, v in sims.items()}})
            continue
        blocked |= cluster_of.get(p_id, frozenset([p_id]))
        for lang, r in raws.items():
            seen_exact.add(F.sha256(r))
            seen_squeezed.add(F.squeezed(r))
        chosen.append((rank - 1, p_id, picks, sims))

    files = []
    for lang, ext in (('python', 'py'), ('javascript', 'js')):
        out_dir = HERE / 'corpus' / 'codenet-fresh2' / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        for rk, p_id, picks, sims in chosen:
            (size, s_id, u_id, ol, raw), pool = picks[lang]
            rel = f'corpus/codenet-fresh2/{lang}/{p_id}_{s_id}.{ext}'
            (HERE / rel).write_bytes(raw)
            files.append({'path': rel, 'unit': p_id, 'lang': lang, 'bytes': size, 'sha256': F.sha256(raw),
                          's_id': s_id, 'u_id': u_id, 'original_language': ol, 'rank': rk,
                          'eligible_pool_size': pool, 'closest_prior_jaccard': round(sims[lang], 4)})
    out = {
        'set': 'fresh2',
        'source': 'IBM Project CodeNet v1.0.0 (CDLA-Permissive-2.0), mirror ' + F.REPO_ID + ' at ' + F.REVISION,
        'unit': 'CodeNet problem id; one problem per IBM identical-problem cluster',
        'selection': {
            'rule': 'objective-holdout-v1 fresh rule continued past the last fresh rank; priors primary, '
                    'secondary and fresh; rule 3 is an 8-byte shingle Jaccard screen in both languages',
            'identical_problem_clusters_sha256': F.CLUSTERS_SHA256,
            'first_rank': chosen[0][0], 'last_rank': chosen[-1][0], 'skipped': skipped,
        },
        'files': files,
    }
    (HERE / 'sets').mkdir(exist_ok=True)
    (HERE / 'sets' / 'fresh2.json').write_text(json.dumps(out, indent=1) + '\n')
    print(f'fresh2: {len(chosen)} problems, {len(files)} files, {sum(f["bytes"] for f in files)} bytes, '
          f'ranks {chosen[0][0]}..{chosen[-1][0]}, skipped {len(skipped)}')


if __name__ == '__main__':
    main()
