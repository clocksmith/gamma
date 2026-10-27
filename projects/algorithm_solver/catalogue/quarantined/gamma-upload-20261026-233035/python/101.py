"""101. Symmetric Tree."""
from __future__ import annotations
from collections import deque

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> bool:
    if root is None:
        return True
    queue = deque([(root.left, root.right)])
    while queue:
        left, right = queue.popleft()
        if left is None or right is None:
            if left is not right:
                return False
            continue
        if left.val != right.val:
            return False
        queue.append((left.left, right.right))
        queue.append((left.right, right.left))
    return True

class Solution:
    def isSymmetric(self, root):
        return solve(root)
