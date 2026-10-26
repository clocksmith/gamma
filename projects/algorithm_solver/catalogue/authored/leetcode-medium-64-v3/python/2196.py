"""2196. Create Binary Tree From Descriptions: create each node once and locate the parent without an incoming edge."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(descriptions: list[list[int]]) -> TreeNode | None:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    nodes = {}
    children = set()
    for parent, child, is_left in descriptions:
        if parent not in nodes:
            nodes[parent] = TreeNode(parent)
        if child not in nodes:
            nodes[child] = TreeNode(child)
        if is_left:
            nodes[parent].left = nodes[child]
        else:
            nodes[parent].right = nodes[child]
        children.add(child)
    for value, node in nodes.items():
        if value not in children:
            return node
    return None


class Solution:
    def createBinaryTree(self, descriptions: list[list[int]]) -> TreeNode | None:
        return solve(descriptions)
