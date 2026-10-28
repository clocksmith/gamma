"""496. Next Greater Element I (Easy).

Specification: https://leetcode.com/problems/next-greater-element-i/description/
"""


def solve(nums1: list[int], nums2: list[int]) -> list[int]:
    next_greater = {}
    stack = []
    for value in nums2:
        while stack and stack[-1] < value:
            next_greater[stack.pop()] = value
        stack.append(value)
    while stack:
        next_greater[stack.pop()] = -1
    return [next_greater[value] for value in nums1]


class Solution:
    def nextGreaterElement(self, nums1: list[int], nums2: list[int]) -> list[int]:
        return solve(nums1, nums2)
