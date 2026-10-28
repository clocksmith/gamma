"""1375. Number of Times Binary String Is Prefix-Aligned (Medium).

Specification: https://leetcode.com/problems/number-of-times-binary-string-is-prefix-aligned/description/
"""


def solve(flips):
    best = 0
    count = 0
    for i, value in enumerate(flips):
        best = max(best, value)
        if best == i + 1:
            count += 1
    return count


class Solution:
    def numTimesAllBlue(self, flips):
        return solve(flips)
