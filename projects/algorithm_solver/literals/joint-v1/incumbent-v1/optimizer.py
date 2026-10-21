"""Bounded adaptation of existing exact-DP/joint search. Source bytes are data."""
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations
import hashlib
import importlib.util
import json
import math
import os
import resource
import statistics
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


core = module('exact_core', HERE.parent / 'reachable_core.py')
codec = module('frozen_codec', HERE.parent.parent / 'readable-v1/literal_codec.py')


def brief(state):
    return {key: state[key] for key in ['coverage', 'denominator', 'uncovered', 'unreachable_variants',
                                       'selections', 'dictionary_bytes', 'packet_bytes', 'package_bytes']}


def frontier(states):
    unique = {}
    for state in states:
        unique[state['vocab']] = state
    values = list(unique.values())
    def dominates(a, b):
        aa = (-a['coverage'], a['selections'], a['package_bytes'])
        bb = (-b['coverage'], b['selections'], b['package_bytes'])
        return all(x <= y for x, y in zip(aa, bb)) and aa != bb
    return [s for s in values if not any(dominates(other, s) for other in values)]


def rank_additions(state, index, pool):
    boundaries = {}
    for key, parts in state['parsed'].items():
        if parts is None:
            continue
        pos = 0
        locations = {0: 0}
        for n, part in enumerate(parts, 1):
            pos += len(part)
            locations[pos] = n
        boundaries[key] = locations
    ranks = []
    for fragment in set(pool) - set(state['vocab']):
        owners = {}
        hits = index.get(fragment)
        for key, positions in hits.items():
            locations = boundaries.get(key, {})
            gain = sum(max(0, locations[p+len(fragment)] - locations[p] - 1)
                       for p in positions if p in locations and p+len(fragment) in locations)
            owners[key[0]] = max(gain, owners.get(key[0], 0))
        ranks.append((-sum(owners.values()), -len({p for p, _ in hits}), len(fragment.encode()), fragment))
    return [r[-1] for r in sorted(ranks)[:8]]


def optimize(sources, initial, pool, coordinated, width, expired, *, max_rounds=3, max_trials=96, observe=None):
    if type(max_rounds) is not int or type(max_trials) is not int or min(max_rounds, max_trials) < 0:
        raise ValueError("Nonnegative integer search bounds required")
    began = time.process_time()
    index = core.Occurrences(sources)
    current = initial
    states = [initial]
    trace = []
    parity = trials = forward = 0
    def check(state):
        nonlocal forward
        assert core.audit(sources, state, width)
        forward += 1
    check(initial)
    if observe is not None:
        observe(initial, "initial")
    # Finite source-vocabulary block moves address a real local-search barrier:
    # several new helper/provider identifiers may need to become expressible at once.
    for name, seed in sorted(coordinated.items()):
        if expired() or trials >= max_trials:
            trace.append({'kind': 'budget-stop', 'phase': 'coordinated', 'next_seed': name})
            break
        table = set(seed['literals'])
        if len(table) > 2**width:
            trace.append({'kind': 'coordinated', 'name': name, 'skipped': 'entry cap', 'entries': len(table)})
            continue
        assert table <= set(pool)
        state = core.evaluate(sources, table, width, mandatory=())
        trials += 1
        states.append(state)
        check(state)
        trace.append({'kind': 'coordinated', 'name': name, 'dictionary': list(state['vocab']),
                      'result': brief(state), 'choices': state['chosen']})
        if core.cost(state) < core.cost(current):
            current = state
            if observe is not None:
                observe(current, "coordinated:" + name)
    stop = f'{max_rounds}-round bound'
    for round_no in range(max_rounds):
        if expired() or trials >= max_trials:
            stop = 'budget bound'
            break
        tested = set()
        attempts = []
        best = current
        best_move = None
        def consider(remove=(), add=()):
            nonlocal trials, parity, best, best_move
            candidate = set(current['vocab']) - set(remove) | set(add)
            identity = tuple(sorted(candidate))
            if not candidate or len(candidate) > 2**width or identity in tested or expired() or trials >= max_trials:
                return None
            tested.add(identity)
            trials += 1
            cached = core.evaluate(sources, candidate, width, current, (), index)
            if expired():
                attempts.append({'remove': list(remove), 'add': list(add), 'status': 'expiry-before-parity', 'qualified_trial': False})
                return None
            full = core.evaluate(sources, candidate, width, mandatory=())
            assert core.comparable(cached) == core.comparable(full)
            parity += 1
            states.append(cached)
            move = {'remove': list(remove), 'add': list(add), 'result': brief(cached), 'choices': cached['chosen']}
            attempts.append(move)
            if core.cost(cached) < core.cost(best):
                best, best_move = cached, move
            return cached
        frequency = Counter(p for pid, v in current['chosen'].items() for p in current['parsed'][(pid, v)])
        deletions = sorted(current['vocab'], key=lambda p: (frequency[p], -len(p.encode()), p))[:6]
        harms = []
        for piece in deletions:
            state = consider(remove=[piece])
            if state is not None:
                harms.append((core.cost(state), piece))
        removals = [piece for _, piece in sorted(harms)[:4]]
        additions = rank_additions(current, index, pool)
        for piece in additions:
            consider(add=[piece])
        for add, remove in list((a, r) for a in additions[:4] for r in removals)[:8]:
            consider(remove=[remove], add=[add])
        for pair in list(combinations(additions[:4], 2))[:4]:
            needed = max(0, len(current['vocab']) + 2 - 2**width)
            for remove in list(combinations(removals, needed))[:1]:
                consider(remove=remove, add=pair)
        if best_move:
            check(best)
            used = {p for pid, v in best['chosen'].items() for p in best['parsed'][(pid, v)]}
            if used != set(best['vocab']) and not expired() and trials < max_trials:
                smaller = core.evaluate(sources, used, width, best, (), index)
                if not expired():
                    full = core.evaluate(sources, used, width, mandatory=())
                    assert core.comparable(smaller) == core.comparable(full)
                    assert smaller['coverage'] == best['coverage'] and smaller['selections'] == best['selections']
                    parity += 1
                    check(smaller)
                    states.append(smaller)
                    best = smaller
        trace.append({'kind': 'local', 'round': round_no+1, 'before': brief(current),
                      'attempts': attempts, 'accepted': best_move, 'after': brief(best),
                      'dictionary_after': list(best['vocab'])})
        current = best
        if observe is not None:
            observe(current, "round:" + str(round_no + 1))
        if best_move is None:
            stop = 'budget bound' if expired() or trials >= max_trials else 'no improving tested move'
            break
    check(current)
    if expired() or trials >= max_trials:
        stop = 'budget bound'
    pareto_complete = not expired()
    retained = frontier(states) if pareto_complete else [initial, current]
    return current, {'trials': trials, 'cached_full_parity_checks': parity,
                     'forward_audits': forward, 'cpu_seconds': time.process_time()-began,
                     'stop': stop, 'trace': trace, 'max_rounds': max_rounds, 'max_trials': max_trials,
                     'pareto_complete': pareto_complete,
                     'pareto': [{**brief(s), 'choices': s['chosen'], 'dictionary': list(s['vocab'])}
                                for s in retained]}

