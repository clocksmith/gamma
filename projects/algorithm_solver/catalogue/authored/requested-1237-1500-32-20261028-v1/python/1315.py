"""Original frontend 1315 variant; qualification unknown."""
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


def solve(root) -> int:
    if isinstance(root, list):
        root = _from_level(root)
    if root is None:
        return 0
    total = 0
    stack = [(root, 1, 1)]
    while stack:
        node, p, gp = stack.pop()
        if (gp & 1) == 0:
            total += node.val
        if node.left is not None:
            stack.append((node.left, node.val, p))
        if node.right is not None:
            stack.append((node.right, node.val, p))
    return total


sumEvenGrandparent = solve


class Solution:
    def sumEvenGrandparent(self, root) -> int:
        return solve(root)
