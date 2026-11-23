#!/usr/bin/env python3
"""The race of PREREGISTRATION.md: the deficit hierarchy against the shortest-path Lagrangian baseline on two
unseen sets. Python 3.10+; set B needs numpy and the pinned packages on disk.

    python3 -B race.py --run-a                      set A; writes measurements-a.json
    python3 -B race.py --run-b --source ID=PATH ... set B; writes measurements-b.json
    python3 -B race.py [--source ID=PATH ...]       re-derives every answer from the measurements, replays every
                                                    dictionary; with sources it also recomputes the set B ranks.
                                                    Writes results.json
    python3 -B race.py --verify                     the same re-derivation for set A, compared with results.json, which
                                                    is left as it is (added after the run, for the reproduction bundle)
    python3 -B race.py --one ...                    one child call, printed as JSON (used by the runs)

Witness rule, threshold 2, entries of at most 160 bytes, no whole file. Every arm call is its own process.
"""
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import random
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
SHA_A = '89b020c6ee4a39fb547021db20af13a3a12be06f17a094455a7e67eb6a9a0ecc'
SHA_B = '7e9941e3d085d29c8830cf27412f0efdd655253fe3f629527d2d1b9ce474a9a4'
SEED = 'capacity-deficit-race-v1/2026-11-22'
ARM_SECONDS = 600                      # set A: wall limit of each arm on one family
B_BASELINE_SECONDS, B_HARD_SECONDS, B_MEMORY_KB = 300.0, 420, 8 * 1024 * 1024
B_PREFIXES = (4, 16, 64, 256)
FIELDS = ((1_000_000_007, 2), (998_244_353, 3))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def frozen(name, sha):
    raw = open(os.path.join(HERE, name), 'rb').read()
    if hashlib.sha256(raw).hexdigest() != sha:
        raise SystemExit(f'FAILED: {name} is not the frozen file')
    return json.loads(raw)['corpora']


def boundary_tools():
    sys.path.insert(0, os.path.join(ROOT, 'capacity-boundary-v1'))
    import capped
    import evaluate
    return evaluate, capped.Capped()


def baseline_module():
    return load('canzar_lagrangian', os.path.join(ROOT, 'capacity-lagrangian-race-v1', 'canzar_lagrangian.py'))


# ---------------------------------------------------------------- set A

def one_a(key, arm):
    programs = frozen('instances-a.json', SHA_A)[key]['programs']
    started = time.perf_counter()
    if arm == 'rank':
        evaluate, _ = boundary_tools()
        out = {'alphabet': len(set(''.join(programs))), 'blockRank': evaluate.block_rank(programs)}
    elif arm in ('hierarchy', 'level0'):
        deficit = load('deficit', os.path.join(ROOT, 'capacity-deficit-v1', 'deficit.py'))
        r = deficit.analyze(programs, 'W2') if arm == 'hierarchy' else deficit.analyze(programs, 'W2', class_limit=0)
        out = {k: r.get(k) for k in ('rank', 'nullity', 'lowerBound', 'dictionary', 'levelOne', 'note', 'lines')}
    elif arm == 'second':
        independent = load('independent_kernel', os.path.join(ROOT, 'capacity-kernel-audit-v1', 'independent_kernel.py'))
        r = independent.test(programs)
        out = {k: r.get(k) for k in ('status', 'rank', 'lowerBound', 'dictionary')}
    else:                                              # baseline: ascend from the block rank until a dictionary is returned
        evaluate, _ = boundary_tools()
        baseline = baseline_module()
        budget = lower = evaluate.block_rank(programs)
        calls, upper, multi = [], None, None
        while True:
            left = ARM_SECONDS - (time.perf_counter() - started)
            if left <= 1:
                break
            r = baseline.canzar_lagrangian_decide(programs, 2, budget, timeout_s=min(300.0, left))
            calls.append({'budget': budget, 'status': r['status'], 'phase': r.get('phase'), 'certifiedLowerBound': r.get('certifiedLowerBound'),
                          'iterations': r.get('iterations'), 'elapsedMs': r.get('elapsedMs')})
            if r['status'] == 'FEASIBLE':
                upper, multi = budget, r.get('dictionaryMulti') or []
                break
            if r['status'] != 'IMPOSSIBLE':
                break
            lower = max(budget + 1, r.get('certifiedLowerBound') or 0)
            budget = lower
        out = {'lowerBound': lower, 'upper': upper, 'dictionaryMulti': multi, 'calls': calls}
    out['seconds'] = round(time.perf_counter() - started, 3)
    return out


def call(args, limit, memory_kb=None):
    started = time.time()
    proc = subprocess.Popen([sys.executable, '-B', os.path.abspath(__file__), '--one'] + [str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    peak = 0
    while True:
        try:
            stdout, stderr = proc.communicate(timeout=2)
            break
        except subprocess.TimeoutExpired:
            if memory_kb is not None:
                seen = subprocess.run(['ps', '-o', 'rss=', '-p', str(proc.pid)], capture_output=True, text=True).stdout.strip()
                peak = max(peak, int(seen or 0))
                if peak > memory_kb:
                    proc.kill()
                    proc.communicate()
                    return {'status': 'MEMORY', 'seconds': round(time.time() - started, 1), 'note': f'killed above {memory_kb // 1024 // 1024} GB resident'}
            if time.time() - started > limit:
                proc.kill()
                proc.communicate()
                return {'status': 'TIMEOUT', 'seconds': round(time.time() - started, 1), 'note': f'killed after {limit} s', 'peakResidentKb': peak or None}
    if proc.returncode != 0:
        return {'status': 'ERROR', 'seconds': round(time.time() - started, 1), 'note': stderr[-400:]}
    out = json.loads(stdout)
    if peak:
        out['peakResidentKb'] = peak
    return out


def run_family(key):
    rank = call(['a', key, 'rank'], ARM_SECONDS)
    row = {'rank': rank}
    if rank.get('blockRank') is not None and rank['blockRank'] < rank['alphabet']:
        row['hierarchy'] = call(['a', key, 'hierarchy'], ARM_SECONDS)
        if row['hierarchy'].get('status') in ('TIMEOUT', 'ERROR'):
            row['level0'] = call(['a', key, 'level0'], ARM_SECONDS)
        row['second'] = call(['a', key, 'second'], ARM_SECONDS)
        row['baseline'] = call(['a', key, 'baseline'], ARM_SECONDS + 60)
    print(key, {arm: {k: v for k, v in r.items() if k in ('alphabet', 'blockRank', 'lowerBound', 'upper', 'levelOne', 'note', 'status', 'seconds')} for arm, r in row.items()}, flush=True)
    return key, row


def run_a():
    keys = sorted(frozen('instances-a.json', SHA_A))
    with concurrent.futures.ThreadPoolExecutor(3) as pool:
        out = dict(pool.map(run_family, keys))
    with open(os.path.join(HERE, 'measurements-a.json'), 'w') as f:
        json.dump({'schema': 'capacity-deficit-race-measurements-a/v1', 'armSeconds': ARM_SECONDS, 'parallelFamilies': 3, 'corpora': {k: out[k] for k in keys}}, f, indent=1)
        f.write('\n')


# ---------------------------------------------------------------- set B

def sources():
    return dict(arg.split('=', 1) for flag, arg in zip(sys.argv[1:], sys.argv[2:]) if flag == '--source')


def load_b(key, root, prefix=None):
    c = frozen('instances-b.json', SHA_B)[key]
    texts = []
    for f in c['files']:
        raw = open(os.path.join(root, *f['path'].split('/')), 'rb').read()
        if hashlib.sha256(raw).hexdigest() != f['sha256']:
            raise SystemExit(f"FAILED: {key} {f['path']} is not the pinned file")
        texts.append(raw.decode('utf-8'))
    texts = sorted(set(texts))
    if prefix is not None:
        random.Random(f'{SEED}/B/{key}').shuffle(texts)
        texts = sorted(texts[:prefix])
    return texts


def block_rank_numpy(programs):
    """Forced blocks and their rank in two prime fields; stops early at full rank. Returns (alphabet, rank, blocks)."""
    import numpy as np
    owners = {}
    for n, p in enumerate(programs):
        for window in {p[i:i + 2] for i in range(len(p) - 1)}:
            seen = owners.setdefault(window, set())
            if len(seen) < 2:
                seen.add(n)
    blocks = set()
    for p in programs:
        start = 0
        for i in range(len(p) - 1):
            if len(owners[p[i:i + 2]]) < 2:
                blocks.add(p[start:i + 1])
                start = i + 1
        blocks.add(p[start:])
    letters = sorted(set(''.join(programs)))
    column, width, best = {c: n for n, c in enumerate(letters)}, len(letters), 0
    for prime, base in FIELDS:
        basis, pivots = np.zeros((0, width), dtype=np.int64), []
        for b in sorted(blocks, key=lambda x: (len(x), x)):
            v, weight = np.zeros(width, dtype=np.int64), 1
            for ch in b:
                v[column[ch]] = (v[column[ch]] + weight) % prime
                weight = weight * base % prime
            for row, pivot in zip(basis, pivots):
                if v[pivot]:
                    v = (v - v[pivot] * row) % prime
            nonzero = np.nonzero(v)[0]
            if len(nonzero) == 0:
                continue
            pivot = int(nonzero[0])
            v = v * pow(int(v[pivot]), prime - 2, prime) % prime
            for i, row in enumerate(basis):
                if row[pivot]:
                    basis[i] = (row - row[pivot] * v) % prime
            basis = np.vstack([basis, v])
            pivots.append(pivot)
            if len(pivots) == width:
                break
        best = max(best, len(pivots))
        if best == width:
            break
    return width, best, len(blocks)


def one_b(key, arm, prefix, root):
    prefix = None if prefix == 'all' else int(prefix)
    started = time.perf_counter()
    programs = load_b(key, root, prefix)
    loaded = time.perf_counter()
    size = {'files': len(programs), 'bytes': sum(len(p.encode()) for p in programs)}
    if arm == 'rank':
        alphabet, rank, blocks = block_rank_numpy(programs)
        out = dict(size, alphabet=alphabet, blockRank=rank, blocks=blocks)
    elif arm == 'hierarchy':
        deficit = load('deficit', os.path.join(ROOT, 'capacity-deficit-v1', 'deficit.py'))
        r = deficit.analyze(programs, 'W2')
        out = dict(size, **{k: r.get(k) for k in ('rank', 'nullity', 'lowerBound', 'dictionary', 'levelOne', 'note', 'lines')})
    else:                                              # baseline asked to refute one entry fewer than the block rank
        _, rank, _ = block_rank_numpy(programs)
        ranked = time.perf_counter()
        r = baseline_module().canzar_lagrangian_decide(programs, 2, rank - 1, timeout_s=B_BASELINE_SECONDS)
        out = dict(size, budget=rank - 1, status=r['status'], phase=r.get('phase'), certifiedLowerBound=r.get('certifiedLowerBound'), iterations=r.get('iterations'),
                   arcs=r.get('numArcs'), entries=r.get('numTokens'), baselineSeconds=round(time.perf_counter() - ranked, 3))
    out['seconds'] = round(time.perf_counter() - loaded, 3)
    return out


def run_directory(item):
    key, root, count = item
    row = {'rank': {}, 'baseline': {}}
    sizes = [n for n in B_PREFIXES if n < count] + ['all']
    for n in sizes:
        row['rank'][str(n)] = call(['b', key, 'rank', n, root], 600)
    refuting = True
    for n in sizes:
        if not refuting:
            break
        r = call(['b', key, 'baseline', n, root], B_HARD_SECONDS, B_MEMORY_KB)
        row['baseline'][str(n)] = r
        refuting = r.get('status') == 'IMPOSSIBLE'
    full = row['rank']['all']
    if full.get('blockRank') is not None and full['blockRank'] < full['alphabet']:
        row['hierarchy'] = call(['b', key, 'hierarchy', 'all', root], ARM_SECONDS, B_MEMORY_KB)
    print(key, json.dumps({arm: ({n: {k: v for k, v in r.items() if k in ('files', 'bytes', 'alphabet', 'blockRank', 'status', 'phase', 'seconds', 'note')} for n, r in rows.items()}
                                 if arm != 'hierarchy' else {k: v for k, v in rows.items() if k != 'dictionary'}) for arm, rows in row.items()}), flush=True)
    return key, row


def run_b():
    roots, corpora = sources(), frozen('instances-b.json', SHA_B)
    items = [(key, roots[c['source']], len(c['files'])) for key, c in sorted(corpora.items())]
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        out = dict(pool.map(run_directory, items))
    with open(os.path.join(HERE, 'measurements-b.json'), 'w') as f:
        json.dump({'schema': 'capacity-deficit-race-measurements-b/v1', 'baselineSeconds': B_BASELINE_SECONDS, 'hardSeconds': B_HARD_SECONDS,
                   'memoryKb': B_MEMORY_KB, 'parallelDirectories': 2, 'corpora': {k: out[k] for k in sorted(out)}}, f, indent=1)
        f.write('\n')


# ---------------------------------------------------------------- check

def fewest_singles(programs, multi, rule):
    eligible = {programs[n][i:j] for n, i, j in rule.occurrences(programs)}
    text = ''.join(programs)
    dictionary = sorted({t for t in multi if t in eligible}) + sorted(set(text))
    for c in sorted(set(text), key=lambda ch: (text.count(ch), ch)):
        rest = [d for d in dictionary if d != c]
        if rule.dictionary_spells(programs, rest):
            dictionary = rest
    return dictionary


def replay_direct(programs, dictionary, cap=160):
    """The same rule as the capped checker, tested entry by entry instead of by listing every eligible substring,
    which does not finish on megabytes. Added after the run; see RESULTS.md."""
    whole = set(programs)
    if len(set(dictionary)) != len(dictionary):
        return False
    for e in dictionary:
        if e in whole or not e:
            return False
        if len(e) > 1:
            if len(e.encode()) > cap:
                return False
            holders = 0
            for p in programs:
                if e in p:
                    holders += 1
                    if holders == 2:
                        break
            if holders < 2:
                return False
    table = {}
    for e in dictionary:
        table.setdefault(e[0], []).append(e)
    for p in programs:
        reach = [True] + [False] * len(p)
        for i in range(len(p)):
            if reach[i]:
                for e in table.get(p[i], ()):
                    if p.startswith(e, i):
                        reach[i + len(e)] = True
        if not reach[len(p)]:
            return False
    return True


def check():
    evaluate, rule = boundary_tools()
    failures, rows_a = [], []
    measured = json.load(open(os.path.join(HERE, 'measurements-a.json')))['corpora']
    for key, c in sorted(frozen('instances-a.json', SHA_A).items()):
        programs, m = c['programs'], measured[key]
        alphabet, rank = len(set(''.join(programs))), evaluate.block_rank(programs)
        if rank != m['rank'].get('blockRank'):
            failures.append(f'{key}: block rank recomputed {rank}, measured {m["rank"].get("blockRank")}')
        row = {'corpus': key, 'source': c['source'], 'files': len(programs), 'bytes': sum(f['bytes'] for f in c['files']), 'alphabet': alphabet, 'blockRank': rank, 'nullity': alphabet - rank}
        if rank == alphabet:
            row.update(minimum=[rank, rank], settledBy='rank')
            rows_a.append(row)
            continue
        arms = {}
        h = m.get('hierarchy', {})
        if h.get('status') in ('TIMEOUT', 'ERROR'):
            h = dict(m.get('level0', {}), timedOut=True)
        d = h.get('dictionary')
        if d is not None and not rule.dictionary_spells(programs, d):
            failures.append(f'{key}: the hierarchy dictionary does not replay')
            d = None
        if h.get('rank') is not None and h['rank'] != rank:
            failures.append(f'{key}: hierarchy rank {h["rank"]}, recomputed {rank}')
        lower = max(rank, h.get('lowerBound') or rank)
        upper = min(alphabet, len(d)) if d is not None else alphabet
        level = 0 if h.get('note') == 'rank attained' else 1
        arms['hierarchy'] = {'interval': [lower, upper], 'exact': lower == upper, 'level': level if lower == upper else None, 'levelOne': h.get('levelOne'),
                             'note': h.get('note'), 'lines': h.get('lines'), 'seconds': m.get('hierarchy', {}).get('seconds'), 'timedOut': bool(h.get('timedOut'))}
        s = m.get('second', {})
        if s.get('status') in ('RANK_ATTAINED', 'RANK_UNATTAINABLE') and s.get('lowerBound') is not None:
            first_says = 'RANK_ATTAINED' if h.get('note') == 'rank attained' else ('RANK_UNATTAINABLE' if lower > rank else None)
            if first_says is not None and first_says != s['status']:
                failures.append(f'{key}: level 0 says {first_says}, the second implementation says {s["status"]}')
        arms['second'] = {'status': s.get('status'), 'seconds': s.get('seconds')}
        b = m.get('baseline', {})
        b_lower = max(rank, b.get('lowerBound') or rank)
        b_upper = alphabet
        if b.get('upper') is not None:
            rebuilt = fewest_singles(programs, b.get('dictionaryMulti') or [], rule)
            if rule.dictionary_spells(programs, rebuilt) and len(rebuilt) <= b['upper']:
                b_upper = min(alphabet, len(rebuilt))
            elif b['upper'] >= alphabet:
                b_upper = alphabet
            else:
                failures.append(f'{key}: the baseline dictionary of {b["upper"]} entries was not rebuilt (got {len(rebuilt)})')
        arms['baseline'] = {'interval': [b_lower, b_upper], 'exact': b_lower == b_upper, 'calls': [(x['budget'], x['status'], x.get('phase')) for x in b.get('calls', [])],
                            'seconds': b.get('seconds'), 'status': b.get('status')}
        best_lower, best_upper = max(lower, b_lower), min(upper, b_upper)
        if best_lower > best_upper:
            failures.append(f'{key}: arms contradict each other: hierarchy {lower}..{upper}, baseline {b_lower}..{b_upper}')
        row.update(arms=arms, minimum=[best_lower, best_upper],
                   settledBy=[arm for arm in ('hierarchy', 'baseline') if arms[arm]['exact']])
        rows_a.append(row)

    rows_b = []
    path_b = os.path.join(HERE, 'measurements-b.json')
    if os.path.exists(path_b):
        measured_b = json.load(open(path_b))['corpora']
        roots = sources()
        for key, c in sorted(frozen('instances-b.json', SHA_B).items()):
            m = measured_b[key]
            full = m['rank']['all']
            row = {'corpus': key, 'source': c['source'], 'subtree': c['subtree'], 'files': full.get('files'), 'bytes': full.get('bytes'), 'alphabet': full.get('alphabet'),
                   'blockRank': full.get('blockRank'), 'rankSeconds': full.get('seconds'),
                   'prefixNullity': {n: (r['alphabet'] - r['blockRank'] if r.get('blockRank') is not None else None) for n, r in m['rank'].items()},
                   'baseline': {n: {'files': r.get('files'), 'bytes': r.get('bytes'), 'status': r.get('status'), 'phase': r.get('phase'), 'seconds': r.get('seconds'),
                                    'arcs': r.get('arcs'), 'peakResidentKb': r.get('peakResidentKb')} for n, r in m['baseline'].items()}}
            if c['source'] in roots:
                alphabet, rank, _ = block_rank_numpy(load_b(key, roots[c['source']]))
                row['rankRecomputed'] = (alphabet, rank) == (full.get('alphabet'), full.get('blockRank'))
                if not row['rankRecomputed']:
                    failures.append(f'{key}: rank recomputed {rank} of {alphabet}, measured {full.get("blockRank")} of {full.get("alphabet")}')
            h = m.get('hierarchy')
            if h is not None:
                row['hierarchy'] = {k: v for k, v in h.items() if k != 'dictionary'}
                row['hierarchy']['dictionaryEntries'] = None if h.get('dictionary') is None else len(h['dictionary'])
                if h.get('dictionary') is not None and c['source'] in roots:
                    replays = replay_direct(load_b(key, roots[c['source']]), h['dictionary'])
                    row['hierarchy']['dictionaryReplays'] = replays
                    if not replays:
                        failures.append(f'{key}: the hierarchy dictionary does not replay')
            rows_b.append(row)

    deficient = [r for r in rows_a if r['nullity'] > 0]
    both = [r for r in deficient if r['arms']['hierarchy']['exact'] and r['arms']['baseline']['exact']]
    ratios = sorted(r['arms']['baseline']['seconds'] / max(r['arms']['hierarchy']['seconds'], 1e-3) for r in both)
    summary = {
        'familiesWithDeficit': len(deficient), 'families': len(rows_a),
        'hierarchyExact': sum(1 for r in deficient if r['arms']['hierarchy']['exact']),
        'levelZeroExact': sum(1 for r in deficient if r['arms']['hierarchy']['level'] == 0),
        'levelOneExact': sum(1 for r in deficient if r['arms']['hierarchy']['level'] == 1),
        'baselineExact': sum(1 for r in deficient if r['arms']['baseline']['exact']),
        'onlyHierarchy': [r['corpus'] for r in deficient if r['arms']['hierarchy']['exact'] and not r['arms']['baseline']['exact']],
        'onlyBaseline': [r['corpus'] for r in deficient if r['arms']['baseline']['exact'] and not r['arms']['hierarchy']['exact']],
        'medianBaselineOverHierarchySeconds': None if not ratios else round(ratios[len(ratios) // 2] if len(ratios) % 2 else (ratios[len(ratios) // 2 - 1] + ratios[len(ratios) // 2]) / 2, 2),
        'directoriesSaturated': sum(1 for r in rows_b if r['blockRank'] is not None and r['blockRank'] == r['alphabet']), 'directories': len(rows_b),
    }
    if '--verify' in sys.argv:                 # compare with the stored results instead of rewriting them
        kept = json.load(open(os.path.join(HERE, 'results.json')))
        if json.loads(json.dumps(rows_a)) != kept['setA']:
            failures.append('set A re-derived from the measurements differs from results.json')
        if any(summary[k] != kept['summary'][k] for k in summary if k not in ('directoriesSaturated', 'directories')):
            failures.append('the set A summary differs from results.json')
        if kept['failures']:
            failures.append('results.json records failures')
    else:
        with open(os.path.join(HERE, 'results.json'), 'w') as f:
            json.dump({'schema': 'capacity-deficit-race-results/v1', 'summary': summary, 'setA': rows_a, 'setB': rows_b, 'failures': failures}, f, indent=1)
            f.write('\n')
    for r in rows_a:
        if r['nullity'] == 0:
            print(f"{r['corpus']} {r['source']:14} alphabet {r['alphabet']:3} rank {r['blockRank']:3}  saturated")
        else:
            h, b = r['arms']['hierarchy'], r['arms']['baseline']
            print(f"{r['corpus']} {r['source']:14} alphabet {r['alphabet']:3} rank {r['blockRank']:3}  hierarchy {h['interval']} level {h['level']} {h['seconds']} s | baseline {b['interval']} {b['seconds']} s | {h['note']}")
    for r in rows_b:
        print(f"{r['corpus']} {r['source']:14} files {r['files']} bytes {r['bytes']} alphabet {r['alphabet']} rank {r['blockRank']} in {r['rankSeconds']} s; baseline "
              + ', '.join(f"{n}: {x['status']} {x['seconds']} s" for n, x in r['baseline'].items()))
    print(json.dumps(summary))
    for failure in failures:
        print('FAILED:', failure)
    return 1 if failures else 0


if __name__ == '__main__':
    if '--one' in sys.argv:
        args = sys.argv[sys.argv.index('--one') + 1:]
        print(json.dumps(one_a(*args[1:]) if args[0] == 'a' else one_b(*args[1:])))
    elif '--run-a' in sys.argv:
        run_a()
    elif '--run-b' in sys.argv:
        run_b()
    else:
        sys.exit(check())
