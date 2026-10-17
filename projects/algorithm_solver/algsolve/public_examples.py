"""Recover explicit statement examples through the restricted data parser only."""
from dataclasses import replace

from . import importers, values


def recover(problem):
    if problem.public_tests or problem.io_mode != 'functional':
        return problem
    method = problem.entry.get('method')
    if not method or not problem.starter_code:
        return problem
    try:
        params = values.signature(problem.starter_code, method)
        if problem.params and [list(p) for p in params] != problem.params:
            return problem
        tests, dropped = importers.statement_examples(
            problem.statement, params, values.return_annotation(problem.starter_code, method))
    except values.Unsupported:
        return problem
    # Do not approve a subset when another explicit example failed to parse.
    if not tests or dropped:
        return problem
    return replace(problem, public_tests=tests)
