"""Original LeetCode 701 candidate; qualification unknown."""

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



def solve(root, val):
    result = _clone(root)
    if result is None: return TreeNode(val)
    node = result
    while True:
        side = 'left' if val < node.val else 'right'
        child = getattr(node, side)
        if child is None:
            setattr(node, side, TreeNode(val))
            return result
        node = child


class Solution:
    def insertIntoBST(self, root, val):
        return solve(root, val)
