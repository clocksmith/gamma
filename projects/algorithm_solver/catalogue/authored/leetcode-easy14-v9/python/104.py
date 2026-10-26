"""104. Maximum Depth of Binary Tree (Easy).

Specification: https://leetcode.com/problems/maximum-depth-of-binary-tree/description/
"""


def solve(root) -> int:
    """O(n) time, O(h) auxiliary space; use an explicit traversal stack and preserve the tree."""
    if root is None:
        return 0
    stack = [(root, 1)]
    deepest = 0
    while stack:
        node, depth = stack.pop()
        deepest = max(deepest, depth)
        if node.right is not None:
            stack.append((node.right, depth + 1))
        if node.left is not None:
            stack.append((node.left, depth + 1))
    return deepest


class Solution:
    def maxDepth(self, root) -> int:
        return solve(root)
