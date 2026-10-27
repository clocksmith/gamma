"""285. Inorder Successor in BST."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None, p: TreeNode) -> TreeNode | None:
    successor = None
    current = root
    while current is not None:
        if p.val < current.val:
            successor = current
            current = current.left
        else:
            current = current.right
    return successor

class Solution:
    def inorderSuccessor(self, root, p):
        return solve(root, p)
