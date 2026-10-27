"""199. Binary Tree Right Side View."""
from __future__ import annotations
from collections import deque

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> list[int]:
    if root is None:
        return []
    result = []
    queue = deque([root])
    while queue:
        result.append(queue[-1].val)
        for _ in range(len(queue)):
            node = queue.popleft()
            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)
    return result

class Solution:
    def rightSideView(self, root):
        return solve(root)
