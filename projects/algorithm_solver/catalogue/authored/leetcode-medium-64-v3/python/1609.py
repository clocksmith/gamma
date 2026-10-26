"""1609. Even Odd Tree: validate parity and strict ordering one level at a time."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None) -> bool:
    """O(n) time and O(w) auxiliary space for maximum level width w; inputs are read-only."""
    if root is None:
        return True
    level = [root]
    even_level = True
    while level:
        previous = float('-inf') if even_level else float('inf')
        following = []
        for node in level:
            if even_level:
                if node.val % 2 == 0 or node.val <= previous:
                    return False
            elif node.val % 2 != 0 or node.val >= previous:
                return False
            previous = node.val
            if node.left is not None:
                following.append(node.left)
            if node.right is not None:
                following.append(node.right)
        level = following
        even_level = not even_level
    return True


class Solution:
    def isEvenOddTree(self, root: TreeNode | None) -> bool:
        return solve(root)
