"""100. Same Tree (Easy).

Specification: https://leetcode.com/problems/same-tree/description/
"""


def solve(p, q) -> bool:
    """O(n) time, O(h) auxiliary space; compare shape and values without modifying either tree."""
    stack = [(p, q)]
    while stack:
        first, second = stack.pop()
        if first is None or second is None:
            if first is not second:
                return False
            continue
        if first.val != second.val:
            return False
        stack.append((first.right, second.right))
        stack.append((first.left, second.left))
    return True


class Solution:
    def isSameTree(self, p, q) -> bool:
        return solve(p, q)
