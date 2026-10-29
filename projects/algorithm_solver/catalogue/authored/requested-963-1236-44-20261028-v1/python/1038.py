"""Original candidate; no qualification or admission."""

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



def solve(root):
    out=_clone(root);node=out;stack=[];total=0
    while node is not None or stack:
        while node is not None:stack.append(node);node=node.right
        node=stack.pop();total+=node.val;node.val=total;node=node.left
    return out


class Solution:
    def bstToGst(self, root):
        return solve(root)
