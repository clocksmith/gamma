"""94. Binary Tree Inorder Traversal (Easy).

Specification: https://leetcode.com/problems/binary-tree-inorder-traversal/description/
"""


def solve(root) -> list[int]:
    """O(n) time, O(h) auxiliary space excluding the result; preserve every node and link."""
    result = []
    stack = []
    current = root
    while current is not None or stack:
        while current is not None:
            stack.append(current)
            current = current.left
        current = stack.pop()
        result.append(current.val)
        current = current.right
    return result


class Solution:
    def inorderTraversal(self, root) -> list[int]:
        return solve(root)
