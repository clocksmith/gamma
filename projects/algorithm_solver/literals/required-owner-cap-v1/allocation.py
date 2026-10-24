"""Item 61 supplied-input finite allocation; no loaders or scientific replay.

``allocate`` merges next available owner marginals with a heap. ``independent``
uses a separate validator and global residual sort, never calling production
helpers. Both retain finite zero slots and tie by owner ID then rank. Row ties
choose fewer one-owner slots. Prefix inputs are accepted numerical authorities,
not freshly verified full-graph certificates. Integers are arbitrary precision.

With M owners, A supplied marginal entries and capacity B, production uses
O(A + M log(M+1) + B log(M+1) + B**2) time and O(M+B) auxiliary
space. Independent replay uses O(A log(A+1) + M log(M+1) + B**2)
time and O(A+B+M) space. The B**2 row scan is bounded
by the supplied capacity, not by full-substring entry counts.
"""
import heapq


def _validate(prefixes, shared, forced, L, D, B):
    if not __debug__:
        raise RuntimeError('normal assertions required')
    assert type(prefixes) is dict
    assert all(type(pid) is str for pid in prefixes)
    assert type(forced) is list and all(type(pid) is str for pid in forced)
    assert forced == sorted(set(forced)) and set(forced) <= prefixes.keys()
    assert type(L) is int and type(D) is int and D > 0
    assert type(B) is int and B >= 0
    for values in [shared, *prefixes.values()]:
        assert type(values) is list and values
        assert all(type(v) is int and v >= 0 for v in values)
        assert values[0] == 0
        previous = None
        for left, right in zip(values, values[1:]):
            step = right - left
            assert step >= 0 and (previous is None or step <= previous)
            previous = step
    assert all(len(prefixes[pid]) > 1 for pid in forced), 'forced owner has no available entry'


def allocate(capped_prefixes, shared_prefix, forced, L, D, B=256):
    """Exact required-owner charge curve for k=0..B; no feasibility assertion."""
    _validate(capped_prefixes, shared_prefix, forced, L, D, B)
    r = len(forced)
    totals, choices, counts, mandatory = {}, [], None, None
    if r <= B:
        required = set(forced)
        counts = {pid: int(pid in required) for pid in sorted(capped_prefixes)}
        mandatory = sum(capped_prefixes[pid][1] for pid in forced)
        totals[r] = mandatory
        heap = []
        for pid, values in capped_prefixes.items():
            rank = counts[pid] + 1
            if rank < len(values):
                heapq.heappush(heap, (values[rank-1]-values[rank], pid, rank))
        while heap and r + len(choices) < B:
            negative, pid, rank = heapq.heappop(heap)
            assert rank == counts[pid] + 1
            counts[pid] = rank
            choices.append((pid, rank, -negative))
            j = r + len(choices)
            totals[j] = totals[j-1] - negative
            rank += 1
            values = capped_prefixes[pid]
            if rank < len(values):
                heapq.heappush(heap, (values[rank-1]-values[rank], pid, rank))
    rows = []
    for k in range(B+1):
        if k < r:
            rows.append(dict(k=k, empty_by_required_owners=True, one_owner_slots=None,
                             shared_slots=None, charge=None, numerator=None, integer_lower_bound=None))
        else:
            charge, minus_j = max((value + shared_prefix[min(B-j, len(shared_prefix)-1)], -j)
                                  for j, value in totals.items() if j <= k)
            j = -minus_j
            numerator = L-charge
            rows.append(dict(k=k, empty_by_required_owners=False, one_owner_slots=j,
                             shared_slots=min(B-j, len(shared_prefix)-1), charge=charge,
                             numerator=numerator, integer_lower_bound=-(-numerator//D)))
    return dict(coverage_floor=r, mandatory_value=mandatory, required_owner_prefix=totals,
                remaining_marginal_choices=choices, final_owner_counts=counts, rows=rows)


def independent(capped_prefixes, shared_prefix, forced, L, D, B=256):
    """Isolated sort-based replay, including its own validation and row scan."""
    if not __debug__:
        raise RuntimeError('normal assertions required')
    assert type(capped_prefixes) is dict
    assert type(forced) is list
    assert all(type(key) is str for key in capped_prefixes)
    assert all(type(key) is str for key in forced)
    assert len(set(forced)) == len(forced) and sorted(forced) == forced
    assert all(key in capped_prefixes for key in forced)
    assert type(L) is int
    assert type(D) is int and D >= 1
    assert type(B) is int and B >= 0
    for vector in list(capped_prefixes.values()) + [shared_prefix]:
        assert type(vector) is list and len(vector) >= 1
        assert all(type(value) is int and value >= 0 for value in vector)
        assert vector[0] == 0
        deltas = [vector[i]-vector[i-1] for i in range(1, len(vector))]
        assert all(value >= 0 for value in deltas)
        assert deltas == sorted(deltas, reverse=True)
    for pid in forced:
        assert len(capped_prefixes[pid]) >= 2, 'forced owner has no available entry'
    r = len(forced)
    mandatory, counts, totals, choices = None, None, {}, []
    if r <= B:
        required = set(forced)
        counts = {pid: (1 if pid in required else 0) for pid in sorted(capped_prefixes)}
        mandatory = sum(capped_prefixes[pid][counts[pid]] for pid in counts)
        totals[r] = mandatory
        residual = []
        for pid, vector in capped_prefixes.items():
            for rank in range(counts[pid]+1, len(vector)):
                residual.append((vector[rank]-vector[rank-1], pid, rank))
        residual.sort(key=lambda item: (-item[0], item[1], item[2]))
        value = mandatory
        for gain, pid, rank in residual[:B-r]:
            assert rank == counts[pid]+1
            counts[pid] += 1
            choices.append((pid, rank, gain))
            value += gain
            totals[r+len(choices)] = value
    rows = []
    for k in range(B+1):
        if k < r:
            rows.append({'k': k, 'empty_by_required_owners': True, 'one_owner_slots': None,
                         'shared_slots': None, 'charge': None, 'numerator': None, 'integer_lower_bound': None})
            continue
        best, slots, shared_slots = None, None, None
        for j in sorted(totals):
            if j > k:
                break
            s = min(B-j, len(shared_prefix)-1)
            candidate = totals[j] + shared_prefix[s]
            if best is None or candidate > best:
                best, slots, shared_slots = candidate, j, s
        assert best is not None
        numerator = L-best
        quotient, remainder = divmod(numerator, D)
        rows.append({'k': k, 'empty_by_required_owners': False, 'one_owner_slots': slots,
                     'shared_slots': shared_slots, 'charge': best, 'numerator': numerator,
                     'integer_lower_bound': quotient + int(remainder != 0)})
    return {'coverage_floor': r, 'mandatory_value': mandatory, 'required_owner_prefix': totals,
            'remaining_marginal_choices': choices, 'final_owner_counts': counts, 'rows': rows}
