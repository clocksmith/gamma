"""Original frontend 1430 variant; qualification unknown."""
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


def solve(root, arr) -> bool:
    if isinstance(root, list):
        root = _from_level(root)
    stack = [(root, 0)]
    m = len(arr)
    while stack:
        node, idx = stack.pop()
        if node is None or idx >= m or node.val != arr[idx]:
            continue
        if node.left is None and node.right is None:
            if idx == m - 1:
                return True
        else:
            stack.append((node.left, idx + 1))
            stack.append((node.right, idx + 1))
    return False


isValidSequence = solve


class Solution:
    def isValidSequence(self, root, arr) -> bool:
        return solve(root, arr)
