"""Repeatable negative test for the escape-arm slot check (#201).

Swap two entries of the frozen c-w-compact manifest vocabulary while keeping the packaged
dictionary.ltd and every encoded program fixed. The vocabulary is still the same eligible
set, every packet still decodes to its source and the press count is unchanged, so the
checker frozen at the source pin accepts the fixture. The current amended checker compares
the packaged dictionary slot by slot with the vocabulary checked for eligibility and must
reject it. An unmodified copy is accepted by both.

Run from a Gamma checkout that contains the source pin:

    python3 -B -m unittest discover -s projects/algorithm_solver/literals/sixbit-v1/reproducibility -v

Pass another checkout with GAMMA_CHECKOUT=/path/to/gamma. Nothing in the checkout is
written; fixtures live in a temporary directory.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PIN = '59ff04415ff2afd04ff2ed451340f4f02852bf18'
BASE = 'projects/algorithm_solver/literals/'
SIX = BASE + 'sixbit-v1/'
HERE = Path(__file__).resolve().parent
CURRENT_CHECKER = HERE.parent / 'verify_amended.py'
GAMMA = Path(os.environ.get('GAMMA_CHECKOUT') or HERE.parents[4]).resolve()
FROZEN_PRESSES = 75925


def git(*args):
    return subprocess.check_output(['git', '-C', str(GAMMA), *args])


class EscapeSlotSwap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        git('rev-parse', PIN + '^{commit}')
        cls.tmp = tempfile.TemporaryDirectory(prefix='bits-slot-swap-')
        root = cls.root = Path(cls.tmp.name)

        def extract(path):
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git('show', PIN + ':' + path))

        for path in (
            *(SIX + x for x in ('verify.py', 'verify_amended.py', 'escape6_decoder.py')),
            *(BASE + x for x in (
                'literals.py', 'pass2/working/bitpack.py', 'readable-v1/literal_codec.py',
                'scale-v2/qualification/report.json', 'scale-v2/qualification-rerun-v1/report.json',
                'scale-v2/generated/manifest.json', 'matched80-v1/labels/ids.json',
            )),
        ):
            extract(path)
        manifest = json.loads((root / BASE / 'scale-v2/generated/manifest.json').read_text())
        for row in manifest['rows']:
            if row['variant'] == 'compact':
                extract(BASE + 'scale-v2/generated/' + row['file'])
        for path in git('ls-tree', '-r', '--name-only', '--full-tree', PIN, '--', SIX + 'run-v1/c-w-compact').decode().split():
            extract(path)
        # The current checker sits beside the frozen verify.py it wraps; verify.py is unchanged since the pin.
        shutil.copyfile(CURRENT_CHECKER, root / SIX / 'verify_amended_current.py')

        job = root / SIX / 'run-v1/c-w-compact'
        for name, swap in (('control', False), ('swapped', True)):
            folder = root / SIX / name / 'c-w-compact'
            shutil.copytree(job, folder)
            if swap:
                m = json.loads((folder / 'manifest.json').read_text())
                vocabulary = m['vocabulary']
                i, j = 0, next(k for k in range(1, len(vocabulary)) if vocabulary[k] != vocabulary[0])
                vocabulary[i], vocabulary[j] = vocabulary[j], vocabulary[i]
                (folder / 'manifest.json').write_text(json.dumps(m))
                cls.swapped_slots = (i, j)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_checker(self, checker, run):
        return subprocess.run([sys.executable, '-B', str(self.root / SIX / checker), str(self.root / SIX / run)],
                              capture_output=True, text=True)

    def report(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_frozen_checker_accepts_both_fixtures_with_identical_counts(self):
        control = self.report(self.run_checker('verify_amended.py', 'control'))
        swapped = self.report(self.run_checker('verify_amended.py', 'swapped'))
        self.assertEqual(control['presses'], FROZEN_PRESSES)
        self.assertEqual(swapped, control)

    def test_current_checker_accepts_control(self):
        control = self.report(self.run_checker('verify_amended_current.py', 'control'))
        self.assertEqual(control['presses'], FROZEN_PRESSES)

    def test_current_checker_rejects_swapped_slots(self):
        result = self.run_checker('verify_amended_current.py', 'swapped')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('dictionary.ltd differs from eligibility-checked vocabulary', result.stderr)


if __name__ == '__main__':
    unittest.main()
