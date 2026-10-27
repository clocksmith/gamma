"""257. Binary Tree Paths."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> list[str]:
    if root is None:
        return []
    result = []
    stack = [(root, str(root.val))]
    while stack:
        node, path = stack.pop()
        if node.left is None and node.right is None:
            result.append(path)
        if node.right is not None:
            stack.append((node.right, path + '->' + str(node.right.val)))
        if node.left is not None:
            stack.append((node.left, path + '->' + str(node.left.val)))
    return result

class Solution:
    def binaryTreePaths(self, root):
        return solve(root)
