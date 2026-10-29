"""Original frontend 1485 variant; qualification unknown."""


class NodeCopy:
    def __init__(self, val=0, left=None, right=None, random=None):
        self.val = val
        self.left = left
        self.right = right
        self.random = random


def solve(root):
    if isinstance(root, list):
        return [None if item is None else [item[0], item[1]] for item in root]
    if root is None:
        return None
    mapping = {}
    stack = [root]
    while stack:
        node = stack.pop()
        if node not in mapping:
            mapping[node] = NodeCopy(node.val)
        if node.left is not None:
            stack.append(node.left)
        if node.right is not None:
            stack.append(node.right)
    for orig, clone in mapping.items():
        if orig.left is not None:
            clone.left = mapping[orig.left]
        if orig.right is not None:
            clone.right = mapping[orig.right]
        if orig.random is not None:
            clone.random = mapping[orig.random]
    return mapping[root]


copyRandomBinaryTree = solve


class Solution:
    def copyRandomBinaryTree(self, root):
        return solve(root)
