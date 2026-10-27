"""250. Count Univalue Subtrees."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> int:
    total = 0
    def visit(node):
        nonlocal total
        if node is None:
            return True
        left = visit(node.left)
        right = visit(node.right)
        if not left or not right:
            return False
        if node.left is not None and node.left.val != node.val:
            return False
        if node.right is not None and node.right.val != node.val:
            return False
        total += 1
        return True
    visit(root)
    return total

class Solution:
    def countUnivalSubtrees(self, root):
        return solve(root)
