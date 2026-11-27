"""Tested helper implementations and boundary-behavior contracts for BITS paired-switch-v1.

Every experimental arm (frozen alias, score-only alias, score-and-input alias,
and ordinary named function baseline) executes the exact same tested helper
implementation recorded here.
"""

from __future__ import annotations

import hashlib
import inspect
from dataclasses import dataclass
from typing import Any, Callable


def skip_equal(xs: list[Any], i: int) -> int:
    """Return the first index > i where xs[j] != xs[i], or len(xs) if at/past end.

    Boundary behaviors (tested and recorded at the switch point):
    - empty suffix (i >= len(xs), including xs == []): returns len(xs)
    - run of duplicates (xs[i] == xs[i+1] == ...): skips the entire equal run
    - end of array (run reaches len(xs), or singleton suffix): returns len(xs)
    """
    n = len(xs)
    if not isinstance(i, int) or isinstance(i, bool) or i < 0:
        raise ValueError("index i must be a non-negative integer")
    if i >= n:
        return n
    val = xs[i]
    j = i + 1
    while j < n and xs[j] == val:
        j += 1
    return j


def merge_span(acc: list[list[int]], start: int, end: int) -> list[list[int]]:
    """Merge closed interval [start, end] into sorted disjoint list acc in-place and return acc.

    Boundary behaviors:
    - empty accumulator: appends [start, end]
    - overlapping or touching span (start <= acc[-1][1]): extends acc[-1][1]
    - disjoint span (start > acc[-1][1]): appends [start, end]
    """
    if start > end:
        raise ValueError("interval start must be <= end")
    if not acc or start > acc[-1][1]:
        acc.append([start, end])
    elif end > acc[-1][1]:
        acc[-1][1] = end
    return acc


def push_unvisited(queue: list[Any], visited: set[Any], neighbors: list[Any]) -> int:
    """Append each unseen neighbor to queue, mark in visited, and return count added.

    Boundary behaviors:
    - empty neighbors list: returns 0 without modifying queue or visited
    - duplicate entries or self-loops in neighbors: pushed at most once
    - all neighbors already visited: returns 0 without duplicates
    """
    added = 0
    for nxt in neighbors:
        if nxt not in visited:
            visited.add(nxt)
            queue.append(nxt)
            added += 1
    return added


@dataclass(frozen=True)
class HelperSpec:
    name: str
    family: str
    signature: str
    call_template: str
    description: str
    operand_convention: str
    syntax_mask_regex: str
    implementation: Callable[..., Any]
    boundary_cases: tuple[dict[str, Any], ...]

    def source_code(self) -> str:
        return inspect.getsource(self.implementation)

    def implementation_sha256(self) -> str:
        return hashlib.sha256(self.source_code().encode("utf-8")).hexdigest()

    def exposure_block(self, operator_symbol: str) -> str:
        """Render the exact matched switch-time exposure block for any arm.

        Matches assignment, arguments, punctuation, syntax convention, and
        boundary documentation across all arms; only the operator name differs
        between `<H0>` alias arms and the ordinary named-function baseline.
        """
        call_expr = self.call_template.format(OP=operator_symbol)
        lines = [
            f"HELPER_OPERATOR: {operator_symbol}",
            f"CALL_CONVENTION: {call_expr}",
            f"DESCRIPTION: {self.description}",
            f"OPERAND_CONVENTION: {self.operand_convention.format(OP=operator_symbol)}",
            "BOUNDARY_BEHAVIOR:",
        ]
        for case in self.boundary_cases:
            lines.append(
                f"  - {case['label']}: {operator_symbol}({case['args_repr']}) -> {case['expected_repr']}"
            )
        lines.append(f"SYNTAX_MASK: {self.syntax_mask_regex.format(OP=operator_symbol)}")
        return "\n".join(lines)


HELPER_SPECS: dict[str, HelperSpec] = {
    "skip_equal": HelperSpec(
        name="skip_equal",
        family="duplicate_handling",
        signature="skip_equal(xs, i) -> int",
        call_template="j = {OP}(xs, i)",
        description=(
            "Given sequence xs and non-negative index i, return the smallest index j > i "
            "with xs[j] != xs[i], or len(xs) when i >= len(xs) or the equal run reaches the end."
        ),
        operand_convention=(
            "Assign result via `j = {OP}(xs, i)` with sequence `xs` and integer index `i` "
            "(exact positional arguments, comma-space separator, parentheses required)."
        ),
        syntax_mask_regex=r"[A-Za-z_][A-Za-z0-9_]*\s*=\s*{OP}\([^,()]+,\s*[^,()]+\)",
        implementation=skip_equal,
        boundary_cases=(
            {
                "label": "empty_suffix_empty_list",
                "args": ([], 0),
                "args_repr": "[], 0",
                "expected": 0,
                "expected_repr": "0",
            },
            {
                "label": "empty_suffix_at_len",
                "args": ([1, 2], 2),
                "args_repr": "[1, 2], 2",
                "expected": 2,
                "expected_repr": "2",
            },
            {
                "label": "run_of_duplicates_prefix",
                "args": ([2, 2, 2, 5], 0),
                "args_repr": "[2, 2, 2, 5], 0",
                "expected": 3,
                "expected_repr": "3",
            },
            {
                "label": "run_of_duplicates_interior",
                "args": ([1, 4, 4, 4, 9], 1),
                "args_repr": "[1, 4, 4, 4, 9], 1",
                "expected": 4,
                "expected_repr": "4",
            },
            {
                "label": "end_of_array_duplicate_tail",
                "args": ([1, 3, 3], 1),
                "args_repr": "[1, 3, 3], 1",
                "expected": 3,
                "expected_repr": "3",
            },
            {
                "label": "end_of_array_singleton_tail",
                "args": ([1, 5], 1),
                "args_repr": "[1, 5], 1",
                "expected": 2,
                "expected_repr": "2",
            },
        ),
    ),
    "merge_span": HelperSpec(
        name="merge_span",
        family="interval_processing",
        signature="merge_span(acc, start, end) -> list[list[int]]",
        call_template="acc = {OP}(acc, start, end)",
        description=(
            "Merge closed interval [start, end] into sorted disjoint interval list acc "
            "(in-place) and return acc."
        ),
        operand_convention=(
            "Assign result via `acc = {OP}(acc, start, end)` with sorted disjoint list `acc` "
            "and integers `start <= end`."
        ),
        syntax_mask_regex=r"[A-Za-z_][A-Za-z0-9_]*\s*=\s*{OP}\([^,()]+,\s*[^,()]+,\s*[^,()]+\)",
        implementation=merge_span,
        boundary_cases=(
            {
                "label": "empty_acc",
                "args": ([], 1, 3),
                "args_repr": "[], 1, 3",
                "expected": [[1, 3]],
                "expected_repr": "[[1, 3]]",
            },
            {
                "label": "overlapping_and_touching",
                "args": ([[1, 3]], 3, 5),
                "args_repr": "[[1, 3]], 3, 5",
                "expected": [[1, 5]],
                "expected_repr": "[[1, 5]]",
            },
            {
                "label": "contained_span",
                "args": ([[1, 8]], 2, 4),
                "args_repr": "[[1, 8]], 2, 4",
                "expected": [[1, 8]],
                "expected_repr": "[[1, 8]]",
            },
            {
                "label": "disjoint_span",
                "args": ([[1, 3]], 5, 7),
                "args_repr": "[[1, 3]], 5, 7",
                "expected": [[1, 3], [5, 7]],
                "expected_repr": "[[1, 3], [5, 7]]",
            },
        ),
    ),
    "push_unvisited": HelperSpec(
        name="push_unvisited",
        family="graph_traversal",
        signature="push_unvisited(queue, visited, neighbors) -> int",
        call_template="added = {OP}(queue, visited, neighbors)",
        description=(
            "Append every unseen element of neighbors to queue, add it to visited, "
            "and return the number of newly enqueued nodes."
        ),
        operand_convention=(
            "Assign result via `added = {OP}(queue, visited, neighbors)` with list `queue`, "
            "set `visited`, and iterable `neighbors`."
        ),
        syntax_mask_regex=r"[A-Za-z_][A-Za-z0-9_]*\s*=\s*{OP}\([^,()]+,\s*[^,()]+,\s*[^,()]+\)",
        implementation=push_unvisited,
        boundary_cases=(
            {
                "label": "empty_neighbors",
                "args": ([], {0}, []),
                "args_repr": "[], {0}, []",
                "expected": 0,
                "expected_repr": "0",
            },
            {
                "label": "duplicates_and_self_loop",
                "args": ([], {0}, [0, 1, 1, 2, 1]),
                "args_repr": "[], {0}, [0, 1, 1, 2, 1]",
                "expected": 2,
                "expected_repr": "2",
            },
            {
                "label": "all_seen",
                "args": ([], {0, 1, 2}, [1, 2]),
                "args_repr": "[], {0, 1, 2}, [1, 2]",
                "expected": 0,
                "expected_repr": "0",
            },
        ),
    ),
}


def verify_all_helpers() -> dict[str, dict[str, Any]]:
    """Run every declared boundary case for every helper and return a receipt."""
    receipt: dict[str, dict[str, Any]] = {}
    for name, spec in HELPER_SPECS.items():
        case_results = []
        for case in spec.boundary_cases:
            # Copy mutable inputs so boundary definitions remain clean.
            args = []
            for item in case["args"]:
                if isinstance(item, list):
                    args.append([x[:] if isinstance(x, list) else x for x in item])
                elif isinstance(item, set):
                    args.append(set(item))
                else:
                    args.append(item)
            actual = spec.implementation(*args)
            if actual != case["expected"]:
                raise AssertionError(
                    f"Helper {name} failed boundary case {case['label']}: "
                    f"expected {case['expected']!r}, got {actual!r}"
                )
            case_results.append(
                {
                    "label": case["label"],
                    "args_repr": case["args_repr"],
                    "expected": case["expected"],
                    "actual": actual,
                    "ok": True,
                }
            )
        # Verify negative index rejection for skip_equal.
        if name == "skip_equal":
            try:
                skip_equal([1, 2], -1)
            except ValueError:
                pass
            else:
                raise AssertionError("skip_equal accepted negative index")
        receipt[name] = {
            "family": spec.family,
            "signature": spec.signature,
            "implementation_sha256": spec.implementation_sha256(),
            "cases_passed": len(case_results),
            "cases": case_results,
        }
    return receipt
