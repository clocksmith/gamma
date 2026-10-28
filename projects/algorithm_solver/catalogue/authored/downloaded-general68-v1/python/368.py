"""368. Largest Divisible Subset (Medium).

Specification: https://leetcode.com/problems/largest-divisible-subset/description/
"""


def solve(nums: list[int]) -> list[int]:
    ordered = sorted(nums)
    dp = [1] * len(ordered)
    previous = [-1] * len(ordered)
    best_index = 0
    for i in range(len(ordered)):
        for j in range(i):
            if ordered[i] % ordered[j] == 0 and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                previous[i] = j
        if dp[i] > dp[best_index]:
            best_index = i
    result = []
    index = best_index
    while index != -1:
        result.append(ordered[index])
        index = previous[index]
    return result[::-1]


class Solution:
    def largestDivisibleSubset(self, nums: list[int]) -> list[int]:
        return solve(nums)
