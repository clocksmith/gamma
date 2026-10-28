"""1525. Number of Good Ways to Split a String (Medium).

Specification: https://leetcode.com/problems/number-of-good-ways-to-split-a-string/description/
"""


def solve(s: str) -> int:
    left_counts = {}
    right_counts = {}
    for ch in s:
        right_counts[ch] = right_counts.get(ch, 0) + 1
    count = 0
    for i in range(len(s) - 1):
        ch = s[i]
        left_counts[ch] = left_counts.get(ch, 0) + 1
        remaining = right_counts[ch] - 1
        if remaining == 0:
            del right_counts[ch]
        else:
            right_counts[ch] = remaining
        if len(left_counts) == len(right_counts):
            count += 1
    return count


class Solution:
    def numSplits(self, s: str) -> int:
        return solve(s)
