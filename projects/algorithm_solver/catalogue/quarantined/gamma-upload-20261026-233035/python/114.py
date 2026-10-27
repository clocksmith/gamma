"""114. Flatten Binary Tree to Linked List."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> None:
    current = root
    while current is not None:
        if current.left is not None:
            predecessor = current.left
            while predecessor.right is not None:
                predecessor = predecessor.right
            predecessor.right = current.right
            current.right = current.left
            current.left = None
        current = current.right

class Solution:
    def flatten(self, root) -> None:
        solve(root)
