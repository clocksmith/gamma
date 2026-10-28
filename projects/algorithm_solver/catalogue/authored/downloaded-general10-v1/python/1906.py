"""1906. Minimum Absolute Difference Queries (Medium).

Specification: https://leetcode.com/problems/minimum-absolute-difference-queries/description/
"""


def solve(nums: list[int], queries: list[list[int]]) -> list[int]:
    pref = [[0] * 101]
    for x in nums:
        row = pref[-1][:]
        row[x] += 1
        pref.append(row)
    out = []
    for left, right in queries:
        prev = -1
        best = -1
        for v in range(1, 101):
            if pref[right + 1][v] - pref[left][v] > 0:
                if prev != -1 and (best == -1 or v - prev < best):
                    best = v - prev
                prev = v
        out.append(best)
    return out


class Solution:
    def minDifference(self, nums: list[int], queries: list[list[int]]) -> list[int]:
        return solve(nums, queries)
