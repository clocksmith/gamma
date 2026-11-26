#!/usr/bin/env python3
"""An interrupted or time-limited engine run must never be taken for a finished chain.

    python3 test_chain_guard.py        # a few seconds; needs a C compiler

Builds the engine in a temporary directory, runs it on eight training files, and then breaks the
result the ways a real run breaks: cut short, time-limited, hung.
"""
import json
import stat
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_replication as R  # noqa: E402


def expect_error(kind, fn, label, failed):
    try:
        fn()
    except kind as exc:
        return str(exc)
    failed.append(f'no {kind.__name__} when {label}')
    return ''


def main():
    failed = []
    files = sorted((HERE / 'corpus' / 'primary' / 'python').glob('*.py'))[:8]
    with tempfile.TemporaryDirectory(prefix='chain-guard-') as td:
        td = Path(td)
        engine, sha = R.compile_engine(td)
        lists = td / 'lists'
        lists.mkdir()
        (lists / 'tiny.txt').write_text('\n'.join(map(str, files)) + '\n')
        (lists / 'tiny.groups').write_text(' '.join(map(str, range(len(files)))) + '\n')
        receipt = f'manifest=test split=test pool=tiny cuts=none impl={sha} run=chain-guard-test'
        job = (engine, 'test', 's1-whole', 'bpe', 16, 'tiny', lists, td / 'chains', receipt)
        chain = td / 'chains' / 'test' / 's1-whole' / 'tiny-L16-bpe.txt'

        path, seconds = R.run_single_engine_job(job)
        good = chain.read_bytes()
        if not (Path(path) == chain and R.chain_complete(chain) and seconds > 0):
            failed.append('a normal run did not leave a finished chain')
        _, entries, _ = R.read_chain(chain)
        if len(entries) < 100:
            failed.append(f'a normal run returned only {len(entries)} entries')

        def rebuilt():  # the end line carries run time and memory, so compare what the chain says, not its bytes
            return R.chain_complete(chain) and R.read_chain(chain)[1] == entries
        if R.run_single_engine_job(job)[1] != 0.0:
            failed.append('a finished chain was not reused')

        # 1. Killed mid-write: the file exists, is not empty, and has no end line.
        chain.write_bytes(good[: len(good) // 2])
        if R.chain_complete(chain):
            failed.append('a chain cut in half counts as finished')
        expect_error(ValueError, lambda: R.read_chain(chain), 'reading a chain cut in half', failed)
        if R.run_single_engine_job(job)[1] == 0.0 or not rebuilt():
            failed.append('a chain cut in half was reused instead of rebuilt')

        # 2. Cut just before the end line.
        chain.write_bytes(good[: good.rstrip(b'\n').rfind(b'\n') + 1])
        if R.chain_complete(chain):
            failed.append('a chain without its end line counts as finished')

        # 3. The engine ran into its time limit: it exits 0 and writes stopped=1.
        chain.unlink()
        limit = R.LIMIT_SECONDS
        R.LIMIT_SECONDS = 0
        message = expect_error(RuntimeError, lambda: R.run_single_engine_job(job), 'the engine stops at its time limit', failed)
        R.LIMIT_SECONDS = limit
        if 'stopped=1' not in message or chain.exists():
            failed.append('a time-limited run was moved into place as a chain')
        chain.write_bytes(good.replace(b' stopped=0 ', b' stopped=1 '))
        if R.chain_complete(chain):
            failed.append('a chain marked stopped=1 counts as finished')

        # 4. The engine never returns (a full pair table): the driver must kill it and say so.
        chain.unlink()
        hung = td / 'hung-engine'
        hung.write_text('#!/bin/sh\nsleep 60\n')
        hung.chmod(hung.stat().st_mode | stat.S_IXUSR)
        bound = R.ENGINE_TIMEOUT_SECONDS
        R.ENGINE_TIMEOUT_SECONDS = 1
        message = expect_error(RuntimeError, lambda: R.run_single_engine_job((hung,) + job[1:]), 'the engine hangs', failed)
        R.ENGINE_TIMEOUT_SECONDS = bound
        if 'did not return' not in message or chain.exists() or list(chain.parent.glob('*.partial')):
            failed.append('a hung engine left something behind or was not reported')

        # 5. A finished chain left by another engine build is not this run's chain.
        R.run_single_engine_job(job)
        own = chain.read_bytes()
        chain.write_bytes(own.replace(f'impl={sha}'.encode(), b'impl=' + b'0' * 64, 1))
        if R.run_single_engine_job(job)[1] == 0.0 or f'impl={sha}' not in chain.read_text().splitlines()[0]:
            failed.append('a finished chain from another engine build was reused')

        # 6. Scoring refuses a grid with a missing chain instead of comparing fewer arms.
        manifest = json.loads((HERE / 'manifest.json').read_text())
        message = expect_error(SystemExit, lambda: R.analyze_split('primary', (16,), manifest, td / 'chains'), 'chains are missing', failed)
        if 'missing or unfinished' not in message:
            failed.append('scoring did not name the missing chains')
    if failed:
        print('\n'.join('FAILED: ' + f for f in failed))
        return 1
    print('finished chain reused; cut, unterminated, time-limited and hung runs are refused or rebuilt; a chain from another engine build is rebuilt; scoring refuses missing chains')
    return 0


if __name__ == '__main__':
    sys.exit(main())
