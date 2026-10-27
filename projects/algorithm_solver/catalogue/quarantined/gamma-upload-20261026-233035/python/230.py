"""230. Kth Smallest Element in a BST."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None, k: int) -> int:
    stack = []
    current = root
    while True:
        while current is not None:
            stack.append(current)
            current = current.left
        current = stack.pop()
        k -= 1
        if k == 0:
            return current.val
        current = current.right

class Solution:
    def kthSmallest(self, root, k):
        return solve(root, k)
