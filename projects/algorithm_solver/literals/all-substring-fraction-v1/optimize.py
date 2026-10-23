"""Bounded ascent in the start-tied dual; all retained bounds use exact integers."""
import math
import sys
import time
from pathlib import Path
import numpy as np
import implicit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'fraction-capacity-v1'))
import dual


def optimize(index, seed, capacity, cfg, trace):
    assert len(seed) == len(set(seed)) and len(seed) <= capacity
    assert all(seed) and not set(seed) & index.banned
    # Entries never occurring in this fixed population cannot help an encoding.
    occurring_seed = []
    for word in seed:
        lo, hi = implicit.occurrence_interval(index.texts, index.positions, word)
        if lo < hi:
            occurring_seed.append(word)
    seed = occurring_seed
    seed_cost = dual.objective(index.texts, seed)
    upper, best_vocab = seed_cost, list(seed)
    generated_vocab = None
    generated_cost = None
    lam = {pid: np.zeros(len(text), dtype=float) for pid, text in index.texts.items()}
    best_q, best_cert = None, None
    theta, stall = 1., 0
    started = time.monotonic()
    stop, executed, attempts, infeasible = 'iteration_limit', 0, 0, 0
    denominator = cfg['denominator']
    for iteration in range(cfg['iterations']):
        if time.monotonic() - started >= cfg['seconds']:
            stop = 'time_limit'
            break
        assert all(np.all(np.isfinite(values)) and np.all(values >= 0) for values in lam.values())
        q = {pid: [math.floor(float(value)*denominator) for value in values] for pid, values in lam.items()}
        cert = index.certificate(q, capacity, denominator)
        if best_cert is None or cert['numerator'] > best_cert['numerator']:
            best_cert, best_q = cert, q
            stall = 0
        else:
            stall += 1
        if stall >= cfg['halve_after']:
            theta /= 2
            stall = 0
        if iteration % cfg['primal_every'] == 0:
            # Two fully specified choices within each equal-weight depth group.
            for longest in (False, True):
                vocab = index.selected_vocabulary(cert['selected_groups'], longest_first=longest)
                attempts += 1
                try:
                    value = dual.objective(index.texts, vocab)
                except ValueError:
                    infeasible += 1
                    continue
                if generated_cost is None or value < generated_cost:
                    generated_cost, generated_vocab = value, vocab
                if value < upper:
                    upper, best_vocab = value, vocab
        assert cert['numerator'] <= upper*denominator
        selected = index.selected_occurrences(cert['selected_groups'])
        gradient = {pid: np.asarray(cert['path_starts'][pid])-np.asarray(selected[pid]) for pid in lam}
        norm = sum(int(values @ values) for values in gradient.values())
        trace({'iteration': iteration, 'integer_lower_bound': cert['integer_lower_bound'],
               'best_integer_lower_bound': best_cert['integer_lower_bound'],
               'exact_numerator': cert['numerator'], 'upper_bound': upper,
               'generated_objective': generated_cost, 'theta': theta,
               'seconds': time.monotonic()-started})
        executed += 1
        if best_cert['integer_lower_bound'] == upper:
            stop = 'exact_primal_optimum_certificate'
            break
        if norm == 0:
            stop = 'restricted_dual_stationary'
            break
        step = theta * ((upper*denominator-cert['numerator'])/denominator) / norm
        for pid in lam:
            # Update from the exact point whose minimizing paths supplied g.
            lam[pid] = np.maximum(0., np.asarray(q[pid], dtype=float)/denominator + step*gradient[pid])
    if best_cert is None:
        raise RuntimeError('no completed dual iteration')
    assert implicit.verify(index, best_q, capacity, denominator) == best_cert['numerator']
    summary = {key: value for key, value in best_cert.items() if key not in ('path_starts', 'selected_groups')}
    summary['independent_partition_and_integer_replay'] = True
    summary['excludes_ten_percent'] = summary['integer_lower_bound'] > 0
    return {'seed_objective': seed_cost, 'best_objective': upper,
            'generated_objective': generated_cost, 'certificate': summary,
            'iterations': executed, 'stop': stop, 'primal_attempts': attempts,
            'primal_infeasible': infeasible, 'seconds': time.monotonic()-started}, best_q, seed, best_vocab, generated_vocab
