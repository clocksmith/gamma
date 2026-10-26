"""814. Binary Tree Pruning: prune zero-only child links in iterative postorder."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None) -> TreeNode | None:
    """O(n) time/space; prune zero-only child links and retain surviving nodes."""
    if root is None:
        return None
    kept = {}
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
        if not kept.get(id(node.left), False):
            node.left = None
        if not kept.get(id(node.right), False):
            node.right = None
        kept[id(node)] = bool(node.val or node.left is not None or node.right is not None)
    return root if kept[id(root)] else None


class Solution:
    def pruneTree(self, root: TreeNode | None) -> TreeNode | None:
        return solve(root)
