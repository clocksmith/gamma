"""978. Longest Turbulent Subarray (Medium).

Specification: https://leetcode.com/problems/longest-turbulent-subarray/description/
"""


def solve(arr: list[int]) -> int:
    if len(arr) == 1:
        return 1
    up = 1
    down = 1
    best = 1
    for i in range(1, len(arr)):
        if arr[i] > arr[i - 1]:
            up = down + 1
            down = 1
        elif arr[i] < arr[i - 1]:
            down = up + 1
            up = 1
        else:
            up = 1
            down = 1
        best = max(best, up, down)
    return best


class Solution:
    def maxTurbulenceSize(self, arr: list[int]) -> int:
        return solve(arr)
