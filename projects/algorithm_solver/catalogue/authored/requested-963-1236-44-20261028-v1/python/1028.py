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



def solve(traversal):
    stack=[];at=0
    while at<len(traversal):
        depth=0
        while traversal[at]=='-':depth+=1;at+=1
        end=at
        while end<len(traversal) and traversal[end].isdigit():end+=1
        node=TreeNode(int(traversal[at:end]));at=end
        while len(stack)>depth:stack.pop()
        if stack:
            if stack[-1].left is None:stack[-1].left=node
            else:stack[-1].right=node
        stack.append(node)
    return stack[0]


class Solution:
    def recoverFromPreorder(self, traversal):
        return solve(traversal)
