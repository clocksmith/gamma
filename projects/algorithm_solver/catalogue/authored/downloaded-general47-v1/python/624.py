"""624. Maximum Distance in Arrays (Medium).

Specification: https://leetcode.com/problems/maximum-distance-in-arrays/description/
"""


def solve(arrays: list[list[int]]) -> int:
    smallest = arrays[0][0]
    largest = arrays[0][-1]
    best = 0
    for current in arrays[1:]:
        best = max(best, abs(current[-1] - smallest), abs(current[0] - largest))
        smallest = min(smallest, current[0])
        largest = max(largest, current[-1])
    return best


class Solution:
    def maxDistance(self, arrays: list[list[int]]) -> int:
        return solve(arrays)
