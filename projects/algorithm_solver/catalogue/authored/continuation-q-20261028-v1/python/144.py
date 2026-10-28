"""Original frontend 144 source-defined native ABI; qualification unknown."""

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root):
    answer = []
    pending = [root] if root is not None else []
    while pending:
        node = pending.pop()
        answer.append(node.val)
        if node.right is not None:
            pending.append(node.right)
        if node.left is not None:
            pending.append(node.left)
    return answer


class Solution:
    def preorderTraversal(self, root):
        return solve(root)
