class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def recoverTree(self, root):
        stack = []
        current = root
        previous = first = second = None
        while stack or current is not None:
            while current is not None:
                stack.append(current)
                current = current.left
            current = stack.pop()
            if previous is not None and previous.val > current.val:
                if first is None:
                    first = previous
                second = current
            previous = current
            current = current.right
        first.val, second.val = second.val, first.val
