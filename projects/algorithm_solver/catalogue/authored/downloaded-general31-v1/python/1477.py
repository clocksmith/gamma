"""1477. Find Two Non-overlapping Sub-arrays Each With Target Sum (Medium).

Specification: https://leetcode.com/problems/find-two-non-overlapping-sub-arrays-each-with-target-sum/description/
"""


def solve(arr: list[int], target: int) -> int:
    intervals = []
    for start in range(len(arr)):
        total = 0
        for end in range(start, len(arr)):
            total += arr[end]
            if total == target:
                intervals.append((start, end, end - start + 1))
    best = float('inf')
    for i in range(len(intervals)):
        for j in range(len(intervals)):
            if intervals[i][1] < intervals[j][0] or intervals[j][1] < intervals[i][0]:
                best = min(best, intervals[i][2] + intervals[j][2])
    return -1 if best == float('inf') else best


class Solution:
    def minSumOfLengths(self, arr: list[int], target: int) -> int:
        return solve(arr, target)
