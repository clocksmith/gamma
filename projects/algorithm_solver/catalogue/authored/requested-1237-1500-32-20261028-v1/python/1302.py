"""Original frontend 1302 variant; qualification unknown."""
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
    q = deque([root])
    level_sum = 0
    while q:
        level_sum = 0
        for _ in range(len(q)):
            node = q.popleft()
            level_sum += node.val
            if node.left is not None:
                q.append(node.left)
            if node.right is not None:
                q.append(node.right)
    return level_sum


deepestLeavesSum = solve


class Solution:
    def deepestLeavesSum(self, root) -> int:
        return solve(root)
