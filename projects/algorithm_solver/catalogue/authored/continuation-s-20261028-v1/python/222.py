class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def countNodes(self, root):
        if root is None:
            return 0
        def height(node):
            result = 0
            while node is not None:
                result += 1
                node = node.left
            return result
        left, right = height(root.left), height(root.right)
        if left == right:
            return (1 << left) + self.countNodes(root.right)
        return (1 << right) + self.countNodes(root.left)
