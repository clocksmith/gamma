import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "retrieval_tasks", Path(__file__).with_name("retrieval_tasks.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RetrievalTests(unittest.TestCase):
    def test_oracle_rejects_wrong_partial_and_explanation(self):
        self.assertTrue(module.score_answer("  value_abc\n", "value_abc"))
        for answer in ("abc", "value_def", "The value is value_abc", ""):
            self.assertFalse(module.score_answer(answer, "value_abc"))

    def test_fixture_counts_budgets_and_source(self):
        # Character IDs exercise the budget contract, not model tokenization.
        tasks = module.build_tasks(lambda text: list(text.encode()))
        self.assertEqual(len(tasks), 16)
        self.assertEqual(len({task["expected"] for task in tasks}), 16)
        for task in tasks:
            self.assertLessEqual(len(task["input_ids"]), task["budget"])
            self.assertGreater(len(task["input_ids"]), task["budget"] - 100)
            self.assertEqual(task["prompt"].count(task["expected"]), 1)
            self.assertIn(f"{task['key']} = {task['expected']}", task["prompt"])
            wrong = next(t["expected"] for t in tasks if t["id"] != task["id"])
            self.assertNotIn(wrong, task["prompt"])
            self.assertFalse(module.score_answer(wrong, task["expected"]))


if __name__ == "__main__":
    unittest.main()
