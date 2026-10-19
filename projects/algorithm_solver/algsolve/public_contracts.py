"""Narrow opt-in binding of explicit public output-order declarations.

This reads query requirements only. It does not infer identity or rewrite data,
expected results, stored code, inner order, multiplicity or explicit comparisons.
"""
from dataclasses import replace
import re

_DECLARATION = re.compile(r'(?:You (?:may|can) return|Return) (?:the )?(?:answer|result|output|solution) in any order', re.I)
_CONFLICT = re.compile(r'(?:the )?(?:answer|result|output|solution) (?:must|should|has to|needs to) .*(?:sorted|ascending|descending|order)', re.I)

_DIRECT_ORDER = re.compile(
    r'(?:Return|You (?:must|should|need to|have to) return) (?:the )?'
    r'(?:answer|result|output|solution)\b.*\b'
    r'(?:sorted|ascending|descending|lexicographic|lexicographical|original order|same order)\b.*', re.I)


def unordered_outer_declared(statement):
    """Accept only a complete declarative requirement before worked examples."""
    requirements = re.split(r'\bExample\s*\d*\s*:', statement, maxsplit=1, flags=re.I)[0]
    sentences = [' '.join(s.split()) for s in re.split(r'[.!?\n]', requirements) if s.strip()]
    if any(_CONFLICT.fullmatch(s) or _DIRECT_ORDER.fullmatch(s) for s in sentences):
        return False
    return any(_DECLARATION.fullmatch(s) for s in sentences)


def bind(problem):
    if problem.io_mode != 'functional' or not unordered_outer_declared(problem.statement):
        return problem
    tests = []
    for test in problem.public_tests:
        # An explicitly strict or property-based caller contract takes priority.
        # Non-list and in-place results cannot use an outer-list comparison.
        if test.get('compare', 'return') == 'return' and type(test.get('expected')) is list:
            test = dict(test, compare='return:unordered_outer')
        tests.append(test)
    return replace(problem, public_tests=tests) if tests != problem.public_tests else problem
