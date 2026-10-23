"""Weighted literal search that never invents a missing fallback character.

Search proposals may be infeasible. They are counted and rejected, while a
replacement can restore coverage even when its deletion-only probe cannot.
"""
import importlib.util
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
spec = importlib.util.spec_from_file_location('stack_weighted_legacy', LIT / 'character-objective-v1/search.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
analyze = legacy.analyze
Budget = legacy.Budget
ALPHABET = [chr(i) for i in range(32, 127)] + ['\n']


def order(vocab):
    """Order only entries actually supplied; no mandatory-alphabet insertion."""
    values = set(vocab)
    if not all(isinstance(s, str) and s for s in values):
        raise ValueError('entries must be nonempty strings')
    known = {s: i for i, s in enumerate(ALPHABET)}
    return sorted(values, key=lambda s: (0, known.get(s, len(known)), s) if len(s) == 1 else (1, 0, s))


def evaluate(texts, vocab, weight, budget, *, relaxed=False):
    budget.trials += 1
    vocab = order(vocab)
    if len(vocab) > (512 if relaxed else 256):
        raise ValueError('dictionary capacity exceeded')
    tree = legacy.trie(vocab)
    parsed = {}
    try:
        for pid, text in sorted(texts.items()):
            seq = legacy.encode(text, vocab, weight, tree)
            parsed[pid] = tuple(vocab[i] for i in seq)
    except ValueError:
        budget.coverage_failures = getattr(budget, 'coverage_failures', 0) + 1
        return None
    n = sum(len(parts) for parts in parsed.values())
    c = sum(len(word) == 1 for parts in parsed.values() for word in parts)
    db = len(analyze.dictionary_bytes(vocab))
    pb = sum(41 + len(parts) for parts in parsed.values())
    return dict(vocab=vocab, parsed=parsed, selections=n, characters=c,
                objective=4*n + weight*c, package_bytes=db+pb,
                dictionary_bytes=db, packet_bytes=pb, weight=weight)


def key(state):
    return state['objective'], state['selections'], state['characters'], state['package_bytes']


def best_move(texts, state, reserved, banned, neighborhood, budget):
    vocab = set(state['vocab'])
    removable = sorted(vocab - set(reserved))
    weight = state['weight']
    best, move, tested = None, None, set()

    def consider(remove=(), add=(), relaxed=False):
        nonlocal best, move
        proposal = (vocab - set(remove)) | set(add)
        identity = (tuple(sorted(proposal)), relaxed)
        if (identity in tested or budget.expired() or
                not set(reserved) <= proposal or proposal & banned or
                (not relaxed and len(proposal) > 256)):
            return None
        tested.add(identity)
        result = evaluate(texts, proposal, weight, budget, relaxed=relaxed)
        if result is not None and not relaxed and key(result) < key(best or state):
            best, move = result, {'remove': list(remove), 'add': list(add)}
        return result

    harm = {}
    for word in removable:
        result = consider(remove=[word])
        # Keep infeasible removals eligible: adding a new literal may bridge the hole.
        harm[word] = None if result is None else result['objective'] - state['objective']
    proposed = legacy.propose(texts, state, neighborhood['additions'], banned)
    missing_chars = sorted(set(''.join(texts.values())) - vocab - banned)
    additions = list(dict.fromkeys(missing_chars + proposed))
    gain = {}
    for word in additions:
        result = consider(add=[word], relaxed=len(vocab) >= 256)
        if result is not None:
            gain[word] = state['objective'] - result['objective']
    # Unknown deletion harm is a conservative screening rank, not infeasibility
    # of a swap. They remain eligible, but the shortlist cap can screen them out.
    def estimate(word):
        return 10**12 if harm[word] is None else harm[word]
    swaps = sorted(((gain[a]-estimate(r), r, a) for r in removable for a in gain),
                   key=lambda x: (-x[0], x[1], x[2]))
    for _, remove, add in swaps[:neighborhood['swaps']]:
        consider(remove=[remove], add=[add])
    top = sorted(gain, key=lambda a: (-gain[a], a))[:neighborhood['pair_additions']]
    low = sorted(removable, key=lambda r: (estimate(r), r))[:neighborhood['pair_removals']]
    need = max(0, len(vocab)+2-256)
    doubles = sorted(((gain[a]+gain[b]-sum(estimate(r) for r in rem), rem, (a,b))
                      for a,b in combinations(top, 2) for rem in combinations(low, need)),
                     key=lambda x: (-x[0], x[1], x[2]))
    for _, remove, add in doubles[:neighborhood['pairs']]:
        consider(remove=remove, add=add)
    return best, move


def optimize(texts, vocab, weight, reserved, banned, neighborhood, limits):
    budget = Budget(limits)
    budget.coverage_failures = 0
    if not set(reserved) <= set(vocab) or set(vocab) & set(banned):
        raise ValueError('illegal initial dictionary')
    state = evaluate(texts, vocab, weight, budget)
    if state is None:
        raise ValueError('initial dictionary has a coverage hole')
    log = []
    stop = 'local_optimum'
    while not budget.expired():
        candidate, move = best_move(texts, state, set(reserved), set(banned), neighborhood, budget)
        if candidate is None:
            stop = budget.reason() if budget.expired() else 'local_optimum'
            break
        assert key(candidate) < key(state)
        state = candidate
        log.append({'move': move, 'objective': state['objective'],
                    'selections': state['selections'], 'characters': state['characters'],
                    'entries': len(state['vocab']), 'trials': budget.trials})
    else:
        stop = budget.reason()
    assert set(reserved) <= set(state['vocab']) and not set(state['vocab']) & set(banned)
    return state, dict(trials=budget.trials, seconds=budget.elapsed(), stop=stop,
                       coverage_failures=budget.coverage_failures, trace=log)
