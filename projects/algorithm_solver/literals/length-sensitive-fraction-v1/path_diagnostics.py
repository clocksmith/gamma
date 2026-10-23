"""Post-report descriptive path-bin replay; no search or new qualification."""
import argparse
import json
from pathlib import Path

import bin_diagnostics as activation
from backend import dual, sha, write
import implicit

HERE = Path(__file__).resolve().parent


def path_counts(texts, q, certificate, denominator):
    counts = [0] * len(implicit.BINS)
    covered = [0] * len(counts)
    penalty = [0] * len(counts)
    objectives = {}
    for pid, text in texts.items():
        starts = certificate['path_starts'][pid]
        points = [(i, row.index(1)) for i, row in enumerate(starts) if sum(row)]
        assert points and points[0][0] == 0
        assert all(sum(row) in (0, 1) and all(v in (0, 1) for v in row) for row in starts)
        objective = 0
        for k, (start, b) in enumerate(points):
            end = points[k + 1][0] if k + 1 < len(points) else len(text)
            length = end - start
            assert implicit.bin_index(length) == b
            counts[b] += 1
            covered[b] += length
            penalty[b] += q[pid][start][b]
            objective += (9 if length == 1 else -1) * denominator + q[pid][start][b]
        assert objective == certificate['path_numerators'][pid]
        objectives[pid] = objective
    assert sum(covered) == sum(map(len, texts.values()))
    return summary(counts, covered, penalty), objectives


def summary(counts, covered, penalty=None):
    total = sum(counts)
    return {'edges': total, 'source_bytes': sum(covered),
            'bins': [{'bin': b, 'edges': n, 'edge_share': n / total if total else None,
                      'covered_bytes': covered[b],
                      **({'q_penalty_numerator': penalty[b]} if penalty is not None else {})}
                     for b, n in enumerate(counts)],
            'length_129_plus_edges': sum(counts[9:]),
            'length_129_plus_edge_share': sum(counts[9:]) / total if total else None,
            'length_129_plus_covered_bytes': sum(covered[9:])}


def seed_counts(texts, vocab, witness):
    counts = [0] * len(implicit.BINS)
    covered = [0] * len(counts)
    for pid, text in texts.items():
        value, seq = dual.encode_objective(text, vocab)
        assert ''.join(vocab[i] for i in seq) == text
        row = witness['per_problem'][pid]
        assert value == row['objective'] and len(seq) == row['selections']
        assert sum(len(vocab[i]) == 1 for i in seq) == row['characters']
        for i in seq:
            length = len(vocab[i]); b = implicit.bin_index(length)
            counts[b] += 1; covered[b] += length
    return summary(counts, covered)


def build(run, work):
    # Includes complete independent certificate, source, receipt and pin replay.
    bins = activation.build(run, work)
    c = json.loads((HERE / 'contract.json').read_text())
    evidence = json.loads((HERE / 'evidence/results.json').read_text())
    arms = []
    for clean in evidence['arms']:
        cohort = clean['cohort']; folder = run / f'{cohort}-flex256'
        texts = json.loads((work / c['cohorts'][cohort] / 'fit-sources.json').read_text())
        q = json.loads((folder / 'certificate-q.json').read_text())
        index = implicit.Index(texts, dual.sel.forbidden_strings(texts))
        cert = index.certificate(q, c['pool']['capacity'], c['search']['denominator'])
        assert cert['numerator'] == clean['certificate']['numerator']
        paths, values = path_counts(texts, q, cert, c['search']['denominator'])
        independent = implicit.heap_paths(texts, q, c['search']['denominator'],
                                         implicit.independently_relocate_bans(index.base))
        assert values == independent
        dictionary = folder / 'seed' / 'dictionary.json'
        assert sha(dictionary) == clean['witnesses']['seed']['dictionary_sha256']
        seed = seed_counts(texts, json.loads(dictionary.read_text()), clean['witnesses']['seed'])
        activation_arm = next(a for a in bins['arms'] if a['cohort'] == cohort)
        arms.append({'cohort': cohort, 'relaxed_minimum_path': paths,
                     'feasible_seed_min_F_path': seed,
                     'activation_length_129_plus_entries': activation_arm['upper_two_bins']['selected_entries'],
                     'certificate_numerator': cert['numerator']})
    return {'schema': 'gamma.length-sensitive-fraction.path-diagnostics.v1',
            'complete': True, 'validation_loaded': False, 'arms': arms,
            'contract_sha256': sha(HERE / 'contract.json'),
            'main_evidence_sha256': sha(HERE / 'evidence/results.json'),
            'code_sha256': sha(Path(__file__)),
            'scope': 'Descriptive deterministic final-q relaxed paths versus retained feasible seed min-F paths.',
            'limitation': 'Not a causal decomposition of dual slack; path ties can change bin attribution. No new witness or search.'}


def self_test():
    for text in ('abababc', 'abcdefghij', 'a' * 270):
        texts = {'toy': text}
        index = implicit.Index(texts, {text})
        q = {'toy': [[(i * 3 + b) % 17 for b in range(11)] for i in range(len(text))]}
        cert = index.certificate(q, 4, 10)
        result, values = path_counts(texts, q, cert, 10)
        assert result['source_bytes'] == len(text)
        assert values == implicit.heap_paths(texts, q, 10, implicit.independently_relocate_bans(index.base))
    bad = json.loads(json.dumps(cert)); bad['path_numerators']['toy'] += 1
    try:
        path_counts(texts, q, bad, 10)
    except AssertionError:
        pass
    else:
        raise AssertionError('corrupt path cost accepted')
    print('3 synthetic path replays and cost-corruption rejection passed')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--run', type=Path)
    p.add_argument('--work', type=Path); p.add_argument('--self-test', action='store_true')
    args = p.parse_args()
    if args.self_test:
        self_test()
    else:
        write(HERE / 'evidence/path-diagnostics.json', build(args.run, args.work))
