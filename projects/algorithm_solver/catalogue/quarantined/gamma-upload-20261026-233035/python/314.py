"""314. Binary Tree Vertical Order Traversal."""
from __future__ import annotations
from collections import defaultdict, deque

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: TreeNode | None) -> list[list[int]]:
    if root is None:
        return []
    columns = defaultdict(list)
    queue = deque([(root, 0)])
    minimum = maximum = 0
    while queue:
        node, column = queue.popleft()
        columns[column].append(node.val)
        minimum = min(minimum, column)
        maximum = max(maximum, column)
        if node.left is not None:
            queue.append((node.left, column - 1))
        if node.right is not None:
            queue.append((node.right, column + 1))
    return [columns[column] for column in range(minimum, maximum + 1)]

class Solution:
    def verticalOrder(self, root):
        return solve(root)
