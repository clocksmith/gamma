"""4019. Merge Close Characters II.

Specification: https://leetcode.com/problems/merge-close-characters-ii/description/
"""

from __future__ import annotations


def solve(s: str, k: int) -> str:
    """O(n) time and O(n) output space; distances use retained-output indices, preserving leftmost-first deletions. Inputs are preserved."""
    result = []
    last = [-1] * 26
    for character in s:
        code = ord(character) - ord('a')
        # Normalize the retained prefix before considering the new right endpoint.
        if last[code] >= 0 and len(result) - last[code] <= k:
            continue
        last[code] = len(result)
        result.append(character)
    return ''.join(result)
