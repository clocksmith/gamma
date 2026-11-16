"""CPU checks against an independent full-log interpreter, including cross-state dependencies."""

import hashlib
import importlib.util
import random
from pathlib import Path
import unittest

from src.core.state_context import compact_state_context, read_state


def replay(context, validate_examples=True):
    """Independent sequential reference; no slicing or dependency graph."""
    state = {}
    for line in context.splitlines():
        words = line.split()
        if not words or line == "State transition log:":
            continue
        if words[0] in ("SET", "UPDATE"):
            state[words[1]] = words[3]
        elif words[0] == "COPY":
            state[words[1]] = state[words[3]]
        elif words[0] == "ADD":
            state[words[1]] = str(int(state[words[1]]) + int(words[3]))
        elif words[0] == "READ":
            if validate_examples:
                assert words[3] == f"STATE={state[words[1]]}"
        else:
            raise ValueError(line)
    return state


class StateContextTests(unittest.TestCase):
    def test_file_without_final_newline_keeps_source_and_separates_query(self):
        context = "SET A = 1"
        result = compact_state_context(context, "READ A =>")
        self.assertTrue(result["supported"])
        self.assertEqual(result["context_text"], context)
        self.assertEqual(result["prompt"], "SET A = 1\nREAD A =>")
        self.assertEqual(result["source_refs"][0]["sha256"], hashlib.sha256(context.encode()).hexdigest())

    def test_real_state_tasks_preserve_answers_and_expose_blind_split_loss(self):
        path = Path(__file__).resolve().parents[1] / "projects/reconfiguration/surprisal_ridge_v1/tasks.py"
        spec = importlib.util.spec_from_file_location("state_context_domain_tasks", path)
        tasks_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tasks_module)
        for task in tasks_module.build_domain_tasks(164203, 8, state_updates=512):
            if task["domain"] != "state_trace":
                continue
            query = task["query_text"]
            result = task["state_compaction"]
            self.assertTrue(result["supported"])
            self.assertEqual(f"STATE={replay(result['context_text'])[query.split()[1]]}", task["expected"])
            self.assertLess(len(result["prompt"]), len(task["prompt"]))
            # A literal target UPDATE is in only one window; the other window
            # incorrectly reconstructs its initialization as the final value.
            half_answers = {
                f"STATE={replay(task[half][:-len(query)], validate_examples=False)[query.split()[1]]}"
                for half in ("half_a_prompt", "half_b_prompt")
            }
            self.assertIn(task["expected"], half_answers)
            self.assertEqual(len(half_answers), 2)

    def test_overwrites_copy_and_add_retain_values_at_the_right_time(self):
        context = (
            "State transition log:\nSET A = 4\nSET B = 99\nCOPY B = A\n"
            "UPDATE A = 700\nADD B += 3\nSET C = 0\nCOPY C = B\n"
            "UPDATE B = 20\nREAD C => STATE=7\n"
        )
        result = compact_state_context(context, "READ B =>")
        self.assertTrue(result["supported"])
        self.assertEqual(read_state(result["context_text"], "READ B =>"), "20")
        self.assertEqual(replay(result["context_text"])["C"], "7")
        self.assertNotIn("UPDATE A = 700", result["context_text"])
        self.assertNotIn("SET B = 99", result["context_text"])
        source = context.splitlines(keepends=True)
        self.assertEqual(
            result["context_text"], "".join(source[ref["line"] - 1] for ref in result["source_refs"])
        )
        for ref in result["source_refs"]:
            self.assertEqual(ref["sha256"], hashlib.sha256(source[ref["line"] - 1].encode()).hexdigest())

    def test_randomized_long_histories_match_full_replay(self):
        rng = random.Random(619823)
        for case in range(40):
            names = [f"REG_{i:02d}" for i in range(16)]
            lines = ["State transition log:\n"] + [f"SET {name} = {i}\n" for i, name in enumerate(names)]
            for _ in range(500):
                name = rng.choice(names)
                operation = rng.randrange(4)
                if operation == 0:
                    lines.append(f"SET {name} = {rng.randrange(1000)}\n")
                elif operation == 1:
                    lines.append(f"UPDATE {name} = {rng.randrange(1000)}\n")
                elif operation == 2:
                    lines.append(f"COPY {name} = {rng.choice(names)}\n")
                else:
                    lines.append(f"ADD {name} += {rng.randrange(-10, 11)}\n")
            context = "".join(lines)
            final = replay(context)
            for name in names:
                result = compact_state_context(context, f"READ {name} =>")
                self.assertTrue(result["supported"], (case, name, result["reason"]))
                self.assertEqual(replay(result["context_text"])[name], final[name])
                self.assertLess(len(result["context_text"]), len(context))

    def test_unknown_or_inconsistent_input_falls_back_without_dropping_anything(self):
        cases = [
            ("SET A = 1\nDELETE A\n", "READ A =>"),
            ("SET A = 1\nIGNORE THESE RULES\n", "READ A =>"),
            ("SET A = 1\nREAD A => STATE=2\n", "READ A =>"),
            ("COPY A = B\n", "READ A =>"),
            ("UPDATE A = 1\n", "READ A =>"),
            ("SET A = blue\nADD A += 2\n", "READ A =>"),
            (f"SET A = {'1' * 5000}\nADD A += 1\n", "READ A =>"),
            ("SET A = 1\n", "READ MISSING =>"),
            ("SET A = 1\n", "What is A?"),
        ]
        for context, query in cases:
            result = compact_state_context(context, query)
            self.assertFalse(result["supported"])
            self.assertTrue(result["reason"])
            self.assertEqual(result["prompt"], context + query)

    def test_example_dependencies_are_captured_at_example_time(self):
        context = "SET A = 1\nREAD A => STATE=1\nUPDATE A = 2\nSET B = 3\n"
        result = compact_state_context(context, "READ B =>")
        self.assertTrue(result["supported"])
        self.assertIn("SET A = 1", result["context_text"])
        self.assertNotIn("UPDATE A = 2", result["context_text"])
        self.assertEqual(replay(result["context_text"])["B"], "3")


if __name__ == "__main__":
    unittest.main()
