"""1913. Maximum Product Difference Between Two Pairs (Easy).

Specification: https://leetcode.com/problems/maximum-product-difference-between-two-pairs/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; keep two extrema with multiplicity; preserve nums."""
    smallest = float('inf')
    second_smallest = float('inf')
    largest = float('-inf')
    second_largest = float('-inf')
    for value in nums:
        if value <= smallest:
            second_smallest = smallest
            smallest = value
        elif value < second_smallest:
            second_smallest = value
        if value >= largest:
            second_largest = largest
            largest = value
        elif value > second_largest:
            second_largest = value
    return largest * second_largest - smallest * second_smallest


class Solution:
    def maxProductDifference(self, nums: list[int]) -> int:
        return solve(nums)
