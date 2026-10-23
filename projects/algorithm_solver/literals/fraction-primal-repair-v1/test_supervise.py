"""A sleeping synthetic worker proves the parent enforces the cohort cap."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import supervise


class GuardTests(unittest.TestCase):
    def test_parent_kills_workers_at_cohort_cap_before_outer_cap(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); output = root / 'out'
            (root / 'run.py').write_text('import time\ntime.sleep(20)\n')
            c = {'limits': {'overall_seconds': 3, 'cohort_seconds': .15,
                            'arm_cores': {'R': [0], 'naming': [1]}}}
            (root / 'contract.json').write_text(json.dumps(c))
            started = time.monotonic()
            with patch.object(supervise, 'HERE', root), patch.object(supervise, 'check_contract'), patch.object(supervise.os, 'sched_setaffinity'):
                with self.assertRaisesRegex(TimeoutError, 'cohort hard deadline'):
                    supervise.main(root, output)
            elapsed = time.monotonic() - started
            self.assertLess(elapsed, 3)
            failure = json.loads((output / 'failure.json').read_text())
            self.assertFalse(failure['complete']); self.assertFalse(failure['partial_witnesses_promoted'])
            self.assertFalse(failure['validation_loaded']); self.assertEqual(failure['phase'], 'workers')
            self.assertFalse((output / 'results.json').exists())


if __name__ == '__main__':
    unittest.main()
