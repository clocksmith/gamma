"""Supplied-input mathematical prototype; no loader, optimizer or launcher."""
import heapq
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'support_budget_length_sensitive',
    Path(__file__).resolve().parents[1] / 'length-sensitive-fraction-v1/implicit.py')
parent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parent)
LADDER = (0, 1, 2, 4, 8, 16, 32, 64, 128, 256)


def support_classes(index):
    """1 means one distinct source, 2 means at least two (not exact support)."""
    positions = index.base.positions
    transitions = [0] * len(positions)
    for i in range(1, len(positions)):
        transitions[i] = transitions[i-1] + (positions[i][0] != positions[i-1][0])
    groups = []
    for g in index.base.groups:
        assert 0 <= g['lo'] < g['hi'] <= len(positions)
        groups.append(1 if transitions[g['hi']-1] == transitions[g['lo']] else 2)
    return [groups[p['group']] for p in index.pieces]


def weighted_pieces(index, q):
    """Weights count all occurrences, including repeated/overlapping ones."""
    weights = [0] * len(index.pieces)
    for b, indices in enumerate(index.by_bin):
        prefix = [0]
        for pid, start in index.base.positions:
            prefix.append(prefix[-1] + q[pid][start][b])
        for i in indices:
            p = index.pieces[i]
            weights[i] = prefix[p['hi']] - prefix[p['lo']]
    return weights


def top_slots(records, capacity):
    """Each record is (nonnegative weight, positive multiplicity, piece ID).

    The best B pieces suffice for the best B entries because every retained
    piece contains at least one entry. Expand at most B scalar slots, no words.
    """
    assert type(capacity) is int and capacity >= 0
    def checked():
        for weight, count, ident in records:
            assert type(weight) is int and weight >= 0
            assert type(count) is int and count >= 1
            yield weight, count, ident
    best = heapq.nsmallest(capacity, checked(), key=lambda r: (-r[0], r[2]))
    slots = []
    for weight, count, ident in best:
        slots.extend([(weight, ident)] * min(count, capacity-len(slots)))
        if len(slots) == capacity:
            break
    prefix = [0]
    for weight, ident in slots:
        prefix.append(prefix[-1] + weight)
    return prefix


def capacity_term(one, shared, capacity, k):
    """Exact maximum; prefix arrays represent actual slots, never padding."""
    assert type(k) is int and 0 <= k <= capacity
    candidates = []
    for j in range(min(k, capacity, len(one)-1)+1):
        h = min(capacity-j, len(shared)-1)
        candidates.append((one[j]+shared[h], -j, h))
    value, negative_j, h = max(candidates)  # ties use fewer one-owner slots
    return {'weight': value, 'one_owner_slots': -negative_j, 'shared_slots': h}


def certificate(index, q, capacity=256, denominator=1000000, ladder=LADDER):
    parent.validate_q(index.texts, q, capacity, denominator)
    assert ladder and list(ladder) == sorted(set(ladder))
    assert all(type(k) is int and 0 <= k <= capacity for k in ladder)
    # Unchanged35 paths, with no capacity deduction. This is NOT a new witness.
    paths = index.certificate(q, 0, denominator)
    classes = support_classes(index)
    weights = weighted_pieces(index, q)
    prefixes = {}
    counts = {}
    for support in (1, 2):
        records = [(weights[i], p['multiplicity'], i)
                   for i, p in enumerate(index.pieces)
                   if classes[i] == support and p['multiplicity']]
        counts[support] = sum(r[1] for r in records)
        prefixes[support] = top_slots(records, capacity)
    rows = []
    for k in ladder:
        selected = capacity_term(prefixes[1], prefixes[2], capacity, k)
        numerator = paths['numerator'] - selected['weight']
        rows.append({'k': k, 'numerator': numerator,
                     'integer_lower_bound': -(-numerator // denominator), **selected})
    assert all(a['numerator'] >= b['numerator'] for a, b in zip(rows, rows[1:]))
    return {'denominator': denominator, 'path_numerators': paths['path_numerators'],
            'one_owner_entries': counts[1], 'shared_entries': counts[2], 'rows': rows}
