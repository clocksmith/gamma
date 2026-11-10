"""Host-only, independently authored synthetic contracts for direct BITS development.

These are 26 development tasks, not catalogue coverage or protected evaluation.
Training examples are public synthesis constraints. Evaluation inputs are disjoint
from training inputs but are development evidence, not unseen-family evidence.
This module imports no candidate, interpreter, source corpus, or protected data.
Never pass expected outputs (or this module) into candidate execution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
from typing import Callable

SCHEMA = 'algsolve.direct-bits-development-oracles.v1'
SEED = 20261110


@dataclass(frozen=True)
class Domain:
    max_length: int = 32
    min_value: int = -1_000_000
    max_value: int = 1_000_000

    def validate(self, values: list[int]) -> None:
        if (type(values) is not list or len(values) > self.max_length
                or any(type(x) is not int or not self.min_value <= x <= self.max_value
                       for x in values)):
            raise ValueError('Input must be an integer list within the task domain')


@dataclass(frozen=True)
class Case:
    inputs: tuple[list[int]]
    expected: int | list[int]
    split: str
    category: str


@dataclass(frozen=True)
class Task:
    name: str
    description: str
    train_cases: tuple[Case, ...]
    evaluation_cases: tuple[Case, ...]
    domain: Domain
    budget: int = 100_000

    def contract(self) -> dict:
        """Serializable host contract, including every concrete input and answer."""
        return {'schema': SCHEMA, 'evidence_class': 'synthetic-development-only',
                'oracle_source_sha256': oracle_source_sha256(), **asdict(self)}

    def contract_hash(self) -> str:
        return hashlib.sha256(json.dumps(self.contract(), sort_keys=True,
                                        separators=(',', ':')).encode()).hexdigest()


# Specifications are mathematical Python operations, independent of the BITS IR.
# Order-preserving operations retain input order; distinct keeps first occurrences.
_SPECS: tuple[tuple[str, str, Callable], ...] = (
    ('reverse_input', 'Return input values in reverse order, retaining duplicates.', lambda a: list(reversed(a))),
    ('adjacent_differences', 'Return a[i+1] minus a[i] for adjacent positions; length below two returns an empty list.', lambda a: [y-x for x, y in zip(a, a[1:])]),
    ('sum', 'Sum all values; empty input returns 0.', lambda a: sum(a)),
    ('count_positive', 'Count values strictly greater than zero.', lambda a: sum(x > 0 for x in a)),
    ('sum_positive_squares', 'Sum squares of strictly positive values.', lambda a: sum(x*x for x in a if x > 0)),
    ('sum_squares', 'Sum squares of all values.', lambda a: sum(x*x for x in a)),
    ('sum_absolute', 'Sum absolute values.', lambda a: sum(abs(x) for x in a)),
    ('count_nonzero', 'Count values unequal to zero.', lambda a: sum(x != 0 for x in a)),
    ('product', 'Multiply all values; empty input returns 1.', lambda a: math.prod(a)),
    ('sum_negative', 'Sum strictly negative values.', lambda a: sum(x for x in a if x < 0)),
    ('sum_incremented', 'Sum each value plus one; empty input returns 0.', lambda a: sum(x+1 for x in a)),
    ('filter_positive', 'Retain strictly positive values, preserving order and duplicates.', lambda a: [x for x in a if x > 0]),
    ('filter_negative', 'Retain strictly negative values, preserving order and duplicates.', lambda a: [x for x in a if x < 0]),
    ('filter_nonzero', 'Retain nonzero values, preserving order and duplicates.', lambda a: [x for x in a if x != 0]),
    ('map_square', 'Square every value, preserving order.', lambda a: [x*x for x in a]),
    ('map_negate', 'Negate every value, preserving order.', lambda a: [-x for x in a]),
    ('map_absolute', 'Take every absolute value, preserving order.', lambda a: [abs(x) for x in a]),
    ('map_double', 'Multiply every value by two, preserving order.', lambda a: [2*x for x in a]),
    ('map_increment', 'Add one to every value, preserving order.', lambda a: [x+1 for x in a]),
    ('prefix_sum', 'Return inclusive prefix sums; empty input returns an empty list.', lambda a: list(itertools.accumulate(a))),
    ('sort_ascending', 'Sort all values ascending, retaining duplicates.', lambda a: sorted(a)),
    ('sort_descending', 'Sort all values descending, retaining duplicates.', lambda a: sorted(a, reverse=True)),
    ('stable_distinct', 'Retain first occurrence of each value in input order.', lambda a: list(dict.fromkeys(a))),
    ('sorted_distinct', 'Return distinct values in ascending order.', lambda a: sorted(set(a))),
    ('stable_distinct_absolute', 'Take absolute values, then retain first occurrences in transformed order.', lambda a: list(dict.fromkeys(abs(x) for x in a))),
    ('stable_distinct_squares', 'Square values, then retain first occurrences in transformed order.', lambda a: list(dict.fromkeys(x*x for x in a))),
)


def oracle_source_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def domain_for(name: str) -> Domain:
    if name not in {s[0] for s in _SPECS}:
        raise KeyError(name)
    return Domain(16, -8, 8) if name == 'product' else Domain()


def expected(name: str, values: list[int]) -> int | list[int]:
    """Evaluate only on the host, rejecting bools and out-of-contract inputs."""
    domain_for(name).validate(values)
    return next(fn for key, _, fn in _SPECS if key == name)(values)


_TRAIN = ((), (0,), (1,), (-1,), (2,), (-2,), (3, -2, 0, 3, -1),
          (-3, 2, -3, 0, 2, 1), (2, 2, 2), (-2, -2), (0, 0, 0),
          (1, -1), (-1, 1), (3, 1, 2), (-3, -1, -2),
          (2, -2, 2, -2), (1, 2, 3, 4), (4, 3, 2, 1))


def _evaluation_inputs(domain: Domain):
    seen = set(_TRAIN)

    def unique(values, category):
        key = tuple(values)
        if key not in seen:
            seen.add(key)
            return (list(key), category)
        return None

    for length in range(5):
        for values in itertools.product(range(-2, 3), repeat=length):
            row = unique(values, 'exhaustive-small')
            if row is not None:
                yield row
    lo, hi, n = domain.min_value, domain.max_value, domain.max_length
    boundaries = ([lo], [hi], [lo, hi], [hi, lo], [lo]*n, [hi]*n,
                  [0]*n, [lo, hi]*(n//2), [hi, 0, lo, 0]*(n//4),
                  list(range(-n//2, n//2)))
    for values in boundaries:
        # The product domain has a narrower alphabet than the general lane.
        values = [max(lo, min(hi, x)) for x in values]
        row = unique(values, 'domain-boundary')
        if row is not None:
            yield row
    rng = random.Random(SEED)
    for i in range(192):
        length = rng.randint(5, n)
        alphabet = (lo, -1, 0, 1, hi) if i % 3 == 0 else tuple(range(-4, 5))
        values = ([rng.choice(alphabet) for _ in range(length)] if i % 3 != 2
                  else [rng.randint(lo, hi) for _ in range(length)])
        row = unique(values, 'seeded-varied')
        if row is not None:
            yield row


def tasks(*, include_evaluation: bool = True) -> tuple[Task, ...]:
    """Return fresh contracts so caller mutation cannot poison later runs."""
    result = []
    for name, description, _ in _SPECS:
        domain = domain_for(name)
        train = tuple(Case((list(a),), expected(name, list(a)), 'train', 'authored')
                      for a in _TRAIN)
        evaluation = (tuple(Case((a,), expected(name, a), 'evaluation', category)
                            for a, category in _evaluation_inputs(domain))
                      if include_evaluation else ())
        result.append(Task(name, description, train, evaluation, domain))
    return tuple(result)
