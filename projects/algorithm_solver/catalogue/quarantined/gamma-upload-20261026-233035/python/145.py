"""145. Binary Tree Postorder Traversal."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> list[int]:
    result = []
    stack = [(root, False)] if root is not None else []
    while stack:
        node, ready = stack.pop()
        if ready:
            result.append(node.val)
        else:
            stack.append((node, True))
            if node.right is not None:
                stack.append((node.right, False))
            if node.left is not None:
                stack.append((node.left, False))
    return result

class Solution:
    def postorderTraversal(self, root):
        return solve(root)
