"""Tiny supplied-input packing multiplicity oracle; no loader or scalable kernel.

For each entry e, n_e = sum_p min(m_ep, floor(len(text_p)/len(e)))
upper-bounds its total uses on complete nonoverlapping paths. Replacing m_e
by n_e in floor(lambda/m_e) preserves the at-most-lambda removal per paid
entry. All substring occurrences and schedules are explicit here. String
lengths follow the ancestors' Python-character convention, including Unicode.
"""
import importlib.util
from pathlib import Path


def module(name, component):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).resolve().parents[1]/component/'proof.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


price63 = module('packing71_price63', 'entry-price-path-cap-v1')
global66 = module('packing71_global66', 'global-entry-price-cap-v1')
required68 = module('packing71_required68', 'required-entry-price-cap-v1')


def schedules(texts, incoming, price_count):
    """Explicit free-skip forward maximum for every source and supplied price."""
    vectors, caps = {}, {}
    for pid, text in sorted(texts.items()):
        vectors[pid], caps[pid] = [], []
        for index in range(price_count):
            values = [0]*(len(text)+1)
            for end in range(1, len(text)+1):
                values[end] = max([values[end-1]] +
                    [values[arc['start']]+arc['residuals'][index]
                     for arc in incoming[pid][end]])
            vectors[pid].append(values)
            caps[pid].append(values[-1])
    return vectors, caps


def certificate(texts, banned, q, lambdas, capacity=256, denominator=1):
    if not __debug__:
        raise RuntimeError('normal assertions required')
    assert type(texts) is dict and texts
    assert all(type(pid) is str and type(text) is str and text for pid, text in texts.items())
    assert type(capacity) is int and capacity >= 0
    assert type(denominator) is int and denominator > 0
    assert type(lambdas) is list and lambdas
    assert all(type(value) is int and value >= 0 for value in lambdas)
    assert lambdas == sorted(set(lambdas)) and lambdas[0] == 0
    assert not isinstance(banned, (str, bytes))
    banned = set(banned)
    assert all(type(word) is str and word for word in banned)
    assert type(q) is dict
    for edge, value in q.items():
        assert type(edge) is tuple and len(edge) == 3 and type(edge[0]) is str
        assert type(edge[1]) is type(edge[2]) is int
        assert type(value) is int and value >= 0
    edges = {(pid, start, end): text[start:end]
             for pid, text in sorted(texts.items()) for start in range(len(text))
             for end in range(start+1, len(text)+1) if text[start:end] not in banned}
    assert set(q) == set(edges), 'q must contain exactly every allowed occurrence'

    # Unchanged ancestor functions receive the same normalized inputs. None is
    # patched, and no ancestor result is modified by the new calculation.
    old63 = price63.certificate(texts, banned, q, lambdas, capacity, denominator)
    old66 = global66.certificate(texts, banned, q, lambdas, capacity, denominator)
    old68 = required68.certificate(texts, banned, q, lambdas, capacity, denominator)
    base = old63['base57']
    assert base == old66['base57'] == old68['base61']['base57']
    assert old63 == old68['base63']
    L, D, B = base['L'], denominator, capacity
    words = sorted(set(edges.values()))
    per_source = {word: {pid: 0 for pid in sorted(texts)} for word in words}
    for (pid, _, _), word in edges.items():
        per_source[word][pid] += 1
    per_source_packing = {
        word: {pid: min(count, len(texts[pid])//len(word)) for pid, count in counts.items()}
        for word, counts in per_source.items()}
    counts = {word: sum(values.values()) for word, values in per_source.items()}
    packing = {word: sum(per_source_packing[word].values()) for word in words}
    assert counts == old66['entry_occurrence_counts']
    assert all(0 < packing[word] <= counts[word] for word in words)

    all_incoming = {pid: [[] for _ in range(len(text)+1)] for pid, text in sorted(texts.items())}
    owner_incoming = {pid: [[] for _ in range(len(text)+1)] for pid, text in sorted(texts.items())}
    arcs = []
    for (pid, start, end), word in edges.items():
        arc = {'pid': pid, 'start': start, 'end': end, 'word': word,
               'q': q[pid, start, end], 'multiplicity': counts[word],
               'packing_multiplicity': packing[word],
               'residuals': [max(q[pid, start, end]-price//packing[word], 0) for price in lambdas]}
        arcs.append(arc)
        all_incoming[pid][end].append(arc)
        if base['support'][word] == pid:
            assert packing[word] == per_source_packing[word][pid]
            assert counts[word] == per_source[word][pid]
            owner_incoming[pid][end].append(arc)
    owner_schedules, owner_caps = schedules(texts, owner_incoming, len(lambdas))
    global_schedules, global_caps = schedules(texts, all_incoming, len(lambdas))
    for pid in texts:
        assert owner_schedules[pid][0] == base['owner_schedule_values'][pid]
        assert global_schedules[pid][0] == old66['price_schedules'][pid][0]
        for index, price in enumerate(lambdas):
            assert all(new <= old for new, old in zip(owner_schedules[pid][index], old63['price_schedules'][pid][price]))
            assert all(new <= old for new, old in zip(global_schedules[pid][index], old66['price_schedules'][pid][index]))

    affine, prefixes = {}, {}
    for pid, A in base['owner_prefixes'].items():
        affine[pid] = [min(price*t+cap for price, cap in zip(lambdas, owner_caps[pid])) for t in range(len(A))]
        prefixes[pid] = [min(a, line) for a, line in zip(A, affine[pid])]
        assert prefixes[pid][0] == 0
        increments = [right-left for left, right in zip(prefixes[pid], prefixes[pid][1:])]
        assert all(value >= 0 for value in increments) and increments == sorted(increments, reverse=True)
        assert all(new <= old for new, old in zip(prefixes[pid], old63['priced_prefixes'][pid]))

    # Reuse only61's pure finite concave-allocation helper. No padded entries:
    # zero gains retain their real rank and required zeros consume real slots.
    allocation = required68.required.required_allocation
    owner_totals, owner_choices, _ = allocation(prefixes, [], B)
    owner_prefix = [owner_totals[j] for j in range(len(owner_totals))]
    forced = old68['forced_owners']
    r = len(forced)
    required_totals, required_choices, mandatory = allocation(prefixes, forced, B)
    shared = base['shared_prefix']
    owner_rows, required_rows = [], []
    for k in range(B+1):
        charge, negative = max((value+shared[min(B-j, len(shared)-1)], -j)
                              for j, value in owner_totals.items() if j <= k)
        j = -negative
        numerator = L-charge
        assert charge <= old63['rows'][k]['charge']
        owner_rows.append({'k': k, 'charge': charge, 'one_owner_slots': j,
            'shared_slots': min(B-j, len(shared)-1), 'numerator': numerator,
            'integer_lower_bound': -(-numerator//D),
            'charge_reduction_vs63': old63['rows'][k]['charge']-charge,
            'charge_reduction_vs57': base['rows'][k]['charge']-charge})
        if k < r:
            required_rows.append({'k': k, 'empty_by_required_owners': True,
                **dict.fromkeys(('charge', 'one_owner_slots', 'shared_slots', 'numerator',
                                 'integer_lower_bound', 'charge_reduction_vs68', 'charge_reduction_vs_owner'))})
            continue
        req_charge, negative = max((value+shared[min(B-j, len(shared)-1)], -j)
                                  for j, value in required_totals.items() if j <= k)
        j = -negative
        numerator = L-req_charge
        assert req_charge <= old68['rows'][k]['charge'] and req_charge <= charge
        required_rows.append({'k': k, 'empty_by_required_owners': False,
            'charge': req_charge, 'one_owner_slots': j, 'shared_slots': min(B-j, len(shared)-1),
            'numerator': numerator, 'integer_lower_bound': -(-numerator//D),
            'charge_reduction_vs68': old68['rows'][k]['charge']-req_charge,
            'charge_reduction_vs_owner': charge-req_charge})

    global_price_rows = []
    for index, price in enumerate(lambdas):
        residual_cap = sum(values[index] for values in global_caps.values())
        entry_charge = price*B
        charge = entry_charge+residual_cap
        numerator = L-charge
        assert charge <= old66['price_rows'][index]['charge']
        global_price_rows.append({'lambda': price, 'entry_charge': entry_charge,
            'residual_cap': residual_cap, 'charge': charge, 'numerator': numerator,
            'integer_lower_bound': -(-numerator//D)})
    winner = min(range(len(lambdas)), key=lambda index: (global_price_rows[index]['charge'], lambdas[index]))
    global_row = dict(global_price_rows[winner], price_index=winner)
    global_rows = []
    for k, old in enumerate(base['rows']):
        charge = min(old['charge'], global_row['charge'])
        numerator = L-charge
        assert charge <= old66['rows'][k]['charge']
        global_rows.append({'k': k, 'charge': charge, 'baseline57_charge': old['charge'],
            'global_charge': global_row['charge'], 'numerator': numerator,
            'integer_lower_bound': -(-numerator//D),
            'charge_reduction_vs57': old['charge']-charge,
            'charge_reduction_vs66': old66['rows'][k]['charge']-charge})
    return {'base57': base, 'old63': old63, 'old66': old66, 'old68': old68,
        'capacity': B, 'denominator': D, 'lambda_family': list(lambdas),
        'occurrence_counts_per_source': per_source, 'packing_counts_per_source': per_source_packing,
        'occurrence_counts': counts, 'packing_counts': packing, 'arcs': arcs,
        'owner_price_schedules': owner_schedules, 'owner_price_caps': owner_caps,
        'owner_affine_envelopes': affine, 'owner_priced_prefixes': prefixes,
        'owner_one_owner_prefix': owner_prefix, 'owner_marginal_choices': owner_choices,
        'owner_rows': owner_rows, 'forced_owners': list(forced), 'coverage_floor': r,
        'required_mandatory_value': mandatory, 'required_priced_prefix': required_totals,
        'required_marginal_choices': required_choices, 'required_rows': required_rows,
        'global_price_schedules': global_schedules, 'global_price_caps': global_caps,
        'global_price_rows': global_price_rows, 'global': global_row, 'global_rows': global_rows}
