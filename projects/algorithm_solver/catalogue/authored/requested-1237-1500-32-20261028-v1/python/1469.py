"""Original frontend 1469 variant; qualification unknown."""
from collections import deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def _from_level(arr):
    if not arr or arr[0] is None:
        return None
    root = TreeNode(arr[0])
    q = deque([root])
    i = 1
    while q and i < len(arr):
        n = q.popleft()
        if i < len(arr):
            v = arr[i]; i += 1
            if v is not None:
                n.left = TreeNode(v); q.append(n.left)
        if i < len(arr):
            v = arr[i]; i += 1
            if v is not None:
                n.right = TreeNode(v); q.append(n.right)
    return root


def solve(root):
    if isinstance(root, list):
        root = _from_level(root)
    if root is None:
        return []
    out = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node.left is not None and node.right is None:
            out.append(node.left.val)
        elif node.right is not None and node.left is None:
            out.append(node.right.val)
        if node.right is not None:
            stack.append(node.right)
        if node.left is not None:
            stack.append(node.left)
    return out


getLonelyNodes = solve


class Solution:
    def getLonelyNodes(self, root):
        return solve(root)
