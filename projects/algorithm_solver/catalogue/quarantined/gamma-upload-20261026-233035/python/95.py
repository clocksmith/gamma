"""95. Unique Binary Search Trees II."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def clone(root):
    return None if root is None else TreeNode(root.val, clone(root.left), clone(root.right))

def solve(n: int) -> list[TreeNode | None]:
    def build(low: int, high: int):
        if low > high:
            return [None]
        trees = []
        for value in range(low, high + 1):
            for left in build(low, value - 1):
                for right in build(value + 1, high):
                    trees.append(TreeNode(value, clone(left), clone(right)))
        return trees
    return build(1, n) if n else []

class Solution:
    def generateTrees(self, n: int):
        return solve(n)
