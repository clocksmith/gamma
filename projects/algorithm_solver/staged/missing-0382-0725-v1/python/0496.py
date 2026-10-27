"""496. Next Greater Element I."""

def solve(nums1: list[int], nums2: list[int]) -> list[int]:
    stack, following = [], {}
    for value in nums2:
        while stack and stack[-1] < value:
            following[stack.pop()] = value
        stack.append(value)
    return [following.get(value, -1) for value in nums1]


class Solution:
    def nextGreaterElement(self, nums1: list[int], nums2: list[int]) -> list[int]:
        return solve(nums1, nums2)
