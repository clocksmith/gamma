"""1382. Balance a Binary Search Tree: rebuild fresh nodes from an iterative inorder sequence."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None) -> TreeNode | None:
    """O(n) time and O(n) auxiliary space; reconstruction depth is O(log n); inputs are read-only."""
    ordered = []
    stack = []
    current = root
    while current is not None or stack:
        while current is not None:
            stack.append(current)
            current = current.left
        current = stack.pop()
        ordered.append(current.val)
        current = current.right

    def build(left, right):
        if left >= right:
            return None
        middle = (left + right) // 2
        return TreeNode(ordered[middle], build(left, middle), build(middle + 1, right))

    return build(0, len(ordered))


class Solution:
    def balanceBST(self, root: TreeNode | None) -> TreeNode | None:
        return solve(root)
