"""Original frontend 1490 variant; qualification unknown."""


class Node:
    def __init__(self, val=None, children=None):
        self.val = val
        self.children = [] if children is None else list(children)


def solve(root):
    if isinstance(root, list):
        return list(root)
    if root is None:
        return None
    clone = Node(root.val, [])
    stack = [(root, clone)]
    while stack:
        orig, copy = stack.pop()
        for ch in orig.children or ():
            ch_copy = Node(ch.val, [])
            copy.children.append(ch_copy)
            stack.append((ch, ch_copy))
    return clone


cloneTree = solve


class Solution:
    def cloneTree(self, root):
        return solve(root)
