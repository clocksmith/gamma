"""2583. Kth Largest Sum in a Binary Tree: collect complete breadth-first level sums and select by descending order."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None, k: int) -> int:
    """O(n + l log l) time and O(n) auxiliary space for l levels; inputs are read-only."""
    if root is None:
        return -1
    sums = []
    frontier = [root]
    while frontier:
        total = 0
        following = []
        for node in frontier:
            total += node.val
            if node.left is not None:
                following.append(node.left)
            if node.right is not None:
                following.append(node.right)
        sums.append(total)
        frontier = following
    if k > len(sums):
        return -1
    sums.sort(reverse=True)
    return sums[k - 1]


class Solution:
    def kthLargestLevelSum(self, root: TreeNode | None, k: int) -> int:
        return solve(root, k)
