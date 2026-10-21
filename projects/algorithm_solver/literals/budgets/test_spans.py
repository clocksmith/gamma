import unittest
from compare import measure, selections
from spans import compact, span_pool
from frontier import package_cost, shrink


class SpanTests(unittest.TestCase):
    def test_pool_retains_shared_spans_but_excludes_whole_programs(self):
        sources = {"a": {"v": "a\nb\nc\nx\n"}, "b": {"v": "a\nb\nc\ny\n"}}
        pool = span_pool(sources)
        self.assertIn("a\nb\nc\n", pool)
        self.assertNotIn(sources["a"]["v"], pool)
        state = measure(pool, sources)
        self.assertEqual(selections(state), 4)

    def test_compaction_never_drops_a_program_or_increases_its_selections(self):
        sources = {"a": {"v": "a\nb\nc\nx\n"}, "b": {"v": "a\nb\nc\ny\n"}}
        pool = span_pool(sources)
        before = measure(pool, sources)
        after, _, _ = compact(pool, sources)
        self.assertEqual(
            {k: len(v["sequence"]) for k, v in before["programs"].items()},
            {k: len(v["sequence"]) for k, v in after["programs"].items()})

    def test_storage_frontier_preserves_full_coverage_and_selection_cap(self):
        sources = {"a": {"v": "a\nb\nc\nx\n"}, "b": {"v": "a\nb\nc\ny\n"}}
        pool = span_pool(sources)
        before = measure(pool, sources)
        after, _, _ = shrink(pool, sources, maximum=6)
        self.assertEqual(set(after["programs"]), set(sources))
        self.assertLessEqual(selections(after), 6)
        self.assertLessEqual(package_cost(after), package_cost(before))


if __name__ == "__main__":
    unittest.main()
