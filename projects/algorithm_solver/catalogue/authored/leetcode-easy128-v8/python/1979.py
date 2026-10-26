"""1979. Find Greatest Common Divisor of Array (Easy).

Specification: https://leetcode.com/problems/find-greatest-common-divisor-of-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n + log M) time, O(1) space; apply Euclid to the minimum and maximum values."""
    smallest = min(nums)
    largest = max(nums)
    while smallest:
        largest, smallest = smallest, largest % smallest
    return largest


class Solution:
    def findGCD(self, nums: list[int]) -> int:
        return solve(nums)
