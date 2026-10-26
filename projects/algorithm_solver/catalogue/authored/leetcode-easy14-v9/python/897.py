"""897. Increasing Order Search Tree (Easy).

Specification: https://leetcode.com/problems/increasing-order-search-tree/description/
"""


def solve(root):
    """O(n) time, O(h) space; rewire the original nodes into an increasing right-only chain."""
    stack = []
    current = root
    head = None
    tail = None
    while current is not None or stack:
        while current is not None:
            stack.append(current)
            current = current.left
        current = stack.pop()
        next_root = current.right
        current.left = None
        if tail is None:
            head = current
        else:
            tail.right = current
        tail = current
        current = next_root
    if tail is not None:
        tail.right = None
    return head


class Solution:
    def increasingBST(self, root):
        return solve(root)
