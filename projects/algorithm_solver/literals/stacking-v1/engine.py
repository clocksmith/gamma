"""Pure source proposals and fit-only stack searches; no validation data loader."""
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import time
import coverage_search as weighted

HERE = Path(__file__).resolve().parent
LIT = HERE.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


base = module('stack_lns_engine', LIT / 'lns-naming-v1/engine.py')
slots = module('stack_slots', LIT / 'character-slots-v1/repair.py')
model = module('stack_seeded_model', LIT / 'seeded-repair-v1/model.py')
segment = module('stack_segment', LIT / 'segmentation-audit-v1/segment.py')
tail = module('stack_tail', LIT / 'tail-search-v1/search.py')
analyze = base.analyze
SOURCE_ARMS = ('N', 'NC', 'NP', 'NCP')
DEEP_ARMS = ('D00', 'D01', 'D10', 'D11')


def read(path):
    return json.loads(Path(path).read_text())


def digest(texts):
    return analyze.sha(json.dumps(texts, sort_keys=True, separators=(',', ':')).encode())


def normalized(groups):
    """Variant IDs sort exactly like source text, the final source-choice tie."""
    return {pid: {f'v{i:02d}': text for i, text in enumerate(sorted(set(texts)))}
            for pid, texts in groups.items()}


def forbidden(variants):
    flat = {f'{pid}:{name}': text for pid, vs in variants.items() for name, text in vs.items()}
    return base.sel.forbidden_strings(flat)


def propose_sources(original, seed, selected, prior, vocab, arm, cfg):
    """At most twelve source slots per program; all original/seed/prior choices retained."""
    compiler = 'P' in arm
    coupled = 'C' in arm
    raw, compiler_stats = {}, {}
    if compiler:
        proc = subprocess.run(['node', str(LIT/'compiler-choice-v1/compile.cjs')],
                              input=json.dumps(selected), text=True, capture_output=True,
                              check=True, timeout=120)
        compiled = json.loads(proc.stdout)
    else:
        compiled = {pid: {'candidates': {'original': text}, 'skip': None, 'errors': {}}
                    for pid, text in selected.items()}
    proposed = {}
    for pid, text in selected.items():
        entry = compiled[str(pid)]
        candidates = entry['candidates']
        assert set(candidates) <= {'original', 'layout', 'syntax', 'standard'}
        assert candidates['original'] == text
        proposed[pid] = sorted(set(candidates.values()))
        compiler_stats[pid] = {'skip': entry['skip'], 'errors': entry['errors'],
                               'candidate_count': len(proposed[pid])}
        for i, candidate in enumerate(proposed[pid]):
            raw[f'{pid}:{i}'] = candidate
    records = base.rewrite.records(raw)
    rewritten, traces = {}, {}
    for key, text in sorted(raw.items()):
        rewritten[key], traces[key] = base.rewrite.optimize(
            text, records[key], vocab, mode='coupled' if coupled else 'ordinary',
            sweeps=cfg['sweeps'], max_trials=cfg['trials'], rounds=cfg['rounds'],
            proposal_limit=cfg['proposal_limit'], state_limit=cfg['state_limit'])
    # Reparse every final output, including unchanged and unsupported policies.
    base.rewrite.records(rewritten)
    groups = {}
    for pid in selected:
        values = [original[pid], seed[pid], *prior.get(pid, []), selected[pid]]
        values += proposed[pid]
        values += [rewritten[f'{pid}:{i}'] for i in range(len(proposed[pid]))]
        assert len(prior.get(pid, [])) <= 2 and len(values) <= 13
        # Current is always the latest prior source after round zero. Hash
        # deduplication therefore leaves at most twelve distinct candidates.
        assert len(set(values)) <= 12
        groups[pid] = values
    return normalized(groups), {'compiler': compiler_stats, 'rewrite': traces}


def seal(folder, fields):
    receipt = {'validation_loaded': False, **fields,
               'files': {p.name: analyze.sha(p.read_bytes()) for p in sorted(folder.iterdir()) if p.is_file()}}
    analyze.write(folder/'fit-seal.json', receipt)
    return analyze.sha((folder/'fit-seal.json').read_bytes())


def fit_source(job):
    arm, work, out, c, cores = job
    os.sched_setaffinity(0, set(cores))
    work, out = Path(work), Path(out)
    folder = out/'fit'/arm
    folder.mkdir(parents=True)
    original = read(work/c['references']['R']/'fit-sources.json')
    seed = read(work/c['references']['seed13']/'fit-sources.json')
    assert set(original) == set(seed) == {str(i) for i in c['partition']['dev_fit']}
    vocab = read(work/c['references']['seed13']/'dictionary.json')
    selected, prior, history = dict(seed), {pid: [] for pid in seed}, []
    banned = set()
    start = time.monotonic()
    for no in range(c['source_rounds']):
        variants, stats = propose_sources(original, seed, selected, prior, vocab, arm, c['rewrite'])
        banned |= forbidden(variants)
        assert not set(vocab) & banned
        state = base.choose(variants, vocab)
        before = state['selections']
        state, search = base.polish(variants, state, banned, c['source_search'], c['neighborhood'])
        assert state['selections'] <= before
        selected, vocab = base.selected(variants, state), state['vocab']
        for pid, text in selected.items():
            prior[pid].append(text)
        history.append({'round': no, 'after_source_selection': before,
                        'fit_selections': state['selections'], 'source': stats, 'search': search})
        analyze.write(folder/'trace.json', history)
        print(json.dumps({'phase': 'source_fit', 'arm': arm, 'round': no,
                          'fit_selections': state['selections']}), flush=True)
    analyze.write(folder/'dictionary.json', vocab)
    analyze.write(folder/'fit-sources.json', selected)
    analyze.write(folder/'fit-variants.json', variants)
    analyze.write(folder/'fit-banned.json', sorted(banned))
    receipt = seal(folder, {'initial_source_sha256': digest(seed), 'fit_selections': state['selections']})
    summary = {'arm': arm, 'fit_selections': state['selections'], 'seconds': time.monotonic()-start,
               'fit_seal_sha256': receipt, 'source_rounds': c['source_rounds']}
    analyze.write(folder/'summary.json', summary)
    return summary


def repair_trajectory(job):
    mode, out, c, cores = job
    os.sched_setaffinity(0, set(cores))
    out = Path(out)
    root = out/'fit/NCP'
    texts = read(root/'fit-sources.json')
    vocab = read(root/'dictionary.json')
    banned = set(read(root/'fit-banned.json')) | base.sel.forbidden_strings(texts)
    observed = set(''.join(texts.values()))
    assert observed <= set(slots.ALPHABET)
    reserved = set(slots.ALPHABET) if mode == 'fixed96' else set(slots.ALPHABET)-observed
    folder = out/'repair'/mode
    folder.mkdir(parents=True)
    start = time.monotonic()
    pool, ranked = base.ranked_pool(texts, banned, c['repair']['max_length'])
    analyze.write(folder/'pool.json', pool)
    pool_hash = analyze.sha((folder/'pool.json').read_bytes())
    rng = random.Random(c['repair']['seed'])
    best, _, usage = slots.exact(texts, vocab)
    initial, moves, stop = best, [], 'move_limit'
    for no in range(c['repair']['moves']):
        remaining = c['repair']['seconds']-(time.monotonic()-start)
        if remaining <= 0:
            stop = 'time_limit'
            break
        fixed, candidates, capacity, freed = slots.proposal(
            vocab, observed, reserved, pool, ranked, rng, mode, c['repair'], usage)
        built = model.build(texts, fixed, candidates, capacity, vocab)
        remaining = c['repair']['seconds']-(time.monotonic()-start)
        if remaining <= 0:
            stop = 'time_limit_after_model'
            break
        chosen, solver = model.solve(built, candidates, True,
                                     min(c['repair']['solver_seconds'], remaining), seed=c['repair']['seed'])
        trial = weighted.order(fixed+chosen)
        assert len(trial) <= 256 and reserved <= set(trial) and not set(trial) & banned
        exact, _, new_usage = slots.exact(texts, trial)
        assert exact <= solver['objective']+1e-6
        if solver['optimal']:
            assert abs(exact-solver['objective']) <= 1e-6
        before = best
        accepted = exact < best
        if accepted:
            vocab, best, usage = trial, exact, new_usage
            analyze.write(folder/f'incumbent-{no:02d}.json', vocab)
        record = {'move': no, **solver, **freed, 'before': before, 'exact': exact,
                  'incumbent': best, 'accepted': accepted, 'pool_sha256': pool_hash,
                  'candidate_count': len(candidates), 'capacity': capacity,
                  'model_build_seconds': built['build_seconds'], 'validation_loaded': False}
        moves.append(record)
        with (folder/'moves.jsonl').open('a') as f:
            f.write(json.dumps(record, sort_keys=True)+'\n')
        print(json.dumps({'phase': 'repair', 'arm': mode, **record}), flush=True)
    analyze.write(folder/'dictionary.json', vocab)
    analyze.write(folder/'reserved.json', sorted(reserved))
    analyze.write(folder/'fit-banned.json', sorted(banned))
    summary = {'mode': mode, 'initial_selections': initial, 'fit_selections': best,
               'moves': moves, 'stop': stop, 'seconds': time.monotonic()-start,
               'source_sha256': digest(texts), 'pool_sha256': pool_hash}
    analyze.write(folder/'summary.json', summary)
    return summary


def finish_dictionary(job):
    arm, out, c, cores = job
    os.sched_setaffinity(0, set(cores))
    out = Path(out)
    mode = 'fixed96' if arm[1] == '0' else 'optional'
    weight = int(arm[2])
    root = out/'repair'/mode
    texts = read(out/'fit/NCP/fit-sources.json')
    vocab = read(root/'dictionary.json')
    reserved, banned = set(read(root/'reserved.json')), set(read(root/'fit-banned.json'))
    folder = out/'fit'/arm
    folder.mkdir(parents=True)
    state, trace = weighted.optimize(texts, vocab, weight, reserved, banned,
                                     c['neighborhood'], c['weighted_search'])
    analyze.write(folder/'dictionary.json', state['vocab'])
    analyze.write(folder/'fit-sources.json', texts)
    analyze.write(folder/'fit-banned.json', sorted(banned))
    analyze.write(folder/'trace.json', trace)
    receipt = seal(folder, {'source_cohort': 'NCP', 'objective': state['objective'],
                            'weight': weight, 'fit_selections_weighted': state['selections'],
                            'repair_dictionary_sha256': analyze.sha((root/'dictionary.json').read_bytes())})
    summary = {'arm': arm, 'source_cohort': 'NCP', 'weight': weight,
               'fit_selections_weighted': state['selections'], 'fit_characters_weighted': state['characters'],
               'objective': state['objective'], 'fit_seal_sha256': receipt,
               'search': {k: v for k, v in trace.items() if k != 'trace'}}
    analyze.write(folder/'summary.json', summary)
    return summary


def validation_sources(job):
    arm, work, out, c, cores = job
    os.sched_setaffinity(0, set(cores))
    work, out = Path(work), Path(out)
    assert (out/'all-fit-sealed.json').exists()
    folder = out/'fit'/arm
    vocab = read(folder/'dictionary.json')
    ids = {str(i) for i in c['partition']['dev_val']}
    original = {k:v for k,v in read(work/c['references']['R']/'sources.json').items() if k in ids}
    seed = {k:v for k,v in read(work/c['references']['seed13']/'sources.json').items() if k in ids}
    assert set(original) == set(seed) == ids
    selected = base.selected(normalized({p:[original[p],seed[p]] for p in ids}),
                             base.choose(normalized({p:[original[p],seed[p]] for p in ids}), vocab))
    prior, history = {pid: [] for pid in seed}, []
    banned = set(read(folder/'fit-banned.json'))
    for no in range(c['source_rounds']):
        variants, stats = propose_sources(original, seed, selected, prior, vocab, arm, c['rewrite'])
        state = base.choose(variants, vocab)
        selected = base.selected(variants, state)
        for pid, text in selected.items():
            prior[pid].append(text)
        banned |= forbidden(variants)
        history.append(stats)
    analyze.write(folder/'validation-sources.json', selected)
    analyze.write(folder/'validation-variants.json', variants)
    analyze.write(folder/'validation-trace.json', history)
    analyze.write(folder/'all-banned.json', sorted(banned))
    analyze.write(folder/'validation-seal.json', {'source_sha256': digest(selected),
        'dictionary_sha256': analyze.sha((folder/'dictionary.json').read_bytes()),
        'qualification_started': False,
        'files': {name: analyze.sha((folder/name).read_bytes()) for name in
                  ('validation-sources.json', 'validation-variants.json', 'all-banned.json')}})
    return {'arm': arm, 'source_sha256': digest(selected)}
