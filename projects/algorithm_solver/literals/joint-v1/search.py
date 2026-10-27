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


def order(vocab, alphabet=None):
    """Keep the historical alphabet unless an explicit charged alphabet is supplied."""
    vocab = list(vocab)
    alphabet = base.ALPHABET if alphabet is None else list(alphabet)
    if any(not isinstance(s, str) or not s for s in [*alphabet, *vocab]):
        raise ValueError('literals must be nonempty strings')
    if len(set(alphabet)) != len(alphabet):
        raise ValueError('duplicate alphabet entry')
    return list(alphabet) + sorted(set(vocab) - set(alphabet))


def segment(text, tree, boundaries=None):
    """Minimum selections, then literal-ID order, at permitted lexical boundaries."""
    if boundaries is None:
        return base.segment(text, tree)
    n = len(text)
    costs, edges = [n + 1] * (n + 1), [None] * n
    costs[n] = 0
    for start in range(n - 1, -1, -1):
        if start not in boundaries:
            continue
        node, end = tree, start
        while end < n and text[end] in node:
            node = node[text[end]]
            end += 1
            if end in boundaries and None in node and costs[end] < n + 1:
                candidate = (costs[end] + 1, node[None])
                previous = (costs[start], edges[start][0] if edges[start] else n + 1)
                if candidate < previous:
                    costs[start], edges[start] = candidate[0], (node[None], end)
    if costs[0] > n:
        raise ValueError('unrepresentable at lexical boundaries')
    result, pos = [], 0
    while pos < n:
        index, pos = edges[pos]
        result.append(index)
    return result


def representable_prefix(text, tree, boundaries=None):
    """Longest reachable prefix; the existing exact DP chooses its minimum path.

    This never skips a missing character or joins text across an uncovered gap.
    Equal-length minimum paths retain the existing lower literal-ID tie break.
    """
    reachable = {0}
    for start in range(len(text)):
        if start not in reachable:
            continue
        node, end = tree, start
        while end < len(text) and text[end] in node:
            node = node[text[end]]
            end += 1
            if None in node and (boundaries is None or end in boundaries):
                reachable.add(end)
    end = max(reachable)
    return end, tuple(segment(text[:end], tree, boundaries))


def evaluate(sources, vocab, width, parent=None, *, alphabet=None, allow_partial=False,
             boundaries=None, source_objective='input'):
    """All variants compete after every move. Reuse only unaffected exact parses."""
    if type(width) is not int or not 4 <= width <= 8:
        raise ValueError('width must be 4..8')
    vocab = order(vocab, alphabet)
    if len(vocab) > 2**width:
        raise ValueError('dictionary exceeds fixed-width budget')
    if any(s == text for variants in sources.values() for text in variants.values() for s in vocab):
        raise ValueError('whole-program literal')
    tree = base.trie(vocab)
    if parent:
        shared = set(vocab) & set(parent['vocab'])
        if ([s for s in vocab if s in shared]
                != [s for s in parent['vocab'] if s in shared]):
            parent = None  # IDs define ties, so reordered shared literals need a new path.
    delta = set(vocab).symmetric_difference(parent['vocab']) if parent else None
    parsed, chosen, uncovered, source_hashes, boundary_hashes = {}, {}, {}, {}, {}
    for pid, variants in sorted(sources.items()):
        options = []
        for variant, text in sorted(variants.items()):
            key = (pid, variant)
            allowed = None if boundaries is None else frozenset(boundaries[key])
            if allowed is not None and (0 not in allowed or len(text) not in allowed or
                    any(type(p) is not int or p < 0 or p > len(text) for p in allowed)):
                raise ValueError('invalid lexical boundaries')
            boundary_hashes[key] = None if allowed is None else sha(json.dumps(sorted(allowed)).encode())
            source_hashes[key] = sha(text.encode())
            if (parent and key in parent['parsed']
                    and parent.get('source_hashes', {}).get(key) == source_hashes[key]
                    and parent.get('boundary_hashes', {}).get(key) == boundary_hashes[key]
                    and not any(fragment in text for fragment in delta)):
                parts = parent['parsed'][key]
            else:
                try:
                    parts = tuple(vocab[i] for i in segment(text, tree, allowed))
                except ValueError:
                    if not allow_partial:
                        raise
                    end, prefix = representable_prefix(text, tree, allowed)
                    uncovered[key] = {'prefix_characters': end,
                                      'prefix': tuple(vocab[i] for i in prefix),
                                      'uncovered_characters': len(text) - end,
                                      'uncovered_utf8_bytes': len(text[end:].encode())}
                    continue
            parsed[key] = parts
            priority = ()
            if source_objective == 'compact':
                compliant = bool(parts) and 10 * sum(len(p) == 1 for p in parts) <= len(parts)
                priority = (not (compliant and len(parts) <= 96),
                            not (compliant and len(parts) <= 32), not compliant)
            options.append(priority + (len(parts), len(text.encode()), variant))
        if options:
            chosen[pid] = min(options)[-1]
    counts = [len(parsed[(pid, variant)]) for pid, variant in chosen.items()]
    if not vocab and not allow_partial:
        raise ValueError('nonempty literal list required')
    # An empty proposal pool is a failed search state, not a serialized dictionary.
    dictionary = len(base.dictionary_bytes(vocab)) if vocab else 0
    packets = sum(41 + (width * n + 7) // 8 for n in counts)
    singletons = sum(len(piece) == 1 for pid, variant in chosen.items()
                     for piece in parsed[(pid, variant)])
    # These counts guide search but never delete a failing program from coverage.
    # Check the genuine minimum path; no padded path can dilute singleton share.
    compliant = [parts for pid, variant in chosen.items()
                 if (parts := parsed[pid, variant]) and
                 10 * sum(len(piece) == 1 for piece in parts) <= len(parts)]
    return {'vocab': vocab, 'parsed': parsed, 'chosen': chosen,
            'serializable_dictionary': bool(vocab),
            'boundary_hashes': boundary_hashes,
            'source_hashes': source_hashes, 'uncovered': uncovered,
            'coverage': len(chosen), 'target': len(sources), 'allow_partial': allow_partial,
            'literal_bits': width * sum(counts), 'singleton_bits': width * singletons,
            'singleton_selections': singletons,
            'singleton_bit_share': singletons / sum(counts) if sum(counts) else None,
            'median_selections': statistics.median(counts) if counts else None,
            'p95_selections': sorted(counts)[math.ceil(.95 * len(counts)) - 1] if counts else None,
            'source_utf8_bytes': sum(len(sources[pid][variant].encode()) for pid, variant in chosen.items()),
            'packet_header_bytes': 41 * len(counts),
            'payload_padding_bits': sum((-width * n) % 8 for n in counts),
            'selections': sum(counts), 'package_bytes': dictionary + packets,
            'dictionary_bytes': dictionary, 'packet_bytes': packets,
            'singleton_compliant_programs': len(compliant),
            'within_32_selections': sum(len(parts) <= 32 for parts in compliant),
            'within_96_selections': sum(len(parts) <= 96 for parts in compliant),
            'reachable_prefix_characters': sum(max(
                (len(text) if (pid, v) in parsed else uncovered[pid, v]['prefix_characters'])
                for v, text in variants.items()) for pid, variants in sources.items())}


def cost(state, objective):
    if objective == 'compact':
        feasible = (bool(state['coverage']) and state['singleton_bit_share'] <= .1 and
                    state['median_selections'] <= 32 and state['p95_selections'] <= 96)
        return (not feasible, -state['within_96_selections'], -state['within_32_selections'],
                -state['singleton_compliant_programs'], -state['coverage'],
                -state['reachable_prefix_characters'], state['selections'], state['package_bytes'])
    prefix = (-state['coverage'],) if state.get('allow_partial') else ()
    if objective == 'singleton':
        # Absolute counts precede every denominator. Adding multichar selections
        # with unchanged singleton bits can never improve this objective.
        return prefix + (state['singleton_bits'], state['literal_bits'], state['package_bytes'])
    if objective == 'input':
        return prefix + (state['selections'], state['package_bytes'])
    if objective == 'storage':
        return prefix + (state['package_bytes'], state['selections'])
    raise ValueError('unknown search objective')


def pareto_vector(state):
    """No share/percentage dimension that can reward padding its denominator."""
    return (-state['coverage'], state['singleton_bits'], state['literal_bits'], state['package_bytes'])


def brief(state):
    return {k: state[k] for k in ['coverage', 'target', 'selections', 'literal_bits',
        'singleton_bits', 'package_bytes', 'dictionary_bytes', 'packet_bytes']} | {'entries': len(state['vocab'])}


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


def prune(sources, state, width, *, alphabet=None, allow_partial=False, boundaries=None):
    used = {s for pid, v in state['chosen'].items() for s in state['parsed'][(pid, v)]}
    if not used:
        return state, []  # The existing packet format requires a nonempty dictionary.
    protected = base.ALPHABET if alphabet is None else alphabet
    removed = sorted(set(state['vocab']) - used - set(protected))
    if not removed:
        return state, []
    result = evaluate(sources, set(state['vocab']) - set(removed), width, state,
                      alphabet=alphabet, allow_partial=allow_partial, boundaries=boundaries)
    assert result['selections'] == state['selections']
    assert result['coverage'] == state['coverage']
    return result, removed


def improve(sources, initial, width, objective, limits, *, alphabet=None,
            allow_partial=False, candidate_pool=None, boundaries=None):
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
            if not candidate or len(candidate) > 2**width or identity in tested or expired():
                return None
            tested.add(identity)
            state = evaluate(sources, candidate, width, current,
                             alphabet=alphabet, allow_partial=allow_partial, boundaries=boundaries,
                             source_objective=objective)
            trials += 1
            move = {'remove': list(remove), 'add': list(add), 'result': brief(state),
                    'source_changes': {str(pid): v for pid, v in state['chosen'].items() if v != current['chosen'].get(pid)}}
            attempts.append(move)
            if cost(state, objective) < cost(best, objective):
                best, best_move = state, move
            return state
        # Score deletion harm exactly; frequency is not used to select removals.
        deletions = []
        protected = set(base.ALPHABET if alphabet is None else alphabet)
        for fragment in current['vocab']:
            if fragment in protected:
                continue
            state = consider(remove=[fragment])
            if state:
                deletions.append((cost(state, objective), fragment))
        removals = [s for _, s in sorted(deletions)[:limits['removal_shortlist']]]
        additions = (proposals(sources, current, limits['addition_shortlist']) if candidate_pool is None
                     else [s for s in candidate_pool if s not in current['vocab']][:limits['addition_shortlist']])
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
        if best_move and objective != 'compact':
            best, pruned = prune(sources, best, width, alphabet=alphabet,
                                 allow_partial=allow_partial, boundaries=boundaries)
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
