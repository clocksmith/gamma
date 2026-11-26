#!/usr/bin/env python3
"""Fail-closed reproduction of the BITS results. Supersedes bits-reproduce-v1, which stays frozen.

    python3 -B reproduce.py            quick checks; exits 2 (INCOMPLETE) because some claims are not verified
    python3 -B reproduce.py --full     every check; exits 0 only if every claimed result was verified

Changes from v1 (whose step list is read from its frozen file after its checksums pass):

- Fail closed. v1 printed "passed" after quick mode, although quick mode only compares the hash of the 4,141-node
  PY-3 tree and skips the slow checks. Here a skipped check is NOT VERIFIED, the hash-only tree is NOT VERIFIED,
  and any NOT VERIFIED row makes the exit code 2. Only a run in which every row is ok exits 0.
- --full now covers every number the paper states: it adds the 33rd exact coverage point (76 slots,
  check_addendum.py --deep) and seed 2 of the ladder audit, which v1 left to separate commands.
- Byte accounting: bits-envelope-v1 measures payload, framing, dictionary, index and decoder bytes of the four
  frozen matched80 packages from the files, requires 0 B drift from their package_bytes, refuses to call them
  random-access totals (no index is stored), and its tests reject an uncounted index and a slot swap.
- The solver-free matched80 checker (sixbit-v1/independent-verifier/check.py) and the 06562147d slot-swap test
  are run. Neither imports model.py; nothing here does.

A missing script is FAILED, never skipped. Times and solver-found objects are not reproduced (see
../bits-reproduce-v1/MANIFEST.md).
"""
import hashlib
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LITERALS = os.path.normpath(os.path.join(HERE, '..'))
REPO = os.path.normpath(os.path.join(LITERALS, '..', '..', '..'))
PY = [sys.executable, '-B']
V1 = os.path.join(LITERALS, 'bits-reproduce-v1')
V1_REPRODUCE_SHA256 = 'd4289bd371e9e3e6895809a6c0d0cbd7498263d19ea9a05a68b8ecbf821967f7'
UNITTEST = PY + ['-m', 'unittest', 'discover', '-s', '.']
NEW_FOLDERS = ['bits-reproduce-v1', 'bits-reproduce-v2', 'bits-envelope-v1', 'witness-newline-sensitivity-v1']

# (what it shows, folder, command, slow), added to v1's list.
ADDED = [
    ('byte envelope: four frozen matched80 packages reconcile with 0 B drift, none is a random-access total',
     'bits-envelope-v1', PY + ['envelope.py', REPO], False),
    ('byte envelope: uncounted index, 1 B drift, unlisted file and slot swaps are rejected; a second accountant agrees',
     'bits-envelope-v1', UNITTEST, False),
    ('matched80 compact jobs, solver-free and zero-import (independent-verifier/check.py)',
     os.path.join('sixbit-v1', 'independent-verifier'), PY + ['check.py', REPO], False),
    ('matched80 rank with and without trailing newlines: compact 79 -> 78, canonical 79 -> 79',
     'witness-newline-sensitivity-v1', PY + ['check_stripped_rank.py', REPO], False),
    ('escape-arm slot swap rejected (06562147d)',
     os.path.join('sixbit-v1', 'reproducibility'), UNITTEST, True),
    ('coverage addendum --deep: the 33rd exact budget, 76 slots (82,160 subset ranks, numpy)',
     'witness-coverage-addendum-v1', PY + ['check_addendum.py', REPO, '--deep'], True),
    ('ladder against exhaustive search, seed 2 (numpy)',
     'capacity-ladder-v1', PY + ['audit_ladder.py', '2', '3'], True),
]
# Claims that a passing quick step does not verify.
QUICK_GAPS = [
    'PY-3: the 4,141-node defect tree (quick mode compares its SHA-256 only and scores PY-3 at its rank)',
]


def v1_lists():
    path = os.path.join(V1, 'reproduce.py')
    source = open(path, 'rb').read()
    if hashlib.sha256(source).hexdigest() != V1_REPRODUCE_SHA256:
        raise SystemExit('FAILED: bits-reproduce-v1/reproduce.py is not the frozen file')
    scope = {'__name__': 'bits_reproduce_v1', '__file__': path}
    exec(compile(source, path, 'exec'), scope)  # defines CHECKSUMS and STEPS; main() is not called
    return scope['CHECKSUMS'] + [(f, 'SHA256SUMS') for f in NEW_FOLDERS], scope['STEPS']


def run(command, folder):
    cwd = os.path.join(LITERALS, folder)
    script = next((part for part in command[2:] if part.endswith('.py')), None)
    if not os.path.isdir(cwd) or (script and not os.path.isfile(os.path.join(cwd, script))):
        return False, f'missing: {folder}/{script or ""}'
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return result.returncode == 0, (result.stdout + result.stderr)[-1500:]


def main():
    full = '--full' in sys.argv
    checksums, steps = v1_lists()
    rows = []
    for folder, name in checksums:
        ok, _ = run(['shasum', '-a', '256', '-c', name], folder) if os.path.isfile(
            os.path.join(LITERALS, folder, name)) else (False, 'missing')
        rows.append(('checksums ' + folder + '/' + name, 'ok' if ok else 'FAILED', 0.0))
    for what, folder, command, slow in steps + ADDED:
        if slow and not full:
            rows.append((what, 'NOT VERIFIED (--full)', 0.0))
            continue
        started = time.time()
        ok, tail = run(command, folder)
        seconds = time.time() - started
        rows.append((what, 'ok' if ok else 'FAILED', seconds))
        if not ok:
            print(tail)
        print(f"{'ok' if ok else 'FAILED':6} {seconds:7.1f} s  {what}", flush=True)
    if not full:
        rows += [(gap, 'NOT VERIFIED (--full)', 0.0) for gap in QUICK_GAPS]
    print()
    for what, status, _ in rows:
        print(f'{status:22} {what}')
    failed = sum(r[1] == 'FAILED' for r in rows)
    unverified = sum(r[1].startswith('NOT VERIFIED') for r in rows)
    passed = sum(r[1] == 'ok' for r in rows)
    print(f'\n{passed} ok, {failed} failed, {unverified} not verified')
    if failed:
        print('FAILED')
        sys.exit(1)
    if unverified:
        print('INCOMPLETE: not every claimed result was verified; run with --full')
        sys.exit(2)
    print('VERIFIED: every claimed result was checked')
    sys.exit(0)


if __name__ == '__main__':
    main()
