"""998. Maximum Binary Tree II: copy the tree and insert along its right spine."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None, val: int) -> TreeNode:
    """O(n) time and O(n) auxiliary space including the nonaliasing copy; inputs are read-only."""
    inserted = TreeNode(val)
    if root is None:
        return inserted
    result = TreeNode(root.val)
    stack = [(root, result)]
    while stack:
        original, copied = stack.pop()
        if original.left is not None:
            copied.left = TreeNode(original.left.val)
            stack.append((original.left, copied.left))
        if original.right is not None:
            copied.right = TreeNode(original.right.val)
            stack.append((original.right, copied.right))
    if val > result.val:
        inserted.left = result
        return inserted
    current = result
    while current.right is not None and current.right.val > val:
        current = current.right
    inserted.left = current.right
    current.right = inserted
    return result


class Solution:
    def insertIntoMaxTree(self, root: TreeNode | None, val: int) -> TreeNode:
        return solve(root, val)
