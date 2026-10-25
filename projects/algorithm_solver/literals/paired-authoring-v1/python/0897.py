class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def increasingBST(self, root):
        stack = []
        current = root
        head = None
        tail = None
        while current is not None or stack:
            while current is not None:
                stack.append(current)
                current = current.left
            original = stack.pop()
            node = TreeNode(original.val)
            if tail is None:
                head = node
            else:
                tail.right = node
            tail = node
            current = original.right
        return head
