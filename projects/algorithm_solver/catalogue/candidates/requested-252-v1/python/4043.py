"""4043. Count Rotations With Exactly K Equal Adjacent Pairs.

Specification: https://leetcode.com/problems/count-rotations-with-exactly-k-equal-adjacent-pairs/description/
"""

from __future__ import annotations


def solve(s: str, k: int) -> int:
    """O(n) time and O(1) auxiliary space; count rotations by cut position, including identical resulting strings. Inputs are preserved."""
    circular = sum(s[index] == s[(index + 1) % len(s)] for index in range(len(s)))
    return sum(circular - int(s[index] == s[(index + 1) % len(s)]) == k
               for index in range(len(s)))
