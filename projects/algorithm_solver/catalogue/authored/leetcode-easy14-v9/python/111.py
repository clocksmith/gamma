"""111. Minimum Depth of Binary Tree (Easy).

Specification: https://leetcode.com/problems/minimum-depth-of-binary-tree/description/
"""


def solve(root) -> int:
    """O(n) time, O(w) space; visit complete levels until the first leaf and preserve the tree."""
    if root is None:
        return 0
    level = [root]
    depth = 1
    while level:
        next_level = []
        for node in level:
            if node.left is None and node.right is None:
                return depth
            if node.left is not None:
                next_level.append(node.left)
            if node.right is not None:
                next_level.append(node.right)
        level = next_level
        depth += 1
    return 0


class Solution:
    def minDepth(self, root) -> int:
        return solve(root)
