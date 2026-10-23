"""palette-names-v1: per-binding naming with a multi-character palette under exact literal cost (FREEZE.md).

  palette.py --work DIR --output DIR/palette-names/run-v1

Starts from item 13's selected scope_joint256 dictionary and fit sources. Arms (256 entries): seed (no search),
az_fixed (item 13's scope policy, a-z targets, fixed dictionary: the matched control), palette_fixed (a-z plus at
most 40 multi-character palette names), az_joint and palette_joint (each plus the shared local dictionary search; the
matched joint pair). Every final source is reparsed; a parse failure fails the run (no repair). Lexical capture
constraints, reflection guards and rendering come unchanged from binding-descent-v1/rewrite.py. Validation (after the
fit seal) chooses original R or the seed text by exact cost, then runs two calls of the arm's naming policy under the
sealed dictionary. Changed final sources not already qualified by exact hash are run on every pinned case.
"""
import argparse, concurrent.futures, hashlib, json, keyword, multiprocessing, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(LIT / 'binding-descent-v1'), str(LIT / 'cost-decomposition-v1'), str(LIT / 'tail-search-v1')]
import rewrite, analyze
import search as tail

sha = lambda raw: hashlib.sha256(raw).hexdigest()
IDENT = re.compile(r'^[A-Za-z_$][A-Za-z0-9_$]*$')
JS_RESERVED = set('''break case catch class const continue debugger default delete do else enum export extends false finally for
function if import in instanceof new null return super switch this throw true try typeof var void while with yield let static
implements interface package private protected public await async of get set arguments eval undefined NaN Infinity solve
Math Number String Array Object JSON Map Set WeakMap WeakSet Symbol BigInt Boolean Date RegExp Error console globalThis
window global self Function Promise Reflect Proxy parseInt parseFloat isNaN isFinite constructor prototype'''.split())
ARMS = ('seed', 'az_fixed', 'palette_fixed', 'az_joint', 'palette_joint')


def contract():
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    return c


def build_palette(vocab, fit_records, cap, max_len):
    """Identifier-shaped learned dictionary entries first (longest first, then text), then binding spellings shared by at
    least two fit programs (most owners first, then text). Never keywords, literals, arguments/eval, solve or builtins."""
    ok = lambda s: IDENT.match(s) and 2 <= len(s) <= max_len and s not in JS_RESERVED and not keyword.iskeyword(s)
    learned = sorted({s for s in vocab if len(s) > 1 and ok(s)}, key=lambda s: (-len(s), s))
    owners = {}
    for pid, rec in fit_records.items():
        for v in rec.get('variables', []):
            if ok(v['name']): owners.setdefault(v['name'], set()).add(pid)
    mined = sorted((s for s, o in owners.items() if len(o) >= 2 and s not in learned), key=lambda s: (-len(owners[s]), s))
    return (learned + mined)[:cap]


def optimize(text, record, vocab, names, sweeps, max_trials):
    """binding-descent-v1 scope-mode coordinate descent with `names` as the single-binding target set (pair swaps as before)."""
    if not text.isascii() or record['unsafe']:
        return text, {'trials': 0, 'moves': 0, 'stop': 'unsupported', 'multichar_names_introduced': 0}
    variables = record['variables']; colors = [v['name'] for v in variables]
    assert rewrite.legal(record, colors)
    units = [[v['id']] for v in variables if v['eligible']]
    units.sort(key=lambda ids: (-sum(len(variables[i]['spans']) for i in ids), min(ids)))
    tree = rewrite.codec.trie(vocab); score = lambda t: len(rewrite.codec.encode_text(t, tree))
    current, cost, trials, moves, stop = text, score(text), 0, 0, 'sweep_limit'
    for sweep in range(sweeps):
        changed = False
        for unit in units:
            best, seen = None, set()

            def trial(proposal):
                nonlocal trials, best
                key = tuple(proposal)
                if trials >= max_trials or key in seen or key == tuple(colors): return
                seen.add(key)
                if not rewrite.legal(record, proposal): return
                candidate = rewrite.render(text, record, proposal); value = score(candidate); trials += 1
                order = (value, len(candidate.encode()), candidate)
                if value < cost and (best is None or order < best[0]): best = (order, proposal, candidate)
            for name in names:
                proposal = list(colors)
                for i in unit: proposal[i] = name
                trial(proposal)
            for other in units:
                if other is unit or colors[other[0]] == colors[unit[0]]: continue
                proposal = list(colors)
                for i in unit: proposal[i] = colors[other[0]]
                for i in other: proposal[i] = colors[unit[0]]
                trial(proposal)
            if best is not None:
                order, colors, current = best; cost = order[0]; moves += 1; changed = True
            if trials >= max_trials: stop = 'trial_limit'; break
        if trials >= max_trials: break
        if not changed: stop = 'local_coordinate_stop'; break
    original = {v['name'] for v in variables}
    return current, {'trials': trials, 'moves': moves, 'stop': stop,
                     'multichar_names_introduced': sum(len(c) > 1 and c not in original for c in set(colors))}


def rewrite_all(texts, vocab, names, limits):
    records = rewrite.records(texts); out, stats = {}, {}
    for pid, text in sorted(texts.items()):
        out[pid], stats[str(pid)] = optimize(text, records[str(pid)], vocab, names, limits['sweeps'], limits['trials'])
    return out, stats


def banned_strings(groups):
    out = set()
    for texts in groups:
        structure = tail.source_structure(texts)
        out |= set(texts.values()) | {b for r in structure.values() for b in r['bodies']}
    return out


def arm(job):
    os.environ['PYTHONHASHSEED'] = '0'
    name, work, out = job['arm'], Path(job['work']), Path(job['output'])
    os.sched_setaffinity(0, set(job['cores']))
    c = contract(); parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text())
    fit_ids, val_ids = parent['partition']['dev_fit'], parent['partition']['dev_val']
    seedf = work / c['seed']['relative_path']
    for f, h in c['seed']['private_sha256'].items(): assert sha((seedf / f).read_bytes()) == h, f
    vocab = json.loads((seedf / 'dictionary.json').read_text())
    seed_fit = {int(k): v for k, v in json.loads((seedf / 'fit-sources.json').read_text()).items()}
    original_fit = analyze.load_sources(work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(fit_ids)]})
    variants = {pid: {'original': original_fit[pid], 'seed': seed_fit[pid]} for pid in fit_ids}
    m = tail.module(f'palette_style_{name}', LIT / 'style150-v2/measure.py'); v3 = m.v3
    state = v3.evaluate(variants, vocab, 8, None, v3.Budget({'trials': 1, 'seconds': 60}))
    selected = {pid: variants[pid][state['chosen'][pid]] for pid in fit_ids}
    rounds, names_per_round, started = [], [], time.monotonic()
    if name != 'seed':
        for round_no in range(2):
            names = list('abcdefghijklmnopqrstuvwxyz')
            if name.startswith('palette'):
                names += [s for s in build_palette(vocab, rewrite.records(selected), c['palette']['cap'], c['palette']['max_length']) if s not in names]
            names_per_round.append(sha(json.dumps(names).encode()))
            candidates, stats = rewrite_all(selected, vocab, names, c['rewrite'])
            for pid, text in candidates.items(): variants[pid][f'r{round_no}'] = text
            banned = banned_strings([{pid: v[k] for pid, v in variants.items() if k in v} for k in next(iter(variants.values()))])
            budget = v3.Budget(c['search']); log = []; stop = 'fixed_dictionary'
            state = v3.evaluate(variants, vocab, 8, None, budget)
            if name.endswith('_joint'):
                proposer = m.hybrid_chosen([], variants)
                safe = lambda s, st, limit, fraction: [x for x in proposer(s, st, limit, fraction) if x not in banned]
                state, _ = v3.refill(variants, state, 8, safe, c['neighborhood'], 24, budget)
                state, stop = v3.local_search(variants, state, 8, safe, c['neighborhood'], budget, log)
            assert not set(state['vocab']) & banned
            vocab = state['vocab']; selected = {pid: variants[pid][state['chosen'][pid]] for pid in fit_ids}
            rounds.append({'round': round_no, 'palette_size': len(names) - 26, 'fit_selections': state['selections'], 'search_trials': budget.trials,
                           'stop': stop, 'rewrite': {k: sum(s[k] for s in stats.values()) for k in ('trials', 'moves', 'multichar_names_introduced')}})
            print(json.dumps({'arm': name, **rounds[-1]}), flush=True)
    folder = out / name; folder.mkdir(parents=True)
    analyze.write(folder / 'dictionary.json', vocab); analyze.write(folder / 'fit-sources.json', {str(k): v for k, v in selected.items()})
    # The validation palette is fixed now, from the sealed dictionary and the selected fit sources only.
    final_names = list('abcdefghijklmnopqrstuvwxyz')
    if name.startswith('palette'):
        final_names += [s for s in build_palette(vocab, rewrite.records(selected), c['palette']['cap'], c['palette']['max_length']) if s not in final_names]
    analyze.write(folder / 'palette.json', final_names)
    analyze.write(folder / 'fit-seal.json', {'validation_loaded': False, 'dictionary_sha256': sha((folder / 'dictionary.json').read_bytes()),
                                              'fit_sources_sha256': sha((folder / 'fit-sources.json').read_bytes()),
                                              'palette_sha256': sha((folder / 'palette.json').read_bytes())})
    # Validation is opened only now: original R or the seed text by exact cost, then two calls of this arm's policy.
    seed_all = json.loads((seedf / 'sources.json').read_text())
    original_val = analyze.load_sources(work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(val_ids)]})
    tree = rewrite.codec.trie(vocab); cost = lambda t: len(rewrite.codec.encode_text(t, tree))
    validation = {pid: min((original_val[pid], seed_all[str(pid)]), key=lambda t: (cost(t), len(t.encode()), t)) for pid in val_ids}
    val_stats = []
    if name != 'seed':
        for _ in range(2):
            validation, stats = rewrite_all(validation, vocab, final_names, c['rewrite'])
            val_stats.append({k: sum(s[k] for s in stats.values()) for k in ('trials', 'moves', 'multichar_names_introduced')})
    all_sources = {**selected, **validation}
    banned = banned_strings([all_sources]) | {t for v in variants.values() for t in v.values()}  # acorn reparses every final source here
    rows = {}
    db = analyze.dictionary_bytes(vocab)
    for pid, text in sorted(all_sources.items()):
        seq = analyze.shortest_encode(text, vocab); packet = analyze.encode(vocab, seq, 8)
        assert analyze.decode(db, packet) == text
        rows[str(pid)] = {'selections': len(seq), 'actions': len(seq) + 1, 'single_characters': sum(len(vocab[i]) == 1 for i in seq),
                          'packet_bytes': len(packet), 'source_bytes': len(text.encode()), 'source_sha256': sha(text.encode())}
    analyze.write(folder / 'sources.json', {str(k): v for k, v in all_sources.items()})
    result = {'arm': name, 'entries': len(vocab), 'dictionary_bytes': len(db), 'dictionary_sha256': sha((folder / 'dictionary.json').read_bytes()),
              'illegal_entry_sha256': sorted(sha(s.encode()) for s in set(vocab) & banned), 'rounds': rounds, 'palette_sha256': names_per_round,
              'validation_rewrite': val_stats, 'per_problem': rows, 'seconds': time.monotonic() - started}
    analyze.write(folder / 'results.json', result)
    return result


def qualify(work, out, c, results):
    """Fresh strict parity only for final changed (id, hash) pairs not already qualified by exact hash in the pinned receipts."""
    known = set()
    for rel in c['qualified_receipts']:
        ev = json.loads((LIT / rel).read_text())
        for a in ev['arms']:
            for pid, q in a['qualification'].items():
                if q['passed']: known.add((pid, a['per_problem'][pid]['source_sha256']))
    parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text())
    original = {str(r['id']): r['sha256'] for r in parent['sources']}
    minify = tail.module('palette_minify', LIT / 'minify-control-v1/minify.py')
    manifest = json.loads((work / 'population500/manifest.json').read_text())
    specs = {str(r['id']): r for r in manifest['rows']}
    jobs = {}
    for a in results:
        texts = json.loads((out / a['arm'] / 'sources.json').read_text())
        for pid, row in a['per_problem'].items():
            key = (pid, row['source_sha256'])
            if row['source_sha256'] != original[pid] and key not in known: jobs[key] = texts[pid]
    receipts, failures = {}, {}
    with concurrent.futures.ProcessPoolExecutor(4) as pool:
        futs = {pool.submit(minify.style.parity, minify.shim(work), int(pid), text, 'solve', specs[pid], None): (pid, h) for (pid, h), text in jobs.items()}
        for f in concurrent.futures.as_completed(futs):
            pid, h = futs[f]; passed, ok, n, bad = f.result()
            receipts[f'{pid}:{h}'] = {'passed': passed, 'checks_passed': ok, 'cases': n}
            if bad: failures[f'{pid}:{h}'] = bad  # every failure detail is kept, privately
            analyze.write(out / 'qualification-private.json', {'receipts': receipts, 'failures': failures})
    for a in results:
        a['qualification'] = {}
        for pid, row in a['per_problem'].items():
            key = (pid, row['source_sha256'])
            if row['source_sha256'] == original[pid]: a['qualification'][pid] = {'passed': True, 'reused': 'original'}
            elif key in known: a['qualification'][pid] = {'passed': True, 'reused': 'pinned receipt'}
            else: a['qualification'][pid] = {**receipts[f'{pid}:{row["source_sha256"]}'], 'reused': False}
        a['qualified'] = sum(q['passed'] for q in a['qualification'].values())
    return len(jobs)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args(); c = contract(); a.output.mkdir(parents=True, exist_ok=False); started = time.monotonic()
    jobs = [{'arm': n, 'work': str(a.work.resolve()), 'output': str(a.output.resolve()), 'cores': c['cores'][n]} for n in ARMS]
    with concurrent.futures.ProcessPoolExecutor(4, mp_context=multiprocessing.get_context('spawn')) as pool:
        results = list(pool.map(arm, jobs))
    analyze.write(a.output / 'unqualified-results.json', results)
    fresh = qualify(a.work, a.output, c, results)
    analyze.write(a.output / 'results.json', {'arms': results, 'fresh_qualification_jobs': fresh, 'seconds': time.monotonic() - started,
                                              'contract_sha256': sha((HERE / 'contract.json').read_bytes())})
    print(json.dumps({'complete': True, 'fresh_jobs': fresh, 'qualified': {r['arm']: r['qualified'] for r in results}}), flush=True)


if __name__ == '__main__':
    main()
