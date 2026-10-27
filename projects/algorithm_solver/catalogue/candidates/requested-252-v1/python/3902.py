"""3902. Zigzag Level Sum of Binary Tree.

Specification: https://leetcode.com/problems/zigzag-level-sum-of-binary-tree/description/
"""

from __future__ import annotations


def solve(root: TreeNode | None) -> list[int]:
    """O(n) time and O(width) auxiliary space; all nodes still supply the next level after a summation stop. Inputs are preserved."""
    if root is None:
        return []
    level = [root]
    odd = True
    answer = []
    while level:
        total = 0
        ordered = iter(level) if odd else reversed(level)
        for node in ordered:
            if (node.left if odd else node.right) is None:
                break
            total += node.val
        answer.append(total)
        following = []
        for node in level:
            if node.left is not None:
                following.append(node.left)
            if node.right is not None:
                following.append(node.right)
        level = following
        odd = not odd
    return answer
