"""1008. Construct Binary Search Tree from Preorder Traversal: use an ancestor stack to attach each distinct value."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(preorder: list[int]) -> TreeNode | None:
    """O(n) time and O(n) auxiliary space excluding the returned tree; inputs are read-only."""
    if not preorder:
        return None
    root = TreeNode(preorder[0])
    stack = [root]
    for index in range(1, len(preorder)):
        node = TreeNode(preorder[index])
        if node.val < stack[-1].val:
            stack[-1].left = node
        else:
            parent = stack.pop()
            while stack and stack[-1].val < node.val:
                parent = stack.pop()
            parent.right = node
        stack.append(node)
    return root


class Solution:
    def bstFromPreorder(self, preorder: list[int]) -> TreeNode | None:
        return solve(preorder)
