"""2236. Root Equals Sum of Children (Easy).

Specification: https://leetcode.com/problems/root-equals-sum-of-children/description/
"""


def solve(root) -> bool:
    """O(1) time and space; the problem supplies exactly a root and two children."""
    return root.val == root.left.val + root.right.val


class Solution:
    def checkTree(self, root) -> bool:
        return solve(root)
