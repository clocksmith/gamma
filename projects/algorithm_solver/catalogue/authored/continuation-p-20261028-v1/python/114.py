class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def flatten(self, root):
        stack = [root] if root is not None else []
        previous = None
        while stack:
            current = stack.pop()
            if current.right is not None:
                stack.append(current.right)
            if current.left is not None:
                stack.append(current.left)
            if previous is not None:
                previous.left = None
                previous.right = current
            previous = current
        if previous is not None:
            previous.left = previous.right = None
