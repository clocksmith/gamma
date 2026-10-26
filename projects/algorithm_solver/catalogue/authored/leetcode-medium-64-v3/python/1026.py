"""1026. Maximum Difference Between Node and Ancestor: carry the path minimum and maximum through an explicit stack."""
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
    best = 0
    stack = [(root, root.val, root.val)]
    while stack:
        node, low, high = stack.pop()
        low = min(low, node.val)
        high = max(high, node.val)
        best = max(best, high - low)
        if node.left is not None:
            stack.append((node.left, low, high))
        if node.right is not None:
            stack.append((node.right, low, high))
    return best


class Solution:
    def maxAncestorDiff(self, root: TreeNode | None) -> int:
        return solve(root)
