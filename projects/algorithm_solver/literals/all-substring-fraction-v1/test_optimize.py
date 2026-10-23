"""Synthetic optimizer and process-deadline checks; no corpus access."""
import subprocess
import sys
import time
import unittest
import implicit
import optimize
import supervise


class OptimizeTests(unittest.TestCase):
    def test_bounded_ascent_retains_exact_bound_and_feasible_upper(self):
        texts = {'a': 'ababababac', 'b': 'babababcab', 'c': 'cabacacaba'}
        index = implicit.Index(texts, set(texts.values()))
        rows = []
        cfg = {'iterations': 35, 'seconds': 5, 'denominator': 1000,
               'halve_after': 5, 'primal_every': 3}
        info, q, seed, best, generated = optimize.optimize(index, ['a', 'b', 'c', 'z'], 4, cfg, rows.append)
        self.assertEqual(seed, ['a', 'b', 'c'])
        self.assertEqual(info['best_objective'], optimize.dual.objective(texts, best))
        self.assertEqual(info['certificate']['numerator'], implicit.verify(index, q, 4, 1000))
        self.assertLessEqual(info['certificate']['integer_lower_bound'], info['best_objective'])
        self.assertLessEqual(info['iterations'], 35)
        self.assertEqual(len(rows), info['iterations'])
        self.assertEqual(info['certificate']['numerator'], max(row['exact_numerator'] for row in rows))
        for vocab in (best, generated):
            if vocab is not None:
                self.assertLessEqual(len(vocab), 4)
                self.assertFalse(set(vocab) & index.banned)

    def test_immediate_exact_convergence_and_no_iteration_failure(self):
        index = implicit.Index({'a': 'aaaa'}, {'aaaa'})
        cfg = {'iterations': 5, 'seconds': 5, 'denominator': 100,
               'halve_after': 2, 'primal_every': 1}
        info, q, seed, best, generated = optimize.optimize(index, ['a', 'aa'], 3, cfg, lambda row: None)
        self.assertEqual(info['certificate']['integer_lower_bound'], -2)
        self.assertEqual(info['best_objective'], -2)
        self.assertEqual(info['stop'], 'exact_primal_optimum_certificate')
        with self.assertRaises(RuntimeError):
            optimize.optimize(index, ['a'], 3, {**cfg, 'iterations': 0}, lambda row: None)

    def test_process_deadline_kills_worker_group(self):
        worker = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(10)'], start_new_session=True)
        try:
            with self.assertRaises(TimeoutError):
                supervise.wait_workers([worker], time.monotonic()+.03)
        finally:
            supervise.stop_workers([worker])
        self.assertEqual(worker.returncode, -9)

    def test_worker_failure_rejects_whole_job(self):
        worker = subprocess.Popen([sys.executable, '-c', 'raise SystemExit(7)'], start_new_session=True)
        try:
            with self.assertRaises(RuntimeError):
                supervise.wait_workers([worker], time.monotonic()+2)
        finally:
            supervise.stop_workers([worker])
        self.assertEqual(worker.returncode, 7)


if __name__ == '__main__':
    unittest.main()
