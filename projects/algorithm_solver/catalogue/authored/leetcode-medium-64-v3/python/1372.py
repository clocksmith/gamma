"""1372. Longest ZigZag Path in a Binary Tree: carry alternating path lengths without recursive traversal."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None) -> int:
    """O(n) time and O(h) auxiliary space for height h; inputs are read-only."""
    if root is None:
        return 0
    stack = [(root, 0, 0)]
    best = 0
    while stack:
        node, from_left, from_right = stack.pop()
        best = max(best, from_left, from_right)
        if node.left is not None:
            stack.append((node.left, from_right + 1, 0))
        if node.right is not None:
            stack.append((node.right, 0, from_left + 1))
    return best


class Solution:
    def longestZigZag(self, root: TreeNode | None) -> int:
        return solve(root)
