"""Original frontend 129 source-defined native ABI; qualification unknown."""

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root):
    if root is None:
        return 0
    pending = [(root, 0)]
    total = 0
    while pending:
        node, prefix = pending.pop()
        value = prefix * 10 + node.val
        if node.left is None and node.right is None:
            total += value
        else:
            if node.right is not None:
                pending.append((node.right, value))
            if node.left is not None:
                pending.append((node.left, value))
    return total


class Solution:
    def sumNumbers(self, root):
        return solve(root)
