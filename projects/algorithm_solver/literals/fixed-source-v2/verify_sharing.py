#!/usr/bin/env python3
"""Decodes every separate-dictionary split reported in summary.json, under its policy.

    verify_sharing.py <v1 private folder> <run folder> [workers]
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
    total = used = stored = 0
    for language, key, arm in (('python', 'python_entries', 'python_arm'), ('javascript', 'javascript_entries', 'javascript_arm')):
        path = RUN / 'chains' / row['policy'] / f"{language}-L{row['L']}-{row[arm]}.txt"
        receipt, chain, _, _, _ = V.read_chain(path)
        if receipt['policy'] != row['policy'] or receipt['pool'] != language:
            raise SystemExit('a split used a chain with the wrong binding')
        entries = chain[:row[key]]
        V.check_framing(entries)
        V.check_entries(entries, FILES[language], row['L'], row['policy'], True)
        root = {}
        for item in entries:
            V.insert(root, item[4])
        spelled, tokens, _, _ = V.score(FILES[language], root)
        if spelled != 400:
            raise SystemExit('a separate dictionary did not spell its language')
        total += tokens
        used += len(entries)
        stored += entries[-1][1]
    if total != row['separate'] or used > row['K']:
        raise SystemExit('a split differs from its decode')
    if row['B'] is not None and stored + 4 > row['B']:
        raise SystemExit('a split is over its byte budget')
    return row['policy'], row['shared'] < total


def main():
    global RUN
    private, RUN = Path(sys.argv[1]), Path(sys.argv[2])
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    FILES.update(V.load_corpus(private))
    summary = json.loads((RUN / 'out' / 'summary.json').read_text())
    rows = [r for r in summary['sharing'] if r['separate'] is not None and r['shared'] is not None]
    with multiprocessing.get_context('fork').Pool(workers) as pool:
        results = pool.map(decode, rows, chunksize=4)
    report = {'schema': 'gamma.fixed-source-sharing-check.v2', 'splits_decoded': len(rows), 'by_policy': {}}
    for policy in sorted({r[0] for r in results}):
        wins = [won for name, won in results if name == policy]
        report['by_policy'][policy] = {'splits': len(wins), 'shared_wins': sum(wins)}
    (RUN / 'out' / 'sharing-check.json').write_text(json.dumps(report) + '\n')
    print(report)


if __name__ == '__main__':
    main()
