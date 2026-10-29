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



def solve(root,to_delete):
    copy=_clone(root);deleted=set(to_delete);out=[];stack=[(copy,None,None)]
    while stack:
        node,parent,side=stack.pop()
        remove=node.val in deleted
        if remove:
            if parent is not None:setattr(parent,side,None)
        elif parent is None:out.append(node)
        for label in ('left','right'):
            child=getattr(node,label)
            if child is not None:stack.append((child,None if remove else node,label))
    return out


class Solution:
    def delNodes(self, root, to_delete):
        return solve(root, to_delete)
