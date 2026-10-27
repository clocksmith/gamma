"""236. Lowest Common Ancestor of a Binary Tree."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None, p: TreeNode, q: TreeNode) -> TreeNode | None:
    if root is None or root is p or root is q:
        return root
    left = solve(root.left, p, q)
    right = solve(root.right, p, q)
    return root if left is not None and right is not None else left or right

class Solution:
    def lowestCommonAncestor(self, root, p, q):
        return solve(root, p, q)
