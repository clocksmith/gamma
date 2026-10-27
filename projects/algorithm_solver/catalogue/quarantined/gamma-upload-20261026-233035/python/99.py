"""99. Recover Binary Search Tree."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> None:
    first = second = previous = None
    stack = []
    current = root
    while current is not None or stack:
        while current is not None:
            stack.append(current)
            current = current.left
        current = stack.pop()
        if previous is not None and previous.val > current.val:
            if first is None:
                first = previous
            second = current
        previous = current
        current = current.right
    if first is not None:
        first.val, second.val = second.val, first.val

class Solution:
    def recoverTree(self, root: TreeNode | None) -> None:
        solve(root)
