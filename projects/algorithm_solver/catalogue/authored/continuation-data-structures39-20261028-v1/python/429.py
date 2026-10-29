"""Original frontend 429 variant; qualification unknown."""
from collections import deque


class Node:
    def __init__(self, val=None, children=None):
        self.val = val
        self.children = [] if children is None else list(children)


def _from_nary_list(arr):
    if not arr or arr[0] is None:
        return None
    root = Node(arr[0], [])
    q = deque([root])
    i = 2
    while q and i < len(arr):
        parent = q.popleft()
        while i < len(arr) and arr[i] is not None:
            child = Node(arr[i], [])
            parent.children.append(child)
            q.append(child)
            i += 1
        i += 1
    return root


def solve(root):
    if isinstance(root, list):
        root = _from_nary_list(root)
    if root is None:
        return []
    out = []
    q = deque([root])
    while q:
        level = []
        for _ in range(len(q)):
            node = q.popleft()
            level.append(node.val)
            for ch in node.children or ():
                q.append(ch)
        out.append(level)
    return out


levelOrder = solve


class Solution:
    def levelOrder(self, root):
        return solve(root)
