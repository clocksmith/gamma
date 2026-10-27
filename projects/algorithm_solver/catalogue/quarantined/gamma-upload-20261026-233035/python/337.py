"""337. House Robber III."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> int:
    def visit(node):
        if node is None:
            return 0, 0
        left_skip, left_take = visit(node.left)
        right_skip, right_take = visit(node.right)
        take = node.val + left_skip + right_skip
        skip = max(left_skip, left_take) + max(right_skip, right_take)
        return skip, take
    return max(visit(root))

class Solution:
    def rob(self, root):
        return solve(root)
