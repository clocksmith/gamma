"""2385. Amount of Time for Binary Tree to Be Infected: traverse parent and child links outward from the starting node."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None, start: int) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    if root is None:
        return 0
    parents = {id(root): None}
    stack = [root]
    origin = None
    while stack:
        node = stack.pop()
        if node.val == start:
            origin = node
        for child in (node.left, node.right):
            if child is not None:
                parents[id(child)] = node
                stack.append(child)
    if origin is None:
        raise ValueError('start value is absent from the tree')
    seen = {id(origin)}
    frontier = [origin]
    minutes = -1
    while frontier:
        following = []
        minutes += 1
        for node in frontier:
            for neighbor in (node.left, node.right, parents[id(node)]):
                if neighbor is not None and id(neighbor) not in seen:
                    seen.add(id(neighbor))
                    following.append(neighbor)
        frontier = following
    return minutes


class Solution:
    def amountOfTime(self, root: TreeNode | None, start: int) -> int:
        return solve(root, start)
