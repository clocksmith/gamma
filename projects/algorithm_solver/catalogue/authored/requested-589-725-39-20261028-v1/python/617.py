"""Original LeetCode 617 candidate; qualification unknown."""

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



def solve(root1, root2):
    if root1 is None and root2 is None:
        return None
    result = TreeNode()
    stack = [(root1, root2, result)]
    while stack:
        a, b, out = stack.pop()
        out.val = (a.val if a is not None else 0) + (b.val if b is not None else 0)
        for side in ('left', 'right'):
            x = getattr(a, side) if a is not None else None
            y = getattr(b, side) if b is not None else None
            if x is not None or y is not None:
                child = TreeNode()
                setattr(out, side, child)
                stack.append((x, y, child))
    return result


class Solution:
    def mergeTrees(self, root1, root2):
        return solve(root1, root2)
