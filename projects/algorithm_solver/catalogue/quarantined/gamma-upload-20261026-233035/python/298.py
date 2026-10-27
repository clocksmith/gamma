"""298. Binary Tree Longest Consecutive Sequence."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> int:
    if root is None:
        return 0
    best = 0
    stack = [(root, root.val - 1, 0)]
    while stack:
        node, previous, length = stack.pop()
        current = length + 1 if node.val == previous + 1 else 1
        best = max(best, current)
        if node.left is not None:
            stack.append((node.left, node.val, current))
        if node.right is not None:
            stack.append((node.right, node.val, current))
    return best

class Solution:
    def longestConsecutive(self, root):
        return solve(root)
