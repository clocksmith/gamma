"""1305. All Elements in Two Binary Search Trees: merge two iterative inorder traversals."""
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root1: TreeNode | None, root2: TreeNode | None) -> list[int]:
    """O(n + m) time and O(n + m) auxiliary space; inputs are read-only."""
    def values(root):
        ordered = []
        stack = []
        current = root
        while current is not None or stack:
            while current is not None:
                stack.append(current)
                current = current.left
            current = stack.pop()
            ordered.append(current.val)
            current = current.right
        return ordered

    first, second = values(root1), values(root2)
    result = []
    left = right = 0
    while left < len(first) and right < len(second):
        if first[left] <= second[right]:
            result.append(first[left])
            left += 1
        else:
            result.append(second[right])
            right += 1
    result.extend(first[left:])
    result.extend(second[right:])
    return result


class Solution:
    def getAllElements(self, root1: TreeNode | None, root2: TreeNode | None) -> list[int]:
        return solve(root1, root2)
