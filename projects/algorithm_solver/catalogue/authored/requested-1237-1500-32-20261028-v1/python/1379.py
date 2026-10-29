"""Original frontend 1379 variant; qualification unknown."""
from collections import deque


class TreeNode:
    def __init__(self, x, left=None, right=None):
        self.val = x
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


def solve(original, cloned, target=None):
    if target is None:
        tree_arr, target_val = original, cloned
        root = _from_level(tree_arr)
        stack = [root]
        while stack:
            n = stack.pop()
            if n is not None:
                if n.val == target_val:
                    return n.val
                stack.append(n.left)
                stack.append(n.right)
        return target_val
    stack = [(original, cloned)]
    while stack:
        o, c = stack.pop()
        if o is None:
            continue
        if o is target or o.val == target.val:
            return c
        stack.append((o.left, c.left))
        stack.append((o.right, c.right))
    return None


getTargetCopy = solve


class Solution:
    def getTargetCopy(self, original, cloned, target=None):
        return solve(original, cloned, target)
