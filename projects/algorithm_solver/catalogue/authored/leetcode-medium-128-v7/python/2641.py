"""2641. Cousins in Binary Tree II: build a new tree from level totals minus each sibling group."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left: TreeNode | None = None, right: TreeNode | None = None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None) -> TreeNode | None:
    """O(n) time and O(n) auxiliary space including the independent result tree; inputs are read-only."""
    if root is None:
        return None
    result = TreeNode(0)
    level = [(root, result)]
    while level:
        total = 0
        for original, _ in level:
            if original.left is not None:
                total += original.left.val
            if original.right is not None:
                total += original.right.val
        following = []
        for original, copied in level:
            siblings = (original.left.val if original.left is not None else 0)
            siblings += original.right.val if original.right is not None else 0
            if original.left is not None:
                copied.left = TreeNode(total - siblings)
                following.append((original.left, copied.left))
            if original.right is not None:
                copied.right = TreeNode(total - siblings)
                following.append((original.right, copied.right))
        level = following
    return result


class Solution:
    def replaceValueInTree(self, root: TreeNode | None) -> TreeNode | None:
        return solve(root)
