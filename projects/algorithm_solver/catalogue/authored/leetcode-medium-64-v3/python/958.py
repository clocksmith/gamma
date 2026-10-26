"""958. Check Completeness of a Binary Tree: reject a nonempty level-order position after the first gap."""
from __future__ import annotations
from collections import deque


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None) -> bool:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    queue = deque([root])
    gap = False
    while queue:
        node = queue.popleft()
        if node is None:
            gap = True
        else:
            if gap:
                return False
            queue.append(node.left)
            queue.append(node.right)
    return True


class Solution:
    def isCompleteTree(self, root: TreeNode | None) -> bool:
        return solve(root)
