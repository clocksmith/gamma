"""Matched 80-problem literal experiment: twelve fixed-source arms and six joint arms.

Arms differ only in candidate pool (designed, mined, combined). Admission, swaps,
budgets, fallback alphabet, codec, packet framing and the shortlist ranking are
shared and frozen in contract.json. Nothing here executes candidate source: every
packet must decode, through the canonical codec, to a qualified source hash.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import platform
import resource
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIT = ROOT.parent
SCALE = LIT / 'scale-v2'
POOLS = ('designed', 'mined', 'combined')
STYLES = ('canonical', 'compact')
SIZES = (128, 256)
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


base = module('scale_search', SCALE / 'search.py')
joint = module('joint_search', LIT / 'joint-v1/search.py')
codec = module('canonical_codec', LIT / 'readable-v1/literal_codec.py')


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def load_inputs(contract):
    """Verify every frozen input, then return qualified texts by style and by problem."""
    for rel, digest in contract['inputs'].items():
        if sha((ROOT / rel).read_bytes()) != digest:
            raise ValueError(f'frozen input changed: {rel}')
    manifest_bytes = (SCALE / 'generated/manifest.json').read_bytes()
    rows = json.loads(manifest_bytes)['rows']
    for receipt in contract['qualification_receipts'].values():
        report = json.loads((ROOT / receipt).read_text())
        if report['generated_manifest_sha256'] != sha(manifest_bytes) or report['passed_sources'] != 240:
            raise ValueError(f'qualification receipt does not cover the manifest: {receipt}')
        verdicts = {(r['id'], r['variant']): r for r in report['rows']}
        for r in rows:
            v = verdicts[(r['id'], r['variant'])]
            if v['sha256'] != r['sha256'] or not v['passed'] or v['failures']:
                raise ValueError(f'unqualified source {r["id"]} {r["variant"]} in {receipt}')
    texts = {style: {} for style in STYLES}
    for r in rows:
        if r['variant'] in STYLES:
            text = (SCALE / 'generated' / r['file']).read_text()
            if sha(text.encode()) != r['sha256'] or r['entry'] != 'solve' or r['interface'] != 'named-function':
                raise ValueError(f'source/interface mismatch {r["id"]} {r["variant"]}')
            texts[r['variant']][str(r['id'])] = text
    if any(len(t) != 80 for t in texts.values()):
        raise ValueError('unexpected development population')
    return texts, {(r['id'], r['variant']): r for r in rows if r['variant'] in STYLES}


def designed_pool(contract):
    pool = json.loads((ROOT / contract['designed_pool']).read_text())['pool']
    return {style: [p['text'] for p in pool if p['style'] == style] for style in STYLES}


def rank(candidates, joined, vocab):
    """Shared shortlist ranking for every pool: occurrences x selections saved per occurrence.
    Ranking only orders the shortlist; measured exact gain decides admission."""
    tree = base.trie(vocab)
    score = {s: joined.count(s) * (len(base.segment(s, tree)) - 1) for s in candidates}
    return sorted(candidates, key=lambda s: (-score[s], len(s.encode()), s))


def fixed_candidates(pool, designed):
    def propose(texts, vocab, current, retired):
        present = set(vocab) | retired
        found = []
        if pool in ('mined', 'combined'):
            found += base.proposals(texts, vocab, current)
        if pool in ('designed', 'combined'):
            found += [s for s in designed if sum(s in t for t in texts.values()) >= 2]
        unique = [s for s in dict.fromkeys(found) if s not in present]
        return rank(unique, '\x00'.join(texts.values()), vocab)
    return propose


def learn(texts, limits, propose):
    """scale-v2 learn() with the candidate source injected; all other steps unchanged."""
    vocab = list(base.ALPHABET)
    current = base.sequences(texts, vocab)
    trace, snapshots, swaps = [], {}, []
    start, trials = time.monotonic(), 0
    retired = set()
    for budget in SIZES:
        while len(vocab) < budget and time.monotonic() - start < limits['search_seconds_per_arm']:
            candidates = propose(texts, vocab, current, retired)[:limits['shortlist']]
            scored, best = [], None
            for fragment in candidates:
                if trials >= limits['max_trials_per_arm'] or time.monotonic() - start >= limits['search_seconds_per_arm']:
                    break
                gain, proposed = base.exact_addition(texts, vocab, current, fragment)
                trials += 1
                scored.append({'literal': fragment, 'exact_selection_gain': gain})
                key = (-gain, len(fragment.encode()), fragment)
                if best is None or key < best[0]:
                    best = (key, fragment, proposed, gain)
            if best is None or best[3] <= 0:
                break
            _, chosen, proposed, gain = best
            before = sum(map(len, current.values()))
            vocab.append(chosen)
            current = proposed
            used = {i for seq in current.values() for i in seq}
            redundant = [i for i in range(len(base.ALPHABET), len(vocab)) if i not in used]
            retired.update(vocab[i] for i in redundant)
            if redundant:
                vocab = [s for i, s in enumerate(vocab) if i not in redundant]
                current = base.sequences(texts, vocab)
            after = sum(map(len, current.values()))
            assert before - after == gain
            trace.append({'step': len(trace), 'chosen': chosen, 'before': before, 'after': after,
                          'gain': gain, 'reclaimed_slots': len(redundant), 'entries': len(vocab), 'shortlist': scored})
        frequency = Counter(i for seq in current.values() for i in seq)
        removals = sorted(range(len(base.ALPHABET), len(vocab)), key=lambda i: (frequency[i], -len(vocab[i]), vocab[i]))[:3]
        # As in scale-v2, swap additions are not filtered by the retired set.
        additions = propose(texts, vocab, current, set())[:4]
        current_cost = (sum(map(len, current.values())), len(base.dictionary_bytes(vocab)))
        best_swap, attempts = None, []
        for remove in removals:
            for add in additions:
                if trials >= limits['max_trials_per_arm'] or time.monotonic() - start >= limits['search_seconds_per_arm']:
                    break
                candidate = [s for k, s in enumerate(vocab) if k != remove] + [add]
                proposed = base.sequences(texts, candidate)
                trials += 1
                cost = (sum(map(len, proposed.values())), len(base.dictionary_bytes(candidate)))
                attempts.append({'remove': vocab[remove], 'add': add, 'before_selections': current_cost[0],
                                 'after_selections': cost[0], 'dictionary_bytes': cost[1]})
                if cost < current_cost and (best_swap is None or cost < best_swap[0]):
                    best_swap = (cost, candidate, proposed, attempts[-1])
        decision = None
        if best_swap:
            _, vocab, current, decision = best_swap
        swaps.append({'budget': budget, 'attempts': attempts, 'accepted': decision})
        snapshots[budget] = (list(vocab), dict(current))
    elapsed = time.monotonic() - start
    return snapshots, {'steps': trace, 'exact_candidate_trials': trials, 'elapsed_seconds': elapsed, 'swaps': swaps,
                       'retired_literals': sorted(retired), 'time_limit_reached': elapsed >= limits['search_seconds_per_arm'],
                       'trial_limit_reached': trials >= limits['max_trials_per_arm']}


def verify_and_extend(folder, texts, vocab, provenance, extra=None):
    """Independently decode every packet with the canonical codec, then add derived metrics."""
    m = json.loads((folder / 'manifest.json').read_text())
    raw = (folder / 'dictionary.ltd').read_bytes()
    literals = [s.encode() for s in vocab]
    chars_fallback = chars_total = 0
    for row in m['programs']:
        source = texts[str(row['id'])].encode()
        codec.verify_packet((folder / f"{row['id']}.ltv").read_bytes(), raw, literals, source)
        assert sha(source) == row['source_sha256']
        chars_total += len(source)
        chars_fallback += sum(len(vocab[i]) for i in row['sequence'] if len(vocab[i]) == 1)
    counts = sorted(r['selections'] for r in m['programs'])
    met = m['metrics']
    met.update(covered_programs=len(m['programs']), p95_selections=counts[math.ceil(.95 * len(counts)) - 1],
               total_input_bits=met['selection_bits'], fallback_character_fraction=chars_fallback / chars_total,
               entries_by_provenance=dict(Counter(provenance(s) for s in vocab)), **(extra or {}))
    write(folder / 'manifest.json', m)
    return met


def provenance_of(designed_all):
    designed = set(designed_all)
    return lambda s: 'fallback' if s in base.ALPHABET else 'designed' if s in designed else 'mined'


def peak_memory():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {'peak_rss_bytes': rss if sys.platform == 'darwin' else rss * 1024}


def run_fixed(contract, out, pool, style):
    texts, _ = load_inputs(contract)
    designed = designed_pool(contract)
    snapshots, trace = learn(texts[style], contract['fixed_bounds'], fixed_candidates(pool, designed[style]))
    write(out / f'fixed-{pool}-{style}-trace.json', trace)
    provenance = provenance_of(designed[style])
    rows = []
    for size, (vocab, seqs) in snapshots.items():
        folder = out / f'fixed-{pool}-{style}-{size}'
        base.save(folder, texts[style], vocab, seqs, size.bit_length() - 1, style, f'{pool}-pool-measured-gain')
        rows.append(verify_and_extend(folder, texts[style], vocab, provenance,
                                      {'pool': pool, 'style': style, 'size': size, 'kind': 'fixed'}))
    write(out / f'fixed-{pool}-{style}-resources.json', {'search_seconds': trace['elapsed_seconds'], 'trials': trace['exact_candidate_trials'],
                                                         'time_limit_reached': trace['time_limit_reached'], **peak_memory()})
    return rows


def joint_candidates(pool, designed_all):
    def propose(sources, state, limit):
        found = []
        if pool in ('mined', 'combined'):
            found += joint.proposals(sources, state, 10**9)
        if pool in ('designed', 'combined'):
            for s in designed_all:
                owners = {pid for pid, variants in sources.items() if any(s in t for t in variants.values())}
                if len(owners) >= 2:
                    found.append(s)
        unique = [s for s in dict.fromkeys(found) if s not in state['vocab']]
        chosen = '\x00'.join(sources[pid][v] for pid, v in state['chosen'].items())
        return rank(unique, chosen, state['vocab'])[:limit]
    return propose


def improve(sources, initial, width, objective, limits, propose):
    """joint-v1 improve() with the candidate source injected; all other steps unchanged."""
    from itertools import combinations
    current, trace, trials, start, stop = initial, [], 0, time.monotonic(), 'round_limit'
    for round_no in range(limits['rounds_per_start']):
        attempts, tested, best, best_move = [], set(), current, None
        def expired():
            return trials >= limits['trials_per_start'] or time.monotonic() - start >= limits['seconds_per_start']
        def consider(remove=(), add=()):
            nonlocal trials, best, best_move
            candidate = set(current['vocab']) - set(remove) | set(add)
            identity = tuple(sorted(candidate))
            if len(candidate) > 2**width or identity in tested or expired():
                return None
            tested.add(identity)
            state = joint.evaluate(sources, candidate, width, current)
            trials += 1
            move = {'remove': list(remove), 'add': list(add), 'result': joint.brief(state),
                    'source_changes': {str(pid): v for pid, v in state['chosen'].items() if v != current['chosen'][pid]}}
            attempts.append(move)
            if joint.cost(state, objective) < joint.cost(best, objective):
                best, best_move = state, move
            return state
        deletions = []
        for fragment in current['vocab'][len(base.ALPHABET):]:
            state = consider(remove=[fragment])
            if state:
                deletions.append((joint.cost(state, objective), fragment))
        removals = [s for _, s in sorted(deletions)[:limits['removal_shortlist']]]
        additions = propose(sources, current, limits['addition_shortlist'])
        for add in additions:
            consider(add=[add])
            for remove in removals:
                consider(remove=[remove], add=[add])
        needed = max(0, len(current['vocab']) + 2 - 2**width)
        removal_sets = list(combinations(removals, needed))[:limits['pair_removal_sets']]
        for pair in combinations(additions[:limits['pair_addition_shortlist']], 2):
            for remove in removal_sets:
                consider(remove=remove, add=pair)
        pruned = []
        if best_move:
            best, pruned = joint.prune(sources, best, width)
            assert joint.cost(best, objective) < joint.cost(current, objective)
        trace.append({'round': round_no, 'before': joint.brief(current), 'attempts': attempts,
                      'accepted': best_move, 'pruned_after_move': pruned, 'after': joint.brief(best)})
        current = best
        if expired():
            stop = 'trial_limit' if trials >= limits['trials_per_start'] else 'time_limit'
            break
        if not best_move:
            stop = 'no_improvement_in_tested_neighborhood'
            break
    return current, {'rounds': trace, 'trials': trials, 'elapsed_seconds': time.monotonic() - start, 'stop': stop}


def run_joint(contract, out, pool, size):
    texts, metadata = load_inputs(contract)
    sources = {int(pid): {style: texts[style][pid] for style in STYLES} for pid in texts['canonical']}
    designed = designed_pool(contract)
    designed_all = list(dict.fromkeys(designed['canonical'] + designed['compact']))
    width = size.bit_length() - 1
    starts, inherited = [], {}
    for style in STYLES:
        vocab = json.loads((out / f'fixed-{pool}-{style}-{size}/dictionary.json').read_text())
        fixed = json.loads((out / f'fixed-{pool}-{style}-{size}/manifest.json').read_text())['metrics']
        resources = json.loads((out / f'fixed-{pool}-{style}-resources.json').read_text())
        inherited[style] = {'trials': resources['trials'], 'search_seconds': resources['search_seconds']}
        state, _ = joint.prune(sources, joint.evaluate(sources, vocab, width), width)
        starts.append((style, fixed, state))
    incumbent_style, incumbent_fixed, _ = min(starts, key=lambda s: (s[1]['selections'], s[1]['package_bytes'], s[0]))
    finals, records = [], []
    for style, fixed, state in starts:
        final, trace = improve(sources, state, width, 'input', contract['joint_bounds'], joint_candidates(pool, designed_all))
        write(out / f'joint-{pool}-{size}-start-{style}-trace.json', {'start_style': style, 'initial': joint.brief(state), **trace})
        finals.append((joint.cost(final, 'input'), style, final))
        records.append({'start_style': style, 'trials': trace['trials'], 'seconds': trace['elapsed_seconds'], 'stop': trace['stop'],
                        'start': joint.brief(state), 'final': joint.brief(final)})
    _, winner_style, best = min(finals, key=lambda f: (f[0], f[1]))
    # Preserve the best eligible fixed-source incumbent: a joint result may never be worse.
    if (best['selections'], best['package_bytes']) > (incumbent_fixed['selections'], incumbent_fixed['package_bytes']):
        raise AssertionError('joint search lost the fixed-source incumbent')
    folder = out / f'joint-{pool}-{size}'
    joint.save(folder, sources, metadata, best, width, f'{pool}-pool-joint')
    chosen_texts = {str(pid): sources[pid][v] for pid, v in best['chosen'].items()}
    met = verify_and_extend(folder, chosen_texts, best['vocab'], provenance_of(designed_all),
                            {'pool': pool, 'style': 'joint', 'size': size, 'kind': 'joint', 'incumbent_style': incumbent_style,
                             'incumbent_selections': incumbent_fixed['selections'], 'winning_start': winner_style,
                             'starts': records, 'inherited_fixed_search': inherited})
    write(out / f'joint-{pool}-{size}-resources.json', {'search_seconds': sum(r['seconds'] for r in records),
                                                        'trials': sum(r['trials'] for r in records), **peak_memory()})
    return met


def run_control(contract, out, style):
    """Unchanged scale-v2 search: reproduces stored evidence in this environment."""
    texts, _ = load_inputs(contract)
    snapshots, trace = base.learn(texts[style], json.loads((SCALE / 'contract.json').read_text())['bounds'])
    result = {}
    for size, (vocab, seqs) in snapshots.items():
        stored = json.loads((SCALE / f'search-v2/{style}-marginal-{size}/manifest.json').read_text())
        stored_vocab = json.loads((SCALE / f'search-v2/{style}-marginal-{size}/dictionary.json').read_text())
        result[str(size)] = {'selections': sum(map(len, seqs.values())), 'stored_selections': stored['metrics']['selections'],
                             'identical_dictionary': vocab == stored_vocab, 'trials': trace['exact_candidate_trials']}
    write(out / f'control-scale-v2-{style}.json', result)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--fixed', nargs=2, metavar=('POOL', 'STYLE'))
    p.add_argument('--joint', nargs=2, metavar=('POOL', 'SIZE'))
    p.add_argument('--control', metavar='STYLE')
    a = p.parse_args()
    contract = json.loads((ROOT / 'contract.json').read_text())
    if a.fixed:
        print(json.dumps(run_fixed(contract, a.output, *a.fixed)), flush=True)
        return
    if a.joint:
        print(json.dumps(run_joint(contract, a.output, a.joint[0], int(a.joint[1]))), flush=True)
        return
    if a.control:
        print(json.dumps(run_control(contract, a.output, a.control)), flush=True)
        return
    load_inputs(contract)
    a.output.mkdir(exist_ok=False)
    started = time.monotonic()
    me = [sys.executable, '-B', str(Path(__file__).resolve()), '--output', str(a.output)]
    jobs = [['--control', s] for s in STYLES] + [['--fixed', pool, s] for pool in POOLS for s in STYLES] \
        + [['--joint', pool, str(size)] for pool in POOLS for size in SIZES]
    log = []
    for job in jobs:
        t0 = time.monotonic()
        done = subprocess.run(me + job, capture_output=True, text=True)
        log.append({'job': job, 'returncode': done.returncode, 'seconds': time.monotonic() - t0, 'stderr_tail': done.stderr[-2000:]})
        print(json.dumps({'job': job, 'returncode': done.returncode, 'seconds': round(log[-1]['seconds'], 2)}), flush=True)
        if done.returncode:
            break
    write(a.output / 'run.json', {'schema': 'gamma.matched80.run.v1', 'jobs': log, 'elapsed_seconds': time.monotonic() - started,
                                  'host': platform.node(), 'python': platform.python_version(), 'platform': platform.platform(),
                                  'contract_sha256': sha((ROOT / 'contract.json').read_bytes()), 'runner_sha256': sha(Path(__file__).read_bytes()),
                                  'complete': all(j['returncode'] == 0 for j in log) and len(log) == len(jobs)})


if __name__ == '__main__':
    main()
