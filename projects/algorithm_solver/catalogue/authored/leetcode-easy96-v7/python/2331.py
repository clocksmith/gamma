"""2331. Evaluate Boolean Binary Tree (Easy).

Specification: https://leetcode.com/problems/evaluate-boolean-binary-tree/description/
"""


def solve(root: 'TreeNode') -> bool:
    """O(n) time, O(h) auxiliary space; iterative postorder on supplied val/left/right nodes; no tree mutation."""
    pending = [(root, False)]
    values = []
    while pending:
        node, expanded = pending.pop()
        if node.val == 0 or node.val == 1:
            values.append(node.val == 1)
        elif expanded:
            right = values.pop()
            left = values.pop()
            values.append(left or right if node.val == 2 else left and right)
        else:
            pending.append((node, True))
            pending.append((node.right, False))
            pending.append((node.left, False))
    return values[0]


class Solution:
    def evaluateTree(self, root: 'TreeNode') -> bool:
        return solve(root)
