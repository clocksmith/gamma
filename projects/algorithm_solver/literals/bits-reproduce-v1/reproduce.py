#!/usr/bin/env python3
"""One command that re-checks the BITS capacity results without a solver. Python 3.10+ and Git.

    python3 -B reproduce.py            checksums, then every quick checker (a few minutes)
    python3 -B reproduce.py --full     also the slow ones: the exhaustive audit, the three-arm replay, verify_bits

Every checker recomputes its answers from frozen inputs: ranks, exhaustive minimums on small corpora,
certificates in exact fractions, and dictionaries replayed against the stored bytes. Nothing here calls a
linear-programming or integer-programming solver. Times and solver-found objects are not reproduced; see
MANIFEST.md for what each step covers and what it does not.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LITERALS = os.path.join(HERE, '..')
REPO = os.path.abspath(os.path.join(LITERALS, '..', '..', '..'))
PY = [sys.executable, '-B']

CHECKSUMS = [
    ('witness-coverage-v1', 'SHA256SUMS'), ('capacity-theorems-v1', 'SHA256SUMS'), ('capacity-complexity-v1', 'SHA256SUMS'),
    ('capacity-boundary-v1', 'SHA256SUMS'), ('capacity-kernel-audit-v1', 'SHA256SUMS'),
    ('capacity-lagrangian-race-v1', 'SHA256SUMS-PUBLIC'), ('capacity-lagrangian-race-v1', 'SHA256SUMS-THREE-ARM'),
]
# (what it shows, folder, command, slow)
STEPS = [
    ('matched80 needs 92 entries (witness rule) and 79 (unrestricted)', 'witness-coverage-v1', PY + ['check_rank.py', REPO], False),
    ('every plotted coverage point replays', 'witness-coverage-v1', PY + ['check_coverage.py', REPO], False),
    ('the exact unrestricted coverage curve', 'witness-coverage-v1', PY + ['check_unrestricted.py', REPO], True),
    ('hand predictions on the tiny controls', 'capacity-theorems-v1', PY + ['evaluate.py'], False),
    ('counterexamples to both conjectures (round two)', 'capacity-theorems-v1', PY + ['evaluate.py', '--round2'], False),
    ('hardness reductions and 758 certificates', 'capacity-complexity-v1', PY + ['evaluate.py'], False),
    ('two C corpora: minimum 61 and 65', 'capacity-complexity-v1', PY + ['evaluate_real.py'], False),
    ('saturation hardness construction, 20 instances', 'capacity-complexity-v1', PY + ['check_saturation.py'], False),
    ('nine unseen projects, uncapped run', 'capacity-boundary-v1', PY + ['evaluate.py'], False),
    ('nine unseen projects, 160-byte cap', 'capacity-boundary-v1', PY + ['capped.py'], False),
    ('the kernel test alone on 23 corpora', 'capacity-kernel-audit-v1', PY + ['kernel_alone_real.py'], False),
    ('a second implementation agrees on 35 corpora', 'capacity-kernel-audit-v1', PY + ['independent_kernel.py'], False),
    ('the kernel test against exhaustive search, 11,466 checks', 'capacity-kernel-audit-v1', PY + ['audit_kernel.py', '1'], True),
    ('three-arm race on 12 public projects, answers re-derived', 'capacity-lagrangian-race-v1', PY + ['three_arm.py'], True),
    ('matched80 press certificates (verify_bits)', os.path.join('sixbit-v1', 'reproducibility'), PY + ['verify_bits.py', REPO], True),
]


def main():
    full = '--full' in sys.argv
    rows, failed = [], 0
    for folder, name in CHECKSUMS:
        run = subprocess.run(['shasum', '-a', '256', '-c', name], cwd=os.path.join(LITERALS, folder), capture_output=True, text=True)
        ok = run.returncode == 0
        failed += not ok
        rows.append(('checksums ' + folder + '/' + name, 'ok' if ok else 'FAILED', 0.0))
    for what, folder, command, slow in STEPS:
        if slow and not full:
            rows.append((what, 'skipped (use --full)', 0.0))
            continue
        started = time.time()
        run = subprocess.run(command, cwd=os.path.join(LITERALS, folder), capture_output=True, text=True)
        ok = run.returncode == 0
        failed += not ok
        rows.append((what, 'ok' if ok else 'FAILED', time.time() - started))
        if not ok:
            print((run.stdout + run.stderr)[-1500:])
        print(f"{'ok' if ok else 'FAILED':6} {time.time() - started:7.1f} s  {what}", flush=True)
    print()
    for what, status, seconds in rows:
        print(f'{status:22} {what}')
    print(f'\n{sum(1 for r in rows if r[1] == "ok")} passed, {failed} failed, {sum(1 for r in rows if r[1].startswith("skipped"))} skipped')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
