#!/usr/bin/env python3
"""The v3 engine must rebuild v2's deterministic chains entry for entry.

    check_regression.py <v2 chains> <v3 run chains> <output json>
"""
import json
import sys
from pathlib import Path

ARMS = ('greedy-entry', 'greedy-byte', 'freq-occ', 'freq-doc')


def lines(path):
    return [line for line in Path(path).read_text().splitlines() if line[0] == 'E']


def main():
    old, new, output = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    compared, differ, missing = 0, [], []
    for policy in ('s1-whole', 's2-nowhole'):
        for corpus in ('both', 'python', 'javascript'):
            for limit in (8, 16, 32, 64):
                for arm in ARMS:
                    name = f'{policy}/{corpus}-L{limit}-{arm}.txt'
                    if not (old / name).exists() or not (new / name).exists():
                        missing.append(name)
                        continue
                    compared += 1
                    if lines(old / name) != lines(new / name):
                        differ.append(name)
    report = {'schema': 'gamma.fixed-source-regression.v3', 'chains_compared': compared, 'identical': compared - len(differ),
              'different': differ, 'missing': missing}
    output.write_text(json.dumps(report, indent=1) + '\n')
    print({k: (v if not isinstance(v, list) else len(v)) for k, v in report.items()})
    if differ or missing:
        raise SystemExit('v3 did not rebuild the v2 chains')


if __name__ == '__main__':
    main()
