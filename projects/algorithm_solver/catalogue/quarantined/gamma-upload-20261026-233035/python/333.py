"""333. Largest BST Subtree."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> int:
    best = 0
    def visit(node):
        nonlocal best
        if node is None:
            return True, float('inf'), float('-inf'), 0
        left_ok, left_min, left_max, left_size = visit(node.left)
        right_ok, right_min, right_max, right_size = visit(node.right)
        if left_ok and right_ok and left_max < node.val < right_min:
            size = left_size + right_size + 1
            best = max(best, size)
            return True, min(left_min, node.val), max(right_max, node.val), size
        return False, 0, 0, 0
    visit(root)
    return best

class Solution:
    def largestBSTSubtree(self, root):
        return solve(root)
