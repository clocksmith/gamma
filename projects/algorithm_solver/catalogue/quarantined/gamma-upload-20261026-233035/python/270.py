"""270. Closest Binary Search Tree Value."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode, target: float) -> int:
    closest = root.val
    current = root
    while current is not None:
        if abs(current.val - target) < abs(closest - target) or abs(current.val - target) == abs(closest - target) and current.val < closest:
            closest = current.val
        current = current.left if target < current.val else current.right
    return closest

class Solution:
    def closestValue(self, root, target):
        return solve(root, target)
