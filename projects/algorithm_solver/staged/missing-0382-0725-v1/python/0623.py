"""623. Add One Row to Tree. Insert the requested row in place while retaining all original descendant nodes."""

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root, val, depth):
    if depth == 1:
        return TreeNode(val, root, None)
    level = [root] if root else []
    for _ in range(1, depth - 1):
        following = []
        for node in level:
            if node.left:
                following.append(node.left)
            if node.right:
                following.append(node.right)
        level = following
    for node in level:
        node.left = TreeNode(val, node.left, None)
        node.right = TreeNode(val, None, node.right)
    return root


class Solution:
    def addOneRow(self, root, val, depth):
        return solve(root, val, depth)
