"""2848. Points That Intersect With Cars (Easy).

Specification: https://leetcode.com/problems/points-that-intersect-with-cars/description/
"""


def solve(nums: list[list[int]]) -> int:
    """O(n + U) time, O(U) space; U = 100; preserve inclusive intervals."""
    maximum_point = 100
    changes = [0] * (maximum_point + 2)
    for start, end in nums:
        changes[start] += 1
        changes[end + 1] -= 1
    coverage = 0
    result = 0
    for point in range(1, maximum_point + 1):
        coverage += changes[point]
        if coverage > 0:
            result += 1
    return result


class Solution:
    def numberOfPoints(self, nums: list[list[int]]) -> int:
        return solve(nums)
