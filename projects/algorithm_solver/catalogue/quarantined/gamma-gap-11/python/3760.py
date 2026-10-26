"""3760. Maximum Substrings With Distinct Start."""
from __future__ import annotations


def solve(s: str) -> int:
    """O(n) time and O(26) space; cut at the first occurrence of each new starting letter."""
    return len(set(s))


class Solution:
    def maxDistinct(self, s: str) -> int:
        return solve(s)
