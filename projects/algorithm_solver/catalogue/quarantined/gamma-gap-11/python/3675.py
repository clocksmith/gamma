"""3675. Minimum Operations to Transform String."""
from __future__ import annotations


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; input is preserved."""
    answer = 0
    for character in s:
        if character != 'a':
            answer = max(answer, 123 - ord(character))
    return answer


class Solution:
    def minOperations(self, s: str) -> int:
        return solve(s)
