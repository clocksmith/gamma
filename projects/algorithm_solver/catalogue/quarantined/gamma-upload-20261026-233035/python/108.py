"""108. Convert Sorted Array to Binary Search Tree."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(nums: list[int]) -> TreeNode | None:
    def build(left: int, right: int):
        if left >= right:
            return None
        middle = (left + right) // 2
        return TreeNode(nums[middle], build(left, middle), build(middle + 1, right))
    return build(0, len(nums))

class Solution:
    def sortedArrayToBST(self, nums: list[int]):
        return solve(nums)
