"""3713. Longest Balanced Substring I."""
from __future__ import annotations


def solve(s: str) -> int:
    """O(n^2) time and O(26) auxiliary space for lowercase ASCII input."""
    answer = 0
    for left in range(len(s)):
        counts = [0] * 26
        distinct = maximum = 0
        for right in range(left, len(s)):
            index = ord(s[right]) - 97
            if counts[index] == 0:
                distinct += 1
            counts[index] += 1
            maximum = max(maximum, counts[index])
            if maximum * distinct == right - left + 1:
                answer = max(answer, right - left + 1)
    return answer


class Solution:
    def longestBalanced(self, s: str) -> int:
        return solve(s)
