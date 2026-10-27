"""156. Binary Tree Upside Down."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> TreeNode | None:
    previous = None
    previous_right = None
    current = root
    while current is not None:
        following = current.left
        current.left = previous_right
        previous_right = current.right
        current.right = previous
        previous = current
        current = following
    return previous

class Solution:
    def upsideDownBinaryTree(self, root):
        return solve(root)
