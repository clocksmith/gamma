"""Supplied-input item57 checker; isolated adaptation of item53 independent replay.
No loader, search, execution entry point, or production-kernel dependency.

Shared dependencies: item 33's compressed Index and its accepted interval/
suffix-order/ban completeness verifier. Scalar work is separate: Aho-Corasick
old occurrence enumeration, end-ordered path relaxation, same-owner run ends,
and EVERY allowed group depth, including unique occurrences. No prototype
code, range-maximum selection, or optimized unique-occurrence RMQ is used.
"""
from bisect import bisect_left
from collections import deque
import hashlib
import heapq
import importlib.util
import json
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'owner_path_cap_independent_full_index',
    Path(__file__).resolve().parents[1] / 'all-substring-fraction-v1/implicit.py')
full = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(full)


class Matcher:
    """End-order occurrences with terminal links, not copied output lists."""
    def __init__(self, words):
        self.words = words
        self.go, self.fail, self.terminal, self.output = [{}], [0], [None], [None]
        for eid, word in enumerate(words):
            at = 0
            for ch in word:
                if ch not in self.go[at]:
                    self.go[at][ch] = len(self.go)
                    self.go.append({}); self.fail.append(0)
                    self.terminal.append(None); self.output.append(None)
                at = self.go[at][ch]
            assert self.terminal[at] is None
            self.terminal[at] = eid
        queue = deque(self.go[0].values())
        while queue:
            at = queue.popleft()
            for ch, child in self.go[at].items():
                fallback = self.fail[at]
                while fallback and ch not in self.go[fallback]:
                    fallback = self.fail[fallback]
                fallback = self.go[fallback].get(ch, 0)
                self.fail[child] = fallback
                self.output[child] = (fallback if self.terminal[fallback] is not None
                                      else self.output[fallback])
                queue.append(child)

    def occurrences(self, text):
        at = 0
        for end, ch in enumerate(text, 1):
            while at and ch not in self.go[at]:
                at = self.fail[at]
            at = self.go[at].get(ch, 0)
            terminal = at if self.terminal[at] is not None else self.output[at]
            while terminal is not None:
                eid = self.terminal[terminal]
                yield end-len(self.words[eid]), end, eid
                terminal = self.output[terminal]


class TopList:
    """Sorted bounded list, independent of the prototype's bounded heap."""
    def __init__(self, capacity):
        self.capacity, self.keys = capacity, []

    def add(self, weight, group, length):
        if not self.capacity:
            return
        key = (-weight, group, length)
        if len(self.keys) == self.capacity and key >= self.keys[-1]:
            return
        self.keys.insert(bisect_left(self.keys, key), key)
        if len(self.keys) > self.capacity:
            self.keys.pop()

    def entries(self):
        return [(-weight, group, length) for weight, group, length in self.keys]


def _allocations(top, counts, capacity, total, denominator):
    # Enumerate each feasible one-owner allocation once and offer it to every
    # permissive k; this does not call the prototype's per-k maximization.
    prefixes = {}
    for support in (1, 2):
        prefixes[support] = [0]
        for weight, _, _ in top[support]:
            prefixes[support].append(prefixes[support][-1]+weight)
    best = [None]*(capacity+1)
    for one in range(min(capacity, counts[1])+1):
        shared = min(capacity-one, counts[2])
        candidate = (prefixes[1][one]+prefixes[2][shared], -one, shared)
        for k in range(one, capacity+1):
            if best[k] is None or candidate > best[k]:
                best[k] = candidate
    rows = []
    for k, (charge, negative_one, shared) in enumerate(best):
        numerator = total-charge
        lower, remainder = divmod(numerator, denominator)
        rows.append({'k': k, 'charge': charge, 'one_owner_slots': -negative_one,
                     'shared_slots': shared, 'numerator': numerator,
                     'integer_lower_bound': lower+bool(remainder)})
    return rows


def check(texts, banned, old_pool, old_q, seed, alphabet, D, *,
          expected_source_hashes, expected_old_banned,
          expected_old_certificate=None, expected_occurrence_sha256=None,
          capacity=256, expected_prefix_schedule=None):
    """Return independently rebuilt scalar terms; all arguments are in memory.

    Optional old certificate uses item 28's public certificate field names,
    including its path-numerator list in sorted source-ID order.
    File hashes, source/body-ban derivation, and private provenance remain the
    future caller's responsibility. This function opens no supplied paths.
    Capacity is parameterized for tiny exhaustive tests; production is 256.
    """
    if not __debug__:
        raise RuntimeError('independent replay requires assertions')
    assert type(D) is int and D > 0
    assert type(capacity) is int and capacity >= 0
    assert isinstance(texts, dict) and texts
    assert all(type(pid) is str and type(text) is str and text
               for pid, text in texts.items())
    assert expected_source_hashes == {
        pid: hashlib.sha256(text.encode()).hexdigest() for pid, text in texts.items()}
    banned = set(banned)
    assert all(type(word) is str and word for word in banned)
    assert banned == set(expected_old_banned)
    assert all(type(word) is str and word for word in old_pool)
    assert list(old_pool) == sorted(set(old_pool))
    assert not banned.intersection(old_pool)
    assert len(seed) == len(set(seed)) and set(seed) <= set(old_pool)
    assert all(type(word) is str and len(word) == 1 for word in alphabet)
    assert set(alphabet) <= set(old_pool)
    assert set(''.join(texts.values())) <= set(alphabet)
    assert all(type(q) is int and q >= 0 for q in old_q)

    index = full.Index(texts, banned)
    # Reuse the accepted item33 verifier specifically for partition completeness,
    # generalized Kasai suffix geometry and exact ban exclusions. Its q0 scalar
    # result is discarded; it is not a check of this occurrence-based lift.
    full.verify(index, {pid: [0]*len(text) for pid, text in texts.items()}, 0, 1)
    assert index.texts == texts and index.banned == banned
    positions = index.positions
    ranks = {position: rank for rank, position in enumerate(positions)}
    interval_group = {(g['lo'], g['hi']): gid for gid, g in enumerate(index.groups)}
    assert len(interval_group) == len(index.groups)
    run_end = [0]*len(positions)
    for rank in range(len(positions)-1, -1, -1):
        run_end[rank] = (run_end[rank+1] if rank+1 < len(positions)
                         and positions[rank][0] == positions[rank+1][0] else rank+1)
    support = [1 if g['hi'] <= run_end[g['lo']] else 2 for g in index.groups]

    matcher = Matcher(old_pool)
    old_owners = [set() for _ in old_pool]
    weights = [0]*len(old_pool)
    tightened_weights = [0]*len(old_pool)
    reduced_occurrences = multiplier_reduction = 0
    low, high, occurrences = [len(positions)]*len(old_pool), [-1]*len(old_pool), [0]*len(old_pool)
    potentials, paths, cursor = {}, {}, 0
    digest = hashlib.sha256()
    bellman_edges = 0
    for pid, text in sorted(texts.items()):
        by_start = [[] for _ in text]
        for start, end, eid in matcher.occurrences(text):
            by_start[start].append((end, eid))
            old_owners[eid].add(pid)
        incoming = [[] for _ in range(len(text)+1)]
        for start, matches in enumerate(by_start):
            previous_end = start
            for end, eid in matches:
                assert end > previous_end
                previous_end = end
                assert cursor < len(old_q), 'missing occurrence multiplier'
                q = old_q[cursor]; cursor += 1
                digest.update((json.dumps([pid, start, end, eid], separators=(',', ':'))+'\n').encode())
                weight = (9 if end-start == 1 else -1)*D+q
                incoming[end].append((start, weight, eid, q))
                weights[eid] += q
                rank = ranks[pid, start]
                low[eid], high[eid] = min(low[eid], rank), max(high[eid], rank)
                occurrences[eid] += 1
        # Forward end-order paths from source start, independent of the
        # prototype's outgoing-edge backward recurrence.
        forward = [0]+[None]*len(text)
        for end in range(1, len(text)+1):
            choices = [forward[start]+cost for start, cost, _, _ in incoming[end]
                       if forward[start] is not None]
            forward[end] = min(choices) if choices else None
        assert forward[-1] is not None
        # Forward relaxation on the reversed DAG obtains all suffix potentials.
        distance, tight = [None]*len(text)+[0], [None]*len(text)
        for end in range(len(text), 0, -1):
            assert distance[end] is not None
            for start, cost, _, _ in incoming[end]:
                candidate = distance[end]+cost
                if distance[start] is None or candidate < distance[start]:
                    distance[start], tight[start] = candidate, (end, cost)
        assert all(value is not None for value in distance)
        assert forward[-1] == distance[0]
        for end, edges in enumerate(incoming):
            for start, cost, eid, q in edges:
                assert distance[start] <= cost+distance[end]
                base = (9 if end-start == 1 else -1)*D
                minimum = max(0, distance[start]-distance[end]-base)
                assert 0 <= minimum <= q
                if distance[start] == cost+distance[end]: assert minimum == q
                tightened_weights[eid] += minimum
                reduced_occurrences += minimum < q
                multiplier_reduction += q-minimum
                bellman_edges += 1
        for start, (end, cost) in enumerate(tight):
            assert start < end <= len(text) and distance[start] == cost+distance[end]
        potentials[pid], paths[pid] = distance, forward[-1]
    assert cursor == len(old_q), 'extra occurrence multiplier'
    occurrence_sha256 = digest.hexdigest()
    if expected_occurrence_sha256 is not None:
        assert occurrence_sha256 == expected_occurrence_sha256

    old_entries = {}
    for eid, word in enumerate(old_pool):
        if not occurrences[eid]:
            assert word in seed or word in alphabet
            assert weights[eid] == 0
            continue
        assert high[eid]+1-low[eid] == occurrences[eid]
        gid = interval_group[low[eid], high[eid]+1]
        group = index.groups[gid]
        length = len(word)
        assert group['first'] <= length <= group['last']
        assert length not in group['excluded_lengths']
        assert (support[gid] == 2 and length >= 2) or word in seed or word in alphabet
        assert (gid, length) not in old_entries
        old_entries[gid, length] = eid

    owner_tops = {pid: TopList(capacity) for pid in sorted(texts)}
    owner_counts = dict.fromkeys(sorted(texts), 0)
    tops = {name: {1: TopList(capacity), 2: TopList(capacity)}
            for name in ('lifted', 'tightened', 'new_only')}
    new_counts = {1: 0, 2: 0}
    counts = {1: 0, 2: 0}
    new_entries, new_occurrences, streamed_depths = 0, 0, 0
    for gid, group in enumerate(index.groups):
        excluded = set(group['excluded_lengths'])
        group_count = 0
        for length in range(group['first'], group['last']+1):
            if length in excluded:
                continue
            streamed_depths += 1; group_count += 1
            counts[support[gid]] += 1
            if (gid, length) in old_entries:
                eid = old_entries[gid, length]
                lifted_weight, tight_weight = weights[eid], tightened_weights[eid]
            else:
                # Completeness of the old shared pool/alphabet is checked at
                # every individual depth, not inferred from a matching count.
                assert support[gid] == 1 and length >= 2, 'missing old shared/character entry'
                weight = 0; new_entries += 1
                for rank in range(group['lo'], group['hi']):
                    pid, start = positions[rank]
                    difference = potentials[pid][start]-potentials[pid][start+length]+D
                    penalty = difference if difference > 0 else 0
                    assert penalty-D+potentials[pid][start+length] >= potentials[pid][start]
                    weight += penalty; new_occurrences += 1
                new_counts[support[gid]] += 1
                tops['new_only'][support[gid]].add(weight, gid, length)
                lifted_weight = tight_weight = weight
            assert 0 <= tight_weight <= lifted_weight
            if support[gid] == 1:
                owner = positions[group['lo']][0]
                owner_counts[owner] += 1
                owner_tops[owner].add(tight_weight, gid, length)
            elif (gid, length) in old_entries:
                assert len(old_owners[old_entries[gid, length]]) >= 2
            tops['lifted'][support[gid]].add(lifted_weight, gid, length)
            tops['tightened'][support[gid]].add(tight_weight, gid, length)
        assert group_count == group['multiplicity']
    assert streamed_depths == index.distinct_allowed_entries == sum(counts.values())
    entries = {name: {s: top[s].entries() for s in (1, 2)} for name, top in tops.items()}
    assert all(len(entries[name][s]) == min(capacity, counts[s])
               for name in ('lifted', 'tightened') for s in (1, 2))
    total = sum(paths.values())
    old_charge = sum(heapq.nlargest(capacity, weights))
    old_numerator = total-old_charge
    if expected_old_certificate is not None:
        rebuilt = {'denominator': D, 'numerator': old_numerator,
                   'integer_lower_bound': -(-old_numerator//D),
                   'relaxed_paths_numerator': total, 'top_capacity_numerator': old_charge,
                   'per_program_path_numerators': [paths[pid] for pid in sorted(paths)]}
        for key, value in rebuilt.items():
            if isinstance(value, list):
                assert type(expected_old_certificate[key]) is list
                assert all(type(number) is int for number in expected_old_certificate[key])
            else:
                assert type(expected_old_certificate[key]) is int
            assert expected_old_certificate[key] == value, ('old certificate', key)
    proofs = {}
    common = {'denominator': D, 'path_numerators': paths, 'old_charge': old_charge,
              'old_numerator': old_numerator, 'class_counts': counts,
              'old_occurrences': cursor, 'occurrence_sha256': occurrence_sha256}
    for name in ('lifted', 'tightened'):
        rows = _allocations(entries[name], counts, capacity, total, D)
        assert rows[0]['numerator'] >= old_numerator
        assert all(a['charge'] <= b['charge'] for a, b in zip(rows, rows[1:]))
        unrestricted = sum(heapq.nlargest(capacity,
            (w for values in entries[name].values() for w, _, _ in values)))
        assert rows[-1]['charge'] == unrestricted
        proofs[name] = {**common, 'top_entries': entries[name], 'rows': rows}
    deltas = []
    for before, after in zip(proofs['lifted']['rows'], proofs['tightened']['rows']):
        assert after['charge'] <= before['charge']
        assert after['numerator'] >= before['numerator']
        assert after['integer_lower_bound'] >= before['integer_lower_bound']
        deltas.append({'k': before['k'], 'charge_reduction': before['charge']-after['charge'],
                       'integer_bound_gain': after['integer_lower_bound']-before['integer_lower_bound']})
    assert sum(weights)-sum(tightened_weights) == multiplier_reduction
    assert all(a >= b >= 0 for a, b in zip(weights, tightened_weights))
    reductions = {'old_occurrences_reduced': reduced_occurrences,
        'old_multiplier_reduction': multiplier_reduction,
        'old_entries_reduced': sum(a > b for a, b in zip(weights, tightened_weights)),
        'occurring_old_entries': len(old_entries), 'absent_old_entries': len(old_pool)-len(old_entries),
        'strict_charge_budgets': sum(row['charge_reduction'] > 0 for row in deltas),
        'strict_integer_bound_budgets': sum(row['integer_bound_gain'] > 0 for row in deltas)}
    digests = {'potentials_sha256': canonical_digest(potentials),
               'old_weights_sha256': canonical_digest(weights),
               'tightened_old_weights_sha256': canonical_digest(tightened_weights),
               'new_only_top_sha256': canonical_digest(entries['new_only'])}
    for name, proof in proofs.items():
        digests[name+'_proof_sha256'] = canonical_digest(proof)
        digests[name+'_top_entries_sha256'] = canonical_digest(proof['top_entries'])
        digests[name+'_rows_sha256'] = canonical_digest(proof['rows'])
    base = {'schema': 'gamma.potential-tightening.supplied.v1', **proofs,
            'new_only_class_counts': new_counts, 'new_only_top_entries': entries['new_only'],
            'digests': digests, 'reductions': reductions, 'deltas': deltas,
            'geometry': {'source_characters': len(positions), 'full_groups': len(index.groups),
                         'full_distinct_entries': index.distinct_allowed_entries,
                         'exact_ban_occurrences': sum(len(ends) for rows in index.banned_ends.values() for ends in rows)},
            'work': {'old_occurrences_tightened': cursor, 'old_bellman_edges_checked': bellman_edges,
                     'tight_suffix_positions_checked': sum(map(len, texts.values())),
                     'streamed_allowed_depths': streamed_depths,
                     'new_entries_streamed': new_entries,
                     'new_occurrence_contributions': new_occurrences},
            'shared_dependency': 'item33 Index and verify partition/suffix/ban checks',
            'scalar_replay': 'AC/end-order paths; owner-run ends; all-depth exact sums'}

    # Independent scheduling ownership uses freshly matched old-pool owner sets,
    # not suffix-group support thresholds. Every allowed shared entry was proved
    # present above. Among allowed endpoints, a length is shared exactly when
    # it does not exceed the longest allowed shared match: every allowed prefix
    # of that match also occurs in its other source. Banned endpoints are removed
    # independently below; no assumption that banned lengths form a prefix.
    longest_shared = {pid: [0]*len(text) for pid, text in texts.items()}
    schedule_matcher = Matcher(old_pool)
    schedule_old_occurrences = 0
    for pid, text in sorted(texts.items()):
        for start, end, eid in schedule_matcher.occurrences(text):
            schedule_old_occurrences += 1
            if len(old_owners[eid]) >= 2:
                longest_shared[pid][start] = max(longest_shared[pid][start], end-start)
    assert schedule_old_occurrences == cursor
    banned_ends = {pid: [set() for _ in text] for pid, text in texts.items()}
    ban_matcher = Matcher(sorted(banned))
    for pid, text in sorted(texts.items()):
        for start, end, _ in ban_matcher.occurrences(text):
            banned_ends[pid][start].add(end)
    assert banned_ends == index.banned_ends
    schedules, caps = {}, {}
    inspected = admitted = 0
    for pid, text in sorted(texts.items()):
        distance = potentials[pid]
        values = [0]*(len(text)+1)
        for start in range(len(text)-1, -1, -1):
            best = values[start+1]  # free auxiliary skip, not a decoder escape
            for end in range(start+1, len(text)+1):
                inspected += 1
                if end in banned_ends[pid][start] or end-start <= longest_shared[pid][start]:
                    continue
                base_cost = (9 if end-start == 1 else -1)*D
                qstar = max(0, distance[start]-distance[end]-base_cost)
                best = max(best, qstar+values[end])
                admitted += 1
            values[start] = best
        schedules[pid], caps[pid] = values, values[0]
    forward_positions_checked = forward_arcs_inspected = 0
    if expected_prefix_schedule is not None:
        assert type(expected_prefix_schedule) is dict and expected_prefix_schedule.keys() == texts.keys()
        for pid, text in sorted(texts.items()):
            supplied = expected_prefix_schedule[pid]
            assert type(supplied) is list and len(supplied) == len(text)+1
            assert all(type(value) is int and value >= 0 for value in supplied)
            assert supplied[0] == 0
            distance = potentials[pid]
            for end in range(1, len(text)+1):
                best = supplied[end-1]
                for start in range(end):
                    forward_arcs_inspected += 1
                    if end in banned_ends[pid][start] or end-start <= longest_shared[pid][start]:
                        continue
                    qstar = max(0, distance[start]-distance[end]-(9 if end-start == 1 else -1)*D)
                    best = max(best, supplied[start]+qstar)
                assert supplied[end] == best, ('forward recurrence', pid, end)
                forward_positions_checked += 1
            assert supplied[-1] == caps[pid]
    owner_entries = {pid: top.entries() for pid, top in owner_tops.items()}
    assert sum(owner_counts.values()) == counts[1]
    assert all(len(owner_entries[p]) == min(capacity, owner_counts[p]) for p in texts)
    owner_prefixes = {}
    capped_prefixes = {}
    marginals = []
    for pid, values in owner_entries.items():
        prefix = [0]
        for weight, _, _ in values:
            prefix.append(prefix[-1]+weight)
        owner_prefixes[pid] = prefix
        capped = [min(value, caps[pid]) for value in prefix]
        capped_prefixes[pid] = capped
        increments = [b-a for a, b in zip(capped, capped[1:])]
        assert increments == sorted(increments, reverse=True) and all(v >= 0 for v in increments)
        marginals.extend((value, pid, rank) for rank, value in enumerate(increments, 1))
    marginals.sort(key=lambda item: (-item[0], item[1], item[2]))
    choices = marginals[:capacity]
    one_prefix = [0]
    allocated = dict.fromkeys(texts, 0)
    for value, pid, rank in choices:
        assert rank == allocated[pid]+1
        allocated[pid] += 1
        one_prefix.append(one_prefix[-1]+value)
    shared_prefix = [0]
    for weight, _, _ in entries['tightened'][2]:
        shared_prefix.append(shared_prefix[-1]+weight)
    rows, delta57 = [], []
    for k in range(capacity+1):
        options = [(one_prefix[j]+shared_prefix[min(capacity-j, counts[2])], -j)
                   for j in range(min(k, len(one_prefix)-1)+1)]
        charge, negative_j = max(options)
        j = -negative_j
        numerator = total-charge
        row = {'k': k, 'charge': charge, 'one_owner_slots': j,
               'shared_slots': min(capacity-j, counts[2]), 'numerator': numerator,
               'integer_lower_bound': -(-numerator//D)}
        prior = proofs['tightened']['rows'][k]
        assert charge <= prior['charge']
        rows.append(row)
        delta57.append({'k': k, 'charge_reduction': prior['charge']-charge,
                        'integer_bound_gain': row['integer_lower_bound']-prior['integer_lower_bound']})
    output = {'schema': 'gamma.owner-path-cap.supplied.v1', 'base': base,
              'owner_caps': caps, 'owner_top_entries': owner_entries,
              'owner_entry_counts': owner_counts, 'owner_prefixes': owner_prefixes,
              'capped_prefixes': capped_prefixes, 'owner_suffix_schedule': schedules,
              'one_owner_prefix': one_prefix, 'marginal_choices': [(p, rank, value) for value, p, rank in choices],
              'shared_prefix': shared_prefix, 'rows': rows, 'deltas_vs53': delta57,
              'work': {'owner_entries_streamed': sum(owner_counts.values()),
                       'owner_top_entries_retained': sum(map(len, owner_entries.values())),
                       'schedule_old_occurrences': schedule_old_occurrences,
                       'schedule_endpoints_inspected': inspected, 'schedule_occurrences_admitted': admitted,
                       'banned_occurrences_matched': sum(len(ends) for vector in banned_ends.values() for ends in vector),
                       'marginals_sorted': len(marginals),
                       'production_forward_positions_checked': forward_positions_checked,
                       'production_forward_endpoints_inspected': forward_arcs_inspected},
              'shared_dependency': 'item33 Index and verify partition/suffix/ban checks',
              'scalar_replay': 'isolated item53 AC replay; bounded sorted owner tops; fresh AC shared/ban matching; backward schedule; sorted marginals'}
    output['digests'] = {key+'_sha256': canonical_digest(output[key]) for key in
                        ('owner_caps', 'owner_top_entries', 'owner_entry_counts', 'owner_suffix_schedule',
                         'owner_prefixes', 'capped_prefixes', 'one_owner_prefix', 'marginal_choices', 'shared_prefix', 'rows', 'deltas_vs53')}
    output['production_forward_schedule_checked'] = expected_prefix_schedule is not None
    output['production_forward_schedule_sha256'] = (canonical_digest(expected_prefix_schedule)
        if expected_prefix_schedule is not None else None)
    output['digests']['base_paired_sha256'] = canonical_digest({key: base[key] for key in
        ('lifted', 'tightened', 'new_only_class_counts', 'new_only_top_entries', 'digests', 'reductions', 'deltas')})
    return output


def canonical_digest(value):
    def convert(item):
        if isinstance(item, dict): return {str(key): convert(val) for key, val in item.items()}
        if isinstance(item, (tuple, list)): return [convert(val) for val in item]
        return item
    raw = json.dumps(convert(value), sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()
