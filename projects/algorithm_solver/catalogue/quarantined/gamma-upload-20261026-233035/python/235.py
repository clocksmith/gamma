"""235. Lowest Common Ancestor of a Binary Search Tree."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode, p: TreeNode, q: TreeNode) -> TreeNode:
    low, high = sorted((p.val, q.val))
    current = root
    while current is not None:
        if current.val < low:
            current = current.right
        elif current.val > high:
            current = current.left
        else:
            return current

class Solution:
    def lowestCommonAncestor(self, root, p, q):
        return solve(root, p, q)
