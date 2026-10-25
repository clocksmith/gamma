"""Bounded exhaustive finite-U/V control. Text is data; no corpus loader/judge.

Reuse the explicit-basis exact lexicographic DPs and existing LTD1/LTV1 codec.
Dictionary enumeration never prunes by a local frontier: all subsets are visited.
"""
from __future__ import annotations
import hashlib
import importlib.util
import itertools
from fractions import Fraction
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
PROFILES = (16, 32, 64, 128, 256)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


seg = load('exact_frontier_segmentation', LIT/'explicit-basis-v2/segmentation.py')
codec = load('exact_frontier_codec', LIT/'readable-v1/literal_codec.py')
base = load('exact_frontier_literals', LIT/'literals.py')


def exact_path(source, dictionary):
    """None means unreachable; costs are N then actual Unicode singleton count."""
    if not dictionary:
        return None
    try:
        ids = seg.shortest_encode(source, list(dictionary))
    except ValueError as exc:
        if str(exc) == 'source cannot be represented':
            return None
        raise
    if seg.byte_encode(source.encode(), dictionary) != ids:
        raise AssertionError('independent byte/codepoint DP disagreement')
    if ''.join(dictionary[i] for i in ids) != source:
        raise AssertionError('reconstruction mismatch')
    return (len(ids), sum(len(dictionary[i]) == 1 for i in ids), tuple(ids))


def verify_claim(source, dictionary, ids, claimed_n, budget):
    """Dual inequalities alone never certify a selected path or its budget."""
    if any(type(i) is not int or not 0 <= i < len(dictionary) for i in ids):
        return False
    exact = exact_path(source, dictionary)
    return (exact is not None and ''.join(dictionary[i] for i in ids) == source
            and claimed_n == len(ids) == exact[0] and claimed_n <= budget
            and sum(len(dictionary[i]) == 1 for i in ids) == exact[1])


def median(values):
    values = sorted(values)
    n = len(values)
    return None if not n else Fraction(values[(n-1)//2] + values[n//2], 2)


def validate_variants(variants):
    if not variants or len(variants) > 12:
        raise ValueError('one to twelve explicit synthetic/authorized problems required')
    for pid, rows in variants.items():
        if not isinstance(pid, str) or not rows or len(rows) > 8:
            raise ValueError('invalid bounded variant mapping')
        if any(not isinstance(k, str) or not isinstance(s, str) or not s or len(s) > 4096
               for k, s in rows.items()):
            raise ValueError('nonempty bounded source strings required')
        for s in rows.values():
            s.encode('utf8')


def expansion_levels(variants, max_length):
    """Complete incremental adjacent-character merge closure, no top-K sweep.

    Each stage includes every witnessed substring up to its length. Whole sources
    of ANY supplied variant are banned, including unselected variants. Intermediate
    witnesses are not dictionary entries; all accepted entries store literal text.
    Real-pool body/helper legality must be supplied by the existing authority.
    """
    validate_variants(variants)
    if not 1 <= max_length <= 16:
        raise ValueError('bounded expansion length required')
    texts = [s for rows in variants.values() for s in rows.values()]
    banned = set(texts)
    universe = set()
    for length in range(1, max_length+1):
        universe.update(s[i:i+length] for s in texts for i in range(len(s)-length+1)
                        if s[i:i+length] not in banned)
        yield tuple(sorted(universe))


def metrics(dictionary, selected, variants, width):
    """Charge real serialized dictionary/packets and pinned standalone decoder."""
    packed = base.dictionary_bytes(list(dictionary))
    packets = []
    support = {i: [] for i in range(len(dictionary))}
    for pid, (key, path) in selected.items():
        text = variants[pid][key]
        ids = list(path[2])
        packet = codec.packet(ids, width, packed)
        codec.verify_packet(packet, packed, [s.encode() for s in dictionary], text.encode())
        packets.append(packet)
        for i in set(ids):
            support[i].append(pid)
    counts = sorted(p[0] for _, p in selected.values())
    n = sum(counts)
    c = sum(p[1] for _, p in selected.values())
    decoder_bytes = (LIT/'readable-v1/literal_codec.py').stat().st_size
    return dict(coverage=len(selected), denominator=len(variants), selections=n,
                characters=c, median=median(counts),
                p95=counts[(95*len(counts)+99)//100-1] if counts else None,
                entries=len(dictionary), width=width,
                selection_bits=n*width, character_bits=c*width,
                character_fraction=Fraction(c,n) if n else None,
                dictionary_bytes=len(packed), literal_utf8_bytes=sum(len(s.encode()) for s in dictionary),
                packet_bytes=sum(map(len,packets)), framing_bytes=41*len(packets),
                padding_bits=sum((-p[0]*width)%8 for _,p in selected.values()),
                decoder_bytes=decoder_bytes,
                package_bytes=len(packed)+sum(map(len,packets))+decoder_bytes,
                support=support, whole_source_entries=0)


def dominates(a, b):
    # Different covered populations cannot be made comparable by a prettier median.
    if tuple(a['selected']) != tuple(b['selected']):
        return False
    names = ('selections','characters','median','p95','entries','package_bytes')
    av, bv = a['metrics'], b['metrics']
    return all(av[k] <= bv[k] for k in names) and any(av[k] < bv[k] for k in names)


def solve(variants, universe, capacity, *, minimum_coverage=None, max_median=None,
          max_p95=None, max_character_fraction=None, max_evaluations=100000,
          seconds=20, legal=None):
    """Exhaustively co-select dictionary and source variants over explicit finite U/V.

    Exact segmentation per variant is mandatory. Enumerate source cross-products
    rather than independently pick shortest variants: aggregate gates can require
    a different source. Objective: minimum total N, then absolute C among feasible
    maximum-coverage states (all problems by default). No claim after truncation.
    """
    validate_variants(variants)
    if capacity not in PROFILES:
        raise ValueError('capacity must be 16/32/64/128/256')
    if not 0 < seconds <= 60 or not 0 < max_evaluations <= 1000000:
        raise ValueError('bounded time/evaluation budget required')
    if minimum_coverage is None:
        minimum_coverage = len(variants)
    if not 1 <= minimum_coverage <= len(variants):
        raise ValueError('invalid coverage gate')
    original = tuple(universe)
    if any(not isinstance(s,str) or not s for s in original) or len(set(original)) != len(original):
        raise ValueError('invalid finite literal universe')
    whole = {s for rows in variants.values() for s in rows.values()}
    universe = tuple(sorted(s for s in original if s not in whole and (legal is None or legal(s))))
    if len(universe) > 18:
        raise ValueError('exact control limited to 18 candidate literals; freeze smaller legal U')
    start = time.monotonic()
    width = capacity.bit_length()-1
    best = None
    frontier = []
    evaluations = 0
    dictionaries = 0
    complete = True
    for size in range(1, min(capacity,len(universe))+1):
        for dictionary in itertools.combinations(universe,size):
            if time.monotonic()-start >= seconds or evaluations >= max_evaluations:
                complete = False
                break
            dictionaries += 1
            options = {}
            for pid, rows in sorted(variants.items()):
                reachable = [(key,p) for key,text in sorted(rows.items())
                             if (p := exact_path(text,dictionary)) is not None]
                if reachable:
                    options[pid] = reachable
            if not options:
                continue
            for choices in itertools.product(*options.values()):
                if time.monotonic()-start >= seconds or evaluations >= max_evaluations:
                    complete = False
                    break
                evaluations += 1
                selected = dict(zip(options,choices))
                m = metrics(dictionary,selected,variants,width)
                row = dict(dictionary=dictionary, selected=selected, metrics=m,
                           unreachable=tuple(sorted(set(variants)-set(selected))))
                if not any(dominates(other,row) or (other['metrics'] == m and other['selected'] == selected)
                           for other in frontier):
                    frontier = [other for other in frontier if not dominates(row,other)] + [row]
                feasible = (m['coverage'] >= minimum_coverage
                            and (max_median is None or m['median'] <= max_median)
                            and (max_p95 is None or m['p95'] <= max_p95)
                            and (max_character_fraction is None or m['character_fraction'] <= max_character_fraction))
                objective = (-m['coverage'],m['selections'],m['characters'],m['package_bytes'],dictionary,tuple(selected.items()))
                if feasible and (best is None or objective < best[0]):
                    best = (objective,row)
            if not complete:
                break
        if not complete:
            break
    return dict(status=('optimal_finite_U_V' if best else 'infeasible_finite_U_V') if complete else 'incomplete_budget',
                complete=complete, best=best[1] if best else None, frontier=frontier,
                dictionaries=dictionaries, evaluations=evaluations, universe_entries=len(universe),
                excluded_whole_sources=len(set(original)&whole),
                scope='Only supplied finite U/V, exact shortest paths and stated gates; not global impossibility or M1.',
                candidate_execution=False, protected_access=False)
