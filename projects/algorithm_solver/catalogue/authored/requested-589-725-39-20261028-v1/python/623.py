"""Original LeetCode 623 candidate; qualification unknown."""

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right


def _clone(root):
    if root is None:
        return None
    result = TreeNode(root.val)
    stack = [(root, result)]
    while stack:
        old, new = stack.pop()
        for side in ('left', 'right'):
            child = getattr(old, side)
            if child is not None:
                copy = TreeNode(child.val)
                setattr(new, side, copy)
                stack.append((child, copy))
    return result



def solve(root, val, depth):
    copy = _clone(root)
    if depth == 1:
        return TreeNode(val, copy)
    level = [copy]
    for _ in range(depth - 2):
        level = [child for node in level for child in (node.left, node.right) if child is not None]
    for node in level:
        node.left = TreeNode(val, node.left)
        node.right = TreeNode(val, None, node.right)
    return copy


class Solution:
    def addOneRow(self, root, val, depth):
        return solve(root, val, depth)
