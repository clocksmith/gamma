"""3983. Subsequence After One Replacement.

Specification: https://leetcode.com/problems/subsequence-after-one-replacement/description/
"""

from __future__ import annotations


def solve(s: str, t: str) -> bool:
    """O(len(t)) time and O(1) space; match s as a subsequence of t, with at most one replacement in s. Inputs are preserved."""
    if len(s) > len(t):
        return False
    exact = tolerant = 0
    for character in t:
        previous_exact = exact
        if exact < len(s) and s[exact] == character:
            exact += 1
        matched = tolerant + int(tolerant < len(s) and s[tolerant] == character)
        tolerant = min(len(s), max(matched, previous_exact + 1))
        if tolerant == len(s):
            return True
    return False
