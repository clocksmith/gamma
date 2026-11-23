#!/usr/bin/env python3
"""Decodes every separate-dictionary split reported in summary.json.

    verify_sharing.py <private folder> <run folder> [workers]
"""
import json
import multiprocessing
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify as V

FILES = {}
RUN = None


def decode(row):
    total = 0
    used, stored = 0, 0
    for language, key, arm in (('python', 'python_entries', 'python_arm'), ('javascript', 'javascript_entries', 'javascript_arm')):
        entries = V.read_chain(RUN / 'chains' / f"{language}-L{row['L']}-{row[arm]}.txt")[0][:row[key]]
        root = {}
        for item in entries:
            V.insert(root, item[4])
        spelled, tokens = V.score(FILES[language], root)
        if spelled != 400:
            raise SystemExit('a separate dictionary did not spell its language')
        total += tokens
        used += len(entries)
        stored += entries[-1][1]
    if total != row['separate'] or used > row['K']:
        raise SystemExit('a split differs from its decode')
    if row['B'] is not None and stored + 4 > row['B']:
        raise SystemExit('a split is over its byte budget')
    return row['shared'] < total


def main():
    global RUN
    private, RUN = Path(sys.argv[1]), Path(sys.argv[2])
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    FILES.update(V.load_corpus(private, Path(V.__file__).resolve().parent / 'manifest.json'))
    summary = json.loads((RUN / 'out' / 'summary.json').read_text())
    rows = [r for r in summary['sharing'] if r['separate'] is not None and r['shared'] is not None]
    with multiprocessing.get_context('fork').Pool(workers) as pool:
        wins = pool.map(decode, rows, chunksize=4)
    report = {'schema': 'gamma.fixed-source-sharing-check.v1', 'splits_decoded': len(rows), 'shared_wins': sum(wins)}
    (RUN / 'out' / 'sharing-check.json').write_text(json.dumps(report) + '\n')
    print(report)


if __name__ == '__main__':
    main()
