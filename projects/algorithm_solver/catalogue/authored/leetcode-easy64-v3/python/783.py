"""783. Minimum Distance Between BST Nodes (Easy).

Specification: https://leetcode.com/problems/minimum-distance-between-bst-nodes/description/
"""


def solve(root) -> int:
    """O(n) time, O(h) auxiliary space; preserve the supplied tree."""
    stack = []
    node = root
    previous = None
    smallest = float('inf')
    while node is not None or stack:
        while node is not None:
            stack.append(node)
            node = node.left
        node = stack.pop()
        if previous is not None:
            smallest = min(smallest, node.val - previous)
        previous = node.val
        node = node.right
    return smallest


class Solution:
    def minDiffInBST(self, root) -> int:
        return solve(root)
