"""3722. Lexicographically Smallest String After Reverse."""
from __future__ import annotations


def solve(s: str) -> str:
    """O(n^2) time and O(n) auxiliary space; reversing one character permits the unchanged string."""
    answer = s
    for length in range(1, len(s) + 1):
        answer = min(answer, s[:length][::-1] + s[length:])
        answer = min(answer, s[:-length] + s[-length:][::-1])
    return answer


class Solution:
    def lexSmallest(self, s: str) -> str:
        return solve(s)
