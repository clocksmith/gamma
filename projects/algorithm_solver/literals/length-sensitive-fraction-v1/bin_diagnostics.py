"""Unpinned post-report diagnostic; no optimization or partial-run inspection.

Rebuild the frozen full-substring index and verify final q before emitting only
numeric multiplicities, activation-weight totals and tie diagnostics by bin.
"""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path.insert(0, str(HERE))
import implicit
from backend import analyze, dual, sha, write

CERT_KEYS = ('numerator', 'denominator', 'integer_lower_bound',
             'path_numerators', 'top_capacity_numerator')


def fraction(numerator, denominator):
    return numerator/denominator if denominator else None


def summarize(index, q, capacity, denominator):
    """Independently verify the point, then count the frozen deterministic top B."""
    numerator = implicit.verify(index, q, capacity, denominator)
    certificate = index.certificate(q, capacity, denominator)
    assert certificate['numerator'] == numerator
    weights = [0]*len(index.pieces)
    for b in range(len(implicit.BINS)):
        prefix = [0]
        for pid, start in index.base.positions:
            prefix.append(prefix[-1]+q[pid][start][b])
        for piece_id, piece in enumerate(index.pieces):
            if piece['bin'] == b:
                weights[piece_id] = prefix[piece['hi']]-prefix[piece['lo']]
    # Replay the exact registered tie order rather than selecting an arbitrary
    # equal-weight maximizer and interpreting its bins as unique evidence.
    selected, left = [], capacity
    for piece_id in sorted(range(len(weights)), key=lambda k: (-weights[k], k)):
        count = min(left, index.pieces[piece_id]['multiplicity'])
        if count:
            selected.append((piece_id, count))
            left -= count
        if not left:
            break
    assert selected == certificate['selected_pieces']
    bins = [{'bin': b, 'minimum_length': low, 'maximum_length': high,
             'selected_entries': 0, 'selected_pieces': 0,
             'positive_weight_selected_entries': 0, 'zero_weight_selected_entries': 0,
             'activation_weight_numerator': 0}
            for b, (low, high) in enumerate(implicit.BINS)]
    for piece_id, count in selected:
        row = bins[index.pieces[piece_id]['bin']]
        row['selected_entries'] += count
        row['selected_pieces'] += 1
        row['activation_weight_numerator'] += count*weights[piece_id]
        row['positive_weight_selected_entries' if weights[piece_id] > 0
            else 'zero_weight_selected_entries'] += count
    total = sum(row['selected_entries'] for row in bins)
    weight = sum(row['activation_weight_numerator'] for row in bins)
    assert total == min(capacity, index.distinct_allowed_entries)
    assert weight == certificate['top_capacity_numerator']
    positive = sum(row['positive_weight_selected_entries'] for row in bins)
    zeros = total-positive
    for row in bins:
        row['selected_multiplicity_share'] = fraction(row['selected_entries'], total)
        row['activation_weight_share'] = fraction(row['activation_weight_numerator'], weight)
    cutoff = weights[selected[-1][0]] if selected else None
    tied_pool = (sum(piece['multiplicity'] for k, piece in enumerate(index.pieces) if weights[k] == cutoff)
                 if cutoff is not None else 0)
    tied_selected = (sum(count for k, count in selected if weights[k] == cutoff)
                     if cutoff is not None else 0)
    tied_pool_by_bin = [0]*len(implicit.BINS)
    if cutoff is not None:
        for k, piece in enumerate(index.pieces):
            if weights[k] == cutoff:
                tied_pool_by_bin[piece['bin']] += piece['multiplicity']
    upper_count = sum(bins[b]['selected_entries'] for b in (9, 10))
    upper_weight = sum(bins[b]['activation_weight_numerator'] for b in (9, 10))
    all_zero = total > 0 and positive == 0
    ambiguous = 0 < tied_selected < tied_pool
    ambiguous_bins = ambiguous and sum(count > 0 for count in tied_pool_by_bin) > 1
    result = {'capacity': capacity, 'selected_entries': total,
              'positive_weight_selected_entries': positive,
              'positive_weight_selected_share': fraction(positive, total),
              'zero_weight_selected_entries': zeros,
              'zero_weight_selected_share': fraction(zeros, total),
              'all_selected_weights_zero': all_zero,
              'top_capacity_weight_numerator': weight,
              'weight_denominator': denominator,
              'cutoff_weight_numerator': cutoff,
              'cutoff_tied_pool_entries': tied_pool,
              'cutoff_tied_selected_entries': tied_selected,
              'cutoff_tied_pool_entries_by_bin': tied_pool_by_bin,
              'cutoff_selection_nonunique': ambiguous,
              'cutoff_bin_counts_nonunique': ambiguous_bins,
              'bin_attribution_nonidentifying': all_zero or ambiguous_bins,
              'bins': bins,
              'upper_two_bins': {'bins': [9, 10], 'minimum_length': 129,
                                 'selected_entries': upper_count,
                                 'selected_multiplicity_share': fraction(upper_count, total),
                                 'activation_weight_numerator': upper_weight,
                                 'activation_weight_share': fraction(upper_weight, weight)}}
    return result, certificate


def build(run, work):
    implicit.require_checks()
    cpath = HERE/'contract.json'
    c = json.loads(cpath.read_text())
    contract_hash = sha(cpath)
    # This intentionally requires the independently completed main report.
    # It will not inspect a partial/live run to produce provisional diagnostics.
    evidence_path = HERE/'evidence/results.json'
    evidence = json.loads(evidence_path.read_text())
    assert evidence['complete'] is True and evidence['validation_loaded'] is False
    assert evidence['contract_sha256'] == contract_hash
    assert not (run/'failure.json').exists() and not list(run.glob('*/failure.json'))
    raw_path = run/'results.json'
    assert sha(raw_path) == evidence['private_results_sha256']
    raw = json.loads(raw_path.read_text())
    assert raw['complete'] is True and raw['validation_loaded'] is False
    assert raw['contract_sha256'] == contract_hash
    for rel, digest in c['code_hashes'].items():
        assert sha(LIT/rel) == digest, rel
    for path, digest in c['runtime_files'].items():
        assert sha(Path(path)) == digest, path
    assert [list(bounds) for bounds in implicit.BINS] == c['length_bins']
    proof_path = LIT/'binding-descent-v1/evidence/results.json'
    assert sha(proof_path) == c['code_hashes']['binding-descent-v1/evidence/results.json']
    proof = json.loads(proof_path.read_text())
    assert len(raw['arms']) == len(evidence['arms']) == 2
    assert {a['cohort'] for a in raw['arms']} == {a['cohort'] for a in evidence['arms']} == {'R', 'naming'}
    arms = []
    for arm in sorted(raw['arms'], key=lambda a: a['cohort']):
        cohort = arm['cohort']; private = run/f'{cohort}-flex256'
        assert arm['complete'] is True and arm['validation_loaded'] is False
        assert json.loads((private/'results.json').read_text()) == arm
        assert json.loads((private/'status.json').read_text()) == {'phase': 'complete', 'complete': True}
        clean = next(row for row in evidence['arms'] if row['cohort'] == cohort)
        source_rel = c['cohorts'][cohort]+'/fit-sources.json'
        source_hash = sha(work/source_rel)
        assert source_hash == c['private_files'][source_rel] == arm['fit_source_sha256'] == clean['fit_source_sha256']
        texts = json.loads((work/source_rel).read_text())
        assert set(texts) == set(map(str, c['fit_ids'])) and len(texts) == 300
        receipt = next(row for row in proof['arms'] if row['width'] == 8 and
                       row['arm'] == ('control' if cohort == 'R' else 'scope_joint'))
        for pid, text in texts.items():
            assert receipt['qualification'][pid]['passed'] is True
            assert analyze.sha(text.encode()) == receipt['per_problem'][pid]['source_sha256']
        qpath = private/'certificate-q.json'
        q_hash = sha(qpath)
        assert q_hash == arm['optimization']['certificate']['q_sha256'] == clean['certificate']['q_sha256']
        q = json.loads(qpath.read_text())
        index = implicit.Index(texts, dual.sel.forbidden_strings(texts))
        diagnostic, certificate = summarize(index, q, c['pool']['capacity'], c['search']['denominator'])
        for key in CERT_KEYS:
            assert certificate[key] == arm['optimization']['certificate'][key] == clean['certificate'][key]
        assert index.distinct_allowed_entries == arm['pool_entries'] == clean['pool_entries']
        assert len(index.pieces) == arm['length_pieces'] == clean['length_pieces']
        arms.append({'cohort': cohort, 'fit_problems': len(texts),
                     'fit_source_sha256': source_hash, 'q_sha256': q_hash,
                     'certificate_numerator': certificate['numerator'],
                     'integer_lower_bound': certificate['integer_lower_bound'],
                     'independent_certificate_replayed': True, **diagnostic})
    return {'schema': 'gamma.length-sensitive-fraction.bin-diagnostics.v1',
            'complete': True, 'validation_loaded': False,
            'contract_sha256': contract_hash, 'main_evidence_sha256': sha(evidence_path),
            'private_results_sha256': sha(raw_path), 'diagnostic_code_sha256': sha(Path(__file__)),
            'arms': arms,
            'scope': 'Descriptive final-q relaxed top-capacity dictionary term; not a feasible witness dictionary.',
            'tie_rule': 'Frozen descending activation weight, then piece index; multiplicity within each piece is counted exactly.',
            'interpretation': 'All-zero weights make bin attribution non-identifying; a partially selected cutoff tie '
                              'spanning multiple bins also makes bin counts nonunique. Ties confined to one bin leave '
                              'that bin count unchanged but do not identify particular entries. Zero-weight choices '
                              'reflect the deterministic tie rule. Long-bin concentration may describe '
                              'remaining length grouping but does not establish the cause of any bound weakness.',
            'zero_denominators': 'Multiplicity or weight shares are null when their respective denominator is zero.'}


def self_test():
    import random
    rng = random.Random(3509)
    cases = 0
    for _ in range(40):
        texts = {str(i): ''.join(rng.choices('abc', k=rng.randrange(2, 9))) for i in range(3)}
        index = implicit.Index(texts, set(texts.values()))
        q = {pid: [[rng.randrange(10) for _ in implicit.BINS] for _ in text] for pid, text in texts.items()}
        capacity = rng.randrange(1, 20)
        try:
            result, cert = summarize(index, q, capacity, 10)
        except ValueError:
            # A whole-source ban may also remove a character needed elsewhere.
            continue
        words = index.selected_vocabulary(cert['selected_pieces'])
        assert len(words) == len(set(words)) == result['selected_entries']
        expected_weights = []
        for word in words:
            b = implicit.bin_index(len(word))
            expected_weights.append(sum(q[pid][start][b] for pid, text in texts.items()
                                        for start in range(len(text)) if text.startswith(word, start)))
        for b, row in enumerate(result['bins']):
            chosen = [i for i, word in enumerate(words) if implicit.bin_index(len(word)) == b]
            assert row['selected_entries'] == len(chosen)
            assert row['activation_weight_numerator'] == sum(expected_weights[i] for i in chosen)
        pool = {text[i:j] for text in texts.values() for i in range(len(text))
                for j in range(i+1, len(text)+1)}-set(texts.values())
        full_weights = [sum(q[pid][start][implicit.bin_index(len(word))] for pid, text in texts.items()
                            for start in range(len(text)) if text.startswith(word, start)) for word in pool]
        cutoff = result['cutoff_weight_numerator']
        assert result['cutoff_tied_pool_entries'] == full_weights.count(cutoff)
        assert result['top_capacity_weight_numerator'] == sum(sorted(full_weights, reverse=True)[:capacity])
        cases += 1
    # Positive long-bin concentration with a cutoff tie larger than capacity.
    text = ''.join(chr(1000+i) for i in range(600))
    index = implicit.Index({'a': text}, {text})
    q = {'a': [[0]*11 for _ in text]}; q['a'][0][10] = 7
    result, _ = summarize(index, q, 256, 100)
    assert result['bins'][10]['selected_entries'] == 256
    assert result['upper_two_bins']['selected_multiplicity_share'] == 1
    assert result['upper_two_bins']['activation_weight_share'] == 1
    assert result['cutoff_selection_nonunique'] is True
    assert result['cutoff_bin_counts_nonunique'] is False
    assert result['cutoff_tied_pool_entries'] == 343
    # All-zero q: counts still sum to selected capacity, weight shares are null.
    index = implicit.Index({'a': 'abcde'}, {'abcde'})
    q = {'a': [[0]*11 for _ in 'abcde']}
    result, _ = summarize(index, q, 3, 10)
    assert result['selected_entries'] == result['zero_weight_selected_entries'] == 3
    assert result['all_selected_weights_zero'] and result['bin_attribution_nonidentifying']
    assert result['zero_weight_selected_share'] == 1
    assert all(row['activation_weight_share'] is None for row in result['bins'])
    assert result['upper_two_bins']['activation_weight_share'] is None
    # The actual denominator is smaller than 256 when the pool is smaller.
    result, _ = summarize(index, q, 256, 10)
    assert result['selected_entries'] == 14 and not result['cutoff_selection_nonunique']
    assert sum(row['selected_entries'] for row in result['bins']) == 14
    result, _ = summarize(index, q, 0, 10)
    assert result['selected_entries'] == 0 and result['cutoff_weight_numerator'] is None
    assert result['zero_weight_selected_share'] is None
    assert all(row['selected_multiplicity_share'] is None for row in result['bins'])
    return {'random_brute_force_cases': cases, 'long_bin_and_zero_weight_cases': 4,
            'passed': True, 'private_corpus_opened': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path)
    parser.add_argument('--work', type=Path)
    parser.add_argument('--output', type=Path, default=HERE/'evidence/bin-diagnostics.json')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
    else:
        if args.run is None or args.work is None:
            parser.error('--run and --work are required unless --self-test is used')
        result = build(args.run, args.work)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write(args.output, result)
