"""2554. Maximum Number of Integers to Choose From a Range I (Easy).

Specification: https://leetcode.com/problems/maximum-number-of-integers-to-choose-from-a-range-i/description/
"""


def solve(banned, n, maxSum):
    banned_set = set(banned)
    total = 0
    cnt = 0
    for x in range(1, n + 1):
        if x in banned_set:
            continue
        if total + x > maxSum:
            break
        total += x
        cnt += 1
    return cnt


class Solution:
    def maxCount(self, banned, n, maxSum):
        return solve(banned, n, maxSum)
