"""Joint exact-string vocabulary and qualified-source selection, development only."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
from itertools import combinations
import json
import math
from pathlib import Path
import platform
import statistics
import time

ROOT = Path(__file__).resolve().parent
SCALE = ROOT.parent / 'scale-v2'
spec = importlib.util.spec_from_file_location('scale_search', SCALE / 'search.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def order(vocab):
    return list(base.ALPHABET) + sorted(set(vocab) - set(base.ALPHABET))


def evaluate(sources, vocab, width, parent=None):
    """All variants compete after every move. Reuse only unaffected exact parses."""
    vocab = order(vocab)
    if len(vocab) > 2**width:
        raise ValueError('dictionary exceeds fixed-width budget')
    if any(s == text for variants in sources.values() for text in variants.values() for s in vocab):
        raise ValueError('whole-program literal')
    tree = base.trie(vocab)
    delta = set(vocab).symmetric_difference(parent['vocab']) if parent else None
    parsed, chosen = {}, {}
    for pid, variants in sorted(sources.items()):
        options = []
        for variant, text in sorted(variants.items()):
            key = (pid, variant)
            if parent and not any(fragment in text for fragment in delta):
                parts = parent['parsed'][key]
            else:
                parts = tuple(vocab[i] for i in base.segment(text, tree))
            parsed[key] = parts
            options.append((len(parts), len(text.encode()), variant))
        chosen[pid] = min(options)[2]
    counts = [len(parsed[(pid, variant)]) for pid, variant in chosen.items()]
    dictionary = len(base.dictionary_bytes(vocab))
    packets = sum(41 + (width * n + 7) // 8 for n in counts)
    return {'vocab': vocab, 'parsed': parsed, 'chosen': chosen,
            'selections': sum(counts), 'package_bytes': dictionary + packets,
            'dictionary_bytes': dictionary, 'packet_bytes': packets}


def cost(state, objective):
    if objective == 'input':
        return state['selections'], state['package_bytes']
    return state['package_bytes'], state['selections']


def brief(state):
    return {k: state[k] for k in ['selections', 'package_bytes', 'dictionary_bytes', 'packet_bytes']} | {'entries': len(state['vocab'])}


def proposals(sources, state, limit):
    # Different versions of one problem never count as distinct owners.
    scores, owners = defaultdict(dict), defaultdict(set)
    full = {t for vs in sources.values() for t in vs.values()}
    for (pid, variant), parts in state['parsed'].items():
        counts = Counter()
        for start in range(len(parts)):
            for length in range(2, 7):
                if start + length > len(parts):
                    break
                fragment = ''.join(parts[start:start+length])
                if len(fragment.encode()) <= 160 and fragment not in full and fragment not in state['vocab']:
                    counts[fragment] += length - 1
        for fragment, score in counts.items():
            scores[fragment][pid] = max(score, scores[fragment].get(pid, 0))
            owners[fragment].add(pid)
    return sorted((s for s in scores if len(owners[s]) >= 2),
                  key=lambda s: (-sum(scores[s].values()), len(s.encode()), s))[:limit]


def prune(sources, state, width):
    used = {s for pid, v in state['chosen'].items() for s in state['parsed'][(pid, v)]}
    removed = sorted(set(state['vocab']) - used - set(base.ALPHABET))
    if not removed:
        return state, []
    result = evaluate(sources, set(state['vocab']) - set(removed), width, state)
    assert result['selections'] == state['selections']
    return result, removed


def improve(sources, initial, width, objective, limits):
    current = initial
    trace, trials = [], 0
    start = time.monotonic()
    stop = 'round_limit'
    for round_no in range(limits['rounds_per_start']):
        attempts, tested = [], set()
        best = current
        best_move = None
        def expired():
            return trials >= limits['trials_per_start'] or time.monotonic()-start >= limits['seconds_per_start']
        def consider(remove=(), add=()):
            nonlocal trials, best, best_move
            candidate = set(current['vocab']) - set(remove) | set(add)
            identity = tuple(sorted(candidate))
            if len(candidate) > 2**width or identity in tested or expired():
                return None
            tested.add(identity)
            state = evaluate(sources, candidate, width, current)
            trials += 1
            move = {'remove': list(remove), 'add': list(add), 'result': brief(state),
                    'source_changes': {str(pid): v for pid, v in state['chosen'].items() if v != current['chosen'][pid]}}
            attempts.append(move)
            if cost(state, objective) < cost(best, objective):
                best, best_move = state, move
            return state
        # Score deletion harm exactly; frequency is not used to select removals.
        deletions = []
        for fragment in current['vocab'][len(base.ALPHABET):]:
            state = consider(remove=[fragment])
            if state:
                deletions.append((cost(state, objective), fragment))
        removals = [s for _, s in sorted(deletions)[:limits['removal_shortlist']]]
        additions = proposals(sources, current, limits['addition_shortlist'])
        for add in additions:
            consider(add=[add])
            for remove in removals:
                consider(remove=[remove], add=[add])
        # Test two additions together even when neither alone improves anything.
        needed = max(0, len(current['vocab']) + 2 - 2**width)
        removal_sets = list(combinations(removals, needed))[:limits['pair_removal_sets']]
        for pair in combinations(additions[:limits['pair_addition_shortlist']], 2):
            for remove in removal_sets:
                consider(remove=remove, add=pair)
        pruned = []
        if best_move:
            best, pruned = prune(sources, best, width)
            assert cost(best, objective) < cost(current, objective)
        trace.append({'round': round_no, 'before': brief(current), 'attempts': attempts,
                      'accepted': best_move, 'pruned_after_move': pruned, 'after': brief(best)})
        current = best
        print(json.dumps({'width': width, 'objective': objective, 'round': round_no,
                          'trials': trials, **brief(current)}), flush=True)
        if expired():
            stop = 'trial_limit' if trials >= limits['trials_per_start'] else 'time_limit'
            break
        if not best_move:
            stop = 'no_improvement_in_tested_neighborhood'
            break
    return current, {'rounds': trace, 'trials': trials, 'elapsed_seconds': time.monotonic()-start, 'stop': stop}


def load_sources():
    manifest = json.loads((SCALE/'generated/manifest.json').read_text())
    q = json.loads((SCALE/'qualification/report.json').read_text())
    if q['generated_manifest_sha256'] != sha((SCALE/'generated/manifest.json').read_bytes()):
        raise ValueError('qualification/source manifest mismatch')
    qualified = {(r['id'], r['variant']): r for r in q['rows']}
    sources, metadata = defaultdict(dict), {}
    for r in manifest['rows']:
        # Shared declared solve interface; original entrypoints are not free adapters.
        if r['variant'] not in ['canonical', 'compact']:
            continue
        text = (SCALE/'generated'/r['file']).read_text()
        verdict = qualified[(r['id'], r['variant'])]
        if sha(text.encode()) != r['sha256'] or verdict['sha256'] != r['sha256'] or not verdict['passed'] or verdict['failures']:
            raise ValueError('unqualified source')
        if r['entry'] != 'solve' or r['interface'] != 'named-function':
            raise ValueError('incompatible interface')
        sources[r['id']][r['variant']] = text
        metadata[(r['id'], r['variant'])] = r
    if len(sources) != 80 or any(len(v) != 2 for v in sources.values()):
        raise ValueError('unexpected development population')
    return dict(sources), metadata


def save(folder, sources, metadata, state, width, method):
    texts = {str(pid): sources[pid][v] for pid, v in state['chosen'].items()}
    ids = {s: i for i, s in enumerate(state['vocab'])}
    seqs = {str(pid): [ids[s] for s in state['parsed'][(pid, v)]] for pid, v in state['chosen'].items()}
    metrics = base.save(folder, texts, state['vocab'], seqs, width, 'joint-qualified', method)
    m = json.loads((folder/'manifest.json').read_text())
    for row in m['programs']:
        v = state['chosen'][row['id']]
        row.update(variant=v, source_file='../scale-v2/generated/'+metadata[(row['id'], v)]['file'], entry='solve', interface='named-function')
    metrics['p95_selections'] = sorted(r['selections'] for r in m['programs'])[math.ceil(.95*len(texts))-1]
    metrics['source_variants'] = dict(Counter(state['chosen'].values()))
    assert metrics['selections'] == state['selections'] and metrics['package_bytes'] == state['package_bytes']
    m['metrics'] = metrics
    write(folder/'manifest.json', m)
    return metrics


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    contract = json.loads((ROOT/'contract.json').read_text())
    sources, metadata = load_sources()
    for rel, digest in contract['inputs'].items():
        if sha((ROOT/rel).read_bytes()) != digest:
            raise ValueError('frozen input changed: '+rel)
    args.output.mkdir(exist_ok=False)
    seeds = []
    for path in sorted((SCALE/'search-v2').glob('*/dictionary.json')):
        seeds.append((path.parent.name, json.loads(path.read_text())))
    records, seed_rows = [], []
    for width in [7, 8]:
        states = []
        for name, vocab in seeds:
            if len(vocab) > 2**width:
                continue
            state = evaluate(sources, vocab, width)
            raw = brief(state)
            state, removed = prune(sources, state, width)
            states.append((name, state))
            seed_rows.append({'name': name, 'width': width, 'joint_reselection': raw,
                             'removed_unused': removed, 'after_pruning': brief(state)})
        for objective in ['input', 'storage']:
            seen, selected = set(), []
            for name, state in sorted(states, key=lambda pair: (cost(pair[1], objective), pair[0])):
                identity = tuple(state['vocab'])
                if identity not in seen:
                    selected.append((name, state)); seen.add(identity)
                if len(selected) == contract['bounds']['starts_per_arm']:
                    break
            candidates = []
            for index, (name, initial) in enumerate(selected):
                final, trace = improve(sources, initial, width, objective, contract['bounds'])
                label = f'{2**width}-{objective}-start{index}'
                metrics = save(args.output/label, sources, metadata, final, width, 'joint-multi-start-paired-search')
                write(args.output/(label+'-trace.json'), {'seed': name, 'initial_dictionary': initial['vocab'],
                    'initial_sources': initial['chosen'], 'initial': brief(initial), **trace})
                record = {'label': label, 'seed': name, 'objective': objective, 'metrics': metrics,
                          'manifest_sha256': sha((args.output/label/'manifest.json').read_bytes()),
                          'trace_sha256': sha((args.output/(label+'-trace.json')).read_bytes()),
                          'trials': trace['trials'], 'stop': trace['stop']}
                records.append(record); candidates.append((cost(final, objective), label))
            print(json.dumps({'arm_complete': f'{width}-{objective}', 'winner': min(candidates)[1]}), flush=True)
    write(args.output/'summary.json', {'schema':'gamma.literal-joint.v1', 'scope': contract['scope'],
        'host': platform.node(), 'python': platform.python_version(), 'seed_screen': seed_rows, 'runs': records,
        'contract_sha256': sha((ROOT/'contract.json').read_bytes()), 'search_sha256': sha(Path(__file__).read_bytes()),
        'execution_evidence': 'Exact source hashes reuse scale-v2 native receipts; no new JavaScript execution.'})


if __name__ == '__main__':
    main()
