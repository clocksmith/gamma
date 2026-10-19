"""Explicit public output contracts, evaluated only by the host judge.

Modes do not infer problem identity or modify candidate execution. A caller must
declare the rule its examples require; ordinary return comparison is unchanged.
"""
from fractions import Fraction
import math
import re

MODES = frozenset(('return:exact', 'return:numeric_list_tol_1e-5',
                   'return:unordered_distinct_int', 'return:distinct_int_rows',
                   'return:rational_decimal'))


def exact(actual, expected):
    if type(expected) is float:
        return type(actual) in (int, float) and math.isfinite(actual) and math.isfinite(expected) and actual == expected
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(exact(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(exact(actual[k], expected[k]) for k in expected)
    return actual == expected


def decimal(value):
    if type(value) is not str or len(value) > 4096:
        raise ValueError('Expected a bounded decimal string')
    match = re.fullmatch(r'(-?)(0|[1-9][0-9]*)(?:\.([0-9]*)(?:\(([0-9]+)\))?)?', value)
    if not match:
        raise ValueError('Invalid decimal representation')
    sign, whole, tail, cycle = match.groups()
    if tail is not None and not tail and cycle is None:
        raise ValueError('Empty fraction')
    result = Fraction(int(whole))
    if tail:
        result += Fraction(int(tail), 10 ** len(tail))
    if cycle is not None:
        result += Fraction(int(cycle), 10 ** len(tail) * (10 ** len(cycle) - 1))
    if sign:
        result = -result
    if (not result and sign) or (result.denominator == 1 and tail is not None):
        raise ValueError('Noncanonical sign or integer representation')
    denominator = result.denominator
    for factor in (2, 5):
        while denominator % factor == 0:
            denominator //= factor
    if denominator == 1 and cycle is not None:
        raise ValueError('Terminating result encoded as repetition')
    return result


def compare(mode, actual, expected):
    try:
        if mode == 'return:exact':
            return exact(actual, expected)
        if mode == 'return:rational_decimal':
            return decimal(actual) == decimal(expected)
        if not isinstance(actual, list) or not isinstance(expected, list) or len(actual) != len(expected):
            return False
        if mode == 'return:numeric_list_tol_1e-5':
            return all(type(a) in (int, float) and type(b) in (int, float)
                       and math.isfinite(a) and math.isfinite(b)
                       and math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-5)
                       for a, b in zip(actual, expected))
        if mode == 'return:unordered_distinct_int':
            return (all(type(x) is int for x in actual + expected)
                    and len(actual) == len(set(actual)) and len(expected) == len(set(expected))
                    and sorted(actual) == sorted(expected))
        if mode == 'return:distinct_int_rows':
            if not all(isinstance(row, list) and all(type(x) is int for x in row) for row in actual + expected):
                return False
            left, right = [tuple(row) for row in actual], [tuple(row) for row in expected]
            return len(left) == len(set(left)) and len(right) == len(set(right)) and sorted(left) == sorted(right)
        return False
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        return False
