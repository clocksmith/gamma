"""3997. Count Dominant Nodes in a Binary Tree
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-dominant-nodes-in-a-binary-tree/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3997.Count%20Dominant%20Nodes%20in%20a%20Binary%20Tree/README_EN.md
Complexity: O(n) time, O(log n) stack on the guaranteed complete binary tree.
Native TreeNode objects with val/left/right; input tree is preserved. Equal maxima count as dominant; no array transport is inferred.
"""

from __future__ import annotations

def solve(root):
    def visit(node):
        if node is None:
            return float('-inf'), 0
        left, lc = visit(node.left)
        right, rc = visit(node.right)
        maximum = max(node.val, left, right)
        return maximum, lc + rc + int(node.val == maximum)
    return visit(root)[1]


class Solution:
    def countDominantNodes(self, root):
        return solve(root)
