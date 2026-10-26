"""1339. Maximum Product of Splitted Binary Tree: compare exact products of subtree sums before taking the modulus."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None) -> int:
    """O(n) time and O(n) auxiliary space on the bounded integer domain; inputs are read-only."""
    if root is None:
        return 0
    order = [root]
    for node in order:
        if node.left is not None:
            order.append(node.left)
        if node.right is not None:
            order.append(node.right)
    sums = {}
    for node in reversed(order):
        sums[id(node)] = node.val + sums.get(id(node.left), 0) + sums.get(id(node.right), 0)
    total = sums[id(root)]
    best = 0
    for node in order[1:]:
        part = sums[id(node)]
        best = max(best, part * (total - part))
    return best % 1_000_000_007


class Solution:
    def maxProduct(self, root: TreeNode | None) -> int:
        return solve(root)
