"""272. Closest Binary Search Tree Value II."""
from __future__ import annotations

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode, target: float, k: int) -> list[int]:
    predecessors = []
    successors = []
    current = root
    while current is not None:
        if current.val <= target:
            predecessors.append(current)
            current = current.right
        else:
            successors.append(current)
            current = current.left

    def previous():
        node = predecessors.pop()
        value = node.val
        node = node.left
        while node is not None:
            predecessors.append(node)
            node = node.right
        return value

    def following():
        node = successors.pop()
        value = node.val
        node = node.right
        while node is not None:
            successors.append(node)
            node = node.left
        return value

    result = []
    for _ in range(k):
        if not successors or predecessors and target - predecessors[-1].val <= successors[-1].val - target:
            result.append(previous())
        else:
            result.append(following())
    return result

class Solution:
    def closestKValues(self, root, target, k):
        return solve(root, target, k)
