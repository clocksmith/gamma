"""1189. Maximum Number of Balloons (Easy).

Specification: https://leetcode.com/problems/maximum-number-of-balloons/description/
"""


def solve(text: str) -> int:
    counts = {}
    for ch in text:
        counts[ch] = counts.get(ch, 0) + 1
    return min(counts.get('b', 0), counts.get('a', 0), counts.get('l', 0) // 2, counts.get('o', 0) // 2, counts.get('n', 0))


class Solution:
    def maxNumberOfBalloons(self, text: str) -> int:
        return solve(text)
