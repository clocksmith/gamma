"""Original LeetCode 654 candidate; qualification unknown."""

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right


def _clone(root):
    if root is None:
        return None
    result = TreeNode(root.val)
    stack = [(root, result)]
    while stack:
        old, new = stack.pop()
        for side in ('left', 'right'):
            child = getattr(old, side)
            if child is not None:
                copy = TreeNode(child.val)
                setattr(new, side, copy)
                stack.append((child, copy))
    return result



def solve(nums):
    stack = []
    for value in nums:
        node = TreeNode(value)
        while stack and stack[-1].val < value: node.left = stack.pop()
        if stack: stack[-1].right = node
        stack.append(node)
    return stack[0]


class Solution:
    def constructMaximumBinaryTree(self, nums):
        return solve(nums)
