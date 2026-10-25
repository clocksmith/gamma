import importlib.util
from pathlib import Path
import sys
import unittest

spec = importlib.util.spec_from_file_location('six_role_cost_compare', Path(__file__).with_name('compare.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class Controls(unittest.TestCase):
    def test_capture_is_target_local_only(self):
        def other():
            secret_other = 7
            return secret_other
        def target():
            intended = other() + 1
            return intended
        state = c.capture_return(target)
        self.assertEqual(state['intended'], 8)
        self.assertNotIn('secret_other', state)
        self.assertIsNone(sys.getprofile())

    def test_exception_restores_profiler(self):
        def fail():
            raise ValueError('synthetic')
        with self.assertRaises(ValueError):
            c.capture_return(fail)
        self.assertIsNone(sys.getprofile())

    def test_existing_profiler_is_not_replaced(self):
        def existing(frame, event, arg):
            return None
        sys.setprofile(existing)
        try:
            with self.assertRaises(RuntimeError):
                c.capture_return(lambda: None)
            self.assertIs(sys.getprofile(), existing)
        finally:
            sys.setprofile(None)

    def test_minimum_actions_then_absolute_characters(self):
        groups = {'p': ['old', 'new', 'more']}
        rows = {'old': dict(selections=3, characters=2), 'new': dict(selections=3, characters=1),
                'more': dict(selections=4, characters=0)}
        self.assertEqual(c.choose(groups, rows, {'p': 'old'}), {'p': 'new'})

    def test_reference_wins_exact_tie_and_unreachable_is_not_coverage(self):
        rows = {'a': dict(selections=2, characters=1), 'b': dict(selections=2, characters=1), 'x': None}
        self.assertEqual(c.choose({'p': ['a', 'b', 'x']}, rows, {'p': 'b'}), {'p': 'b'})
        with self.assertRaises(ValueError):
            c.choose({'p': ['x']}, rows, {'p': 'x'})

    def test_complete_source_and_body_cannot_be_a_literal(self):
        source = 'function solve(a){return a+1;}'
        for literal in (source, 'return a+1;'):
            with self.assertRaises(ValueError):
                c.whole_source_exclusion(source, [literal])
        c.whole_source_exclusion(source, ['function solve(', 'return ', 'a', '+', '1', ';'])


if __name__ == '__main__':
    unittest.main()
