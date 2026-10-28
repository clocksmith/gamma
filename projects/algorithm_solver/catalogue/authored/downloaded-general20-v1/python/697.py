"""697. Degree of an Array (Easy).

Specification: https://leetcode.com/problems/degree-of-an-array/description/
"""


def solve(nums: list[int]) -> int:
    first = {}
    last = {}
    count = {}
    degree = 0
    for index, value in enumerate(nums):
        if value not in first:
            first[value] = index
        last[value] = index
        count[value] = count.get(value, 0) + 1
        degree = max(degree, count[value])
    shortest = len(nums)
    for value, occurrences in count.items():
        if occurrences == degree:
            shortest = min(shortest, last[value] - first[value] + 1)
    return shortest


class Solution:
    def findShortestSubArray(self, nums: list[int]) -> int:
        return solve(nums)
