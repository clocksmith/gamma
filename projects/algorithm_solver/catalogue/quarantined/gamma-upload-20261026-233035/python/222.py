"""222. Count Complete Tree Nodes."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def height(node):
    value = 0
    while node is not None:
        value += 1
        node = node.left
    return value

def solve(root: TreeNode | None) -> int:
    if root is None:
        return 0
    left_height = height(root.left)
    right_height = height(root.right)
    if left_height == right_height:
        return (1 << left_height) + solve(root.right)
    return (1 << right_height) + solve(root.left)

class Solution:
    def countNodes(self, root):
        return solve(root)
