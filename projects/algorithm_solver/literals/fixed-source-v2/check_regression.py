#!/usr/bin/env python3
"""The historical control must rebuild v1's chains entry for entry.

BPE is excluded: v1 counted a merge's files on its token stream, while v2 applies
the policy to the merged string itself, as FREEZE.md states.

    check_regression.py <v1 chains> <v2 run chains> <output json>
"""
import json
import sys
from pathlib import Path

ARMS = ('greedy-entry', 'greedy-byte', 'freq-occ', 'freq-doc', 'cover-mixed', 'cover-nosingle')


def lines(path):
    return [line for line in Path(path).read_text().splitlines() if line[0] in 'ERF']


def main():
    old, new, output = Path(sys.argv[1]), Path(sys.argv[2]) / 's2-nowhole', Path(sys.argv[3])
    compared, differ, missing = 0, [], []
    for corpus in ('python', 'javascript', 'both'):
        for limit in (2, 4, 8, 16, 32, 64):
            for arm in ARMS:
                name = f'{corpus}-L{limit}-{arm}.txt'
                if not (old / name).exists() or not (new / name).exists():
                    missing.append(name)
                    continue
                compared += 1
                if lines(old / name) != lines(new / name):
                    differ.append(name)
    report = {'schema': 'gamma.fixed-source-regression.v2', 'chains_compared': compared,
              'identical': compared - len(differ), 'different': differ, 'missing': missing}
    output.write_text(json.dumps(report, indent=1) + '\n')
    print({key: (value if not isinstance(value, list) else len(value)) for key, value in report.items()})
    if differ or missing:
        raise SystemExit('the historical control did not rebuild v1')


if __name__ == '__main__':
    main()
