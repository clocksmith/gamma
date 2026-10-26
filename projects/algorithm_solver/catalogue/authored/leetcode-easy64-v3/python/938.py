"""938. Range Sum of BST (Easy).

Specification: https://leetcode.com/problems/range-sum-of-bst/description/
"""


def solve(root, low: int, high: int) -> int:
    """O(n) worst-case time, O(h) auxiliary space; preserve the supplied tree."""
    stack = [root]
    total = 0
    while stack:
        node = stack.pop()
        if node is None:
            continue
        if low <= node.val <= high:
            total += node.val
        if node.val > low and node.left is not None:
            stack.append(node.left)
        if node.val < high and node.right is not None:
            stack.append(node.right)
    return total


class Solution:
    def rangeSumBST(self, root, low: int, high: int) -> int:
        return solve(root, low, high)
