"""366. Find Leaves of Binary Tree."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> list[list[int]]:
    result = []
    def height(node):
        if node is None:
            return -1
        value = 1 + max(height(node.left), height(node.right))
        if value == len(result):
            result.append([])
        result[value].append(node.val)
        return value
    height(root)
    return result

class Solution:
    def findLeaves(self, root):
        return solve(root)
