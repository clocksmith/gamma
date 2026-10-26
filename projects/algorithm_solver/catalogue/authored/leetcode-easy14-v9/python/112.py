"""112. Path Sum (Easy).

Specification: https://leetcode.com/problems/path-sum/description/
"""


def solve(root, targetSum: int) -> bool:
    """O(n) time, O(h) auxiliary space; accept only root-to-leaf paths and preserve the tree."""
    if root is None:
        return False
    stack = [(root, targetSum - root.val)]
    while stack:
        node, remaining = stack.pop()
        if node.left is None and node.right is None and remaining == 0:
            return True
        if node.right is not None:
            stack.append((node.right, remaining - node.right.val))
        if node.left is not None:
            stack.append((node.left, remaining - node.left.val))
    return False


class Solution:
    def hasPathSum(self, root, targetSum: int) -> bool:
        return solve(root, targetSum)
