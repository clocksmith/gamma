"""129. Sum Root to Leaf Numbers."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> int:
    if root is None:
        return 0
    total = 0
    stack = [(root, 0)]
    while stack:
        node, prefix = stack.pop()
        value = prefix * 10 + node.val
        if node.left is None and node.right is None:
            total += value
        else:
            if node.right is not None:
                stack.append((node.right, value))
            if node.left is not None:
                stack.append((node.left, value))
    return total

class Solution:
    def sumNumbers(self, root):
        return solve(root)
