"""1394. Find Lucky Integer in an Array (Easy).

Specification: https://leetcode.com/problems/find-lucky-integer-in-an-array/description/
"""


def solve(arr):
    counts = {}
    for value in arr:
        counts[value] = counts.get(value, 0) + 1
    best = -1
    for value, count in counts.items():
        if value == count:
            best = max(best, value)
    return best


class Solution:
    def findLucky(self, arr):
        return solve(arr)
