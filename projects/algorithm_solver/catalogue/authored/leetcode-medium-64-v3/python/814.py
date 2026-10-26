"""814. Binary Tree Pruning: build a pruned copy in iterative postorder."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None) -> TreeNode | None:
    """O(n) time and O(n) auxiliary space excluding the returned tree; inputs are read-only."""
    if root is None:
        return None
    copies = {}
    stack = [(root, False)]
    while stack:
        node, ready = stack.pop()
        if not ready:
            stack.append((node, True))
            if node.right is not None:
                stack.append((node.right, False))
            if node.left is not None:
                stack.append((node.left, False))
            continue
        left = copies.get(id(node.left))
        right = copies.get(id(node.right))
        copies[id(node)] = TreeNode(node.val, left, right) if node.val or left or right else None
    return copies[id(root)]


class Solution:
    def pruneTree(self, root: TreeNode | None) -> TreeNode | None:
        return solve(root)
