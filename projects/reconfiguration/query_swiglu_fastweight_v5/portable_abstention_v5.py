"""Measure one cross-seed abstention threshold on stored Qwen development features.

Inputs are alternating bare/context rows. Only the table-removed marker is read.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def load(path):
    return json.loads(path.read_bytes())


def score_seed(dump, artifacts):
    study = load(artifacts / 'summary.json')
    index_bytes = (dump / 'index.json').read_bytes()
    index = json.loads(index_bytes)
    assert study['passed'] and index['split'] == 'dev'
    assert hashlib.sha256(index_bytes).hexdigest() == study['dataset']['indexSha256']
    receipts = {t['table']: t for t in study['tables']}
    results = []
    for table in index['tables']:
        key = table['specialty_id']
        header = load(artifacts / key / 'f16/classifier.json')
        data = (artifacts / key / 'f16/weights.bin').read_bytes()
        assert hashlib.sha256(data).hexdigest() == header['sha256']
        assert header['schema'] == 'gamma.linear-classifier/v1'
        assert header['model'] == index['model'] and header['table'] == key
        assert header['baseManifestSha256'] == study['dataset']['manifestSha256']
        assert header['codes'] == table['class_codes'] and header['layers'] == index['layers']
        assert header['endian'] == 'little' and header['dtype'] == 'f16'
        assert header['dimensions'] == [index['intermediate_size']] * len(index['layers'])
        width = sum(header['dimensions'])
        coeff = np.frombuffer(data, dtype='<f2').astype(np.float64).reshape(len(header['codes']), width + 1)

        def scores(file, row_count, marker_indices):
            contents = (dump / file).read_bytes()
            sha = hashlib.sha256(contents).hexdigest()
            frames = np.frombuffer(contents, dtype='<f4').reshape(row_count, index['row_floats'])
            x = frames[marker_indices, :width].astype(np.float64)
            values = x @ coeff[:, 1:].T + coeff[:, 0]
            assert np.isfinite(values).all()
            return values, sha

        queries = table['queries']
        counts = [q['rows'] for q in queries]
        offsets = np.cumsum([0] + counts[:-1])
        inside, query_sha = scores(table['query_file'], sum(counts), offsets)
        n_out = len(table['outside'])
        assert n_out > 0
        outside, outside_sha = scores(table['outside_file'], 2 * n_out, np.arange(0, 2 * n_out, 2))
        assert receipts[key]['querySha256'] == query_sha
        correct = inside.argmax(axis=1) == np.array([q['label'] for q in queries])
        assert int(correct.sum()) == receipts[key]['formats']['f16']['correct']
        results.append((key, inside.max(axis=1), correct, outside.max(axis=1), outside_sha))
    return index, results


def assess(tables, threshold):
    rows = []
    for name, inside, correct, outside, sha in tables:
        accepted = inside > threshold
        rows.append(dict(table=name, covered=len(inside), coveredAccepted=int(accepted.sum()),
                         acceptedCorrect=int((accepted & correct).sum()), uncovered=len(outside),
                         uncoveredAccepted=int((outside > threshold).sum()), outsideSha256=sha))
    totals = {k: sum(row[k] for row in rows) for k in
              ('covered', 'coveredAccepted', 'acceptedCorrect', 'uncovered', 'uncoveredAccepted')}
    return dict(totals=totals, tables=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('fit_dump', 'fit_artifacts', 'eval_dump', 'eval_artifacts', 'out'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    cal, train = score_seed(args.fit_dump, args.fit_artifacts)
    assert cal['seed'] == 1102
    negatives = sorted((float(s) for _, _, _, arr, _ in train for s in arr), reverse=True)
    # At most floor(N * .05) calibration negatives may strictly exceed the cutoff.
    threshold = negatives[math.floor(len(negatives) * 0.05)]
    check, held = score_seed(args.eval_dump, args.eval_artifacts)
    assert check['seed'] == 1103 and check['model'] == cal['model']
    a = assess(train, threshold)
    b = assess(held, threshold)
    assert a['totals']['uncoveredAccepted'] <= math.floor(len(negatives) * 0.05)
    record = dict(scope='Exploratory operating point on archived development tables. Separate from the MiniCPM lock.',
                  model=cal['model'], calibrationSeed=cal['seed'], evaluationSeed=check['seed'],
                  criterion='Accept only when maximum F16 readout score exceeds cutoff. Empirical calibration false acceptance target is 5%.',
                  threshold=threshold, calibration=a, evaluation=b)
    with args.out.open('x') as out:
        json.dump(record, out, indent=2)
        out.write('\n')
    print(json.dumps(dict(threshold=threshold,calibration=a['totals'],evaluation=b['totals'])))


if __name__ == '__main__':
    main()
