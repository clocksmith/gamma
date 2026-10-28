"""491. Non-decreasing Subsequences (Medium).

Specification: https://leetcode.com/problems/non-decreasing-subsequences/description/
"""


def solve(nums: list[int]) -> list[list[int]]:
    seen = set()
    result = []

    def backtrack(start, current):
        if len(current) >= 2:
            key = tuple(current)
            if key not in seen:
                seen.add(key)
                result.append(current[:])
        for i in range(start, len(nums)):
            if not current or nums[i] >= current[-1]:
                current.append(nums[i])
                backtrack(i + 1, current)
                current.pop()

    backtrack(0, [])
    result.sort(key=lambda seq: ",".join(str(v) for v in seq))
    return result


class Solution:
    def findSubsequences(self, nums: list[int]) -> list[list[int]]:
        return solve(nums)
