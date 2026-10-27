"""3996. Even Number of Knight Moves.

Specification: https://leetcode.com/problems/even-number-of-knight-moves/description/
"""

from __future__ import annotations


def solve(start: list[int], target: list[int]) -> bool:
    """O(1) time and space; the standard 8x8 knight graph is connected and bipartite. Inputs are preserved."""
    return (start[0] + start[1]) % 2 == (target[0] + target[1]) % 2
