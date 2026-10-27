"""654. Maximum Binary Tree. Monotone stack builds the Cartesian tree in O(n) time."""

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(nums: list[int]):
    stack = []
    for value in nums:
        node = TreeNode(value)
        while stack and stack[-1].val < value:
            node.left = stack.pop()
        if stack:
            stack[-1].right = node
        stack.append(node)
    return stack[0] if stack else None


class Solution:
    def constructMaximumBinaryTree(self, nums: list[int]):
        return solve(nums)
