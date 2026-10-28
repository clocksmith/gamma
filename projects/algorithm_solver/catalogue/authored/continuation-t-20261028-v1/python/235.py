class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None


class Solution:
    def lowestCommonAncestor(self, root, p, q):
        low, high = min(p.val, q.val), max(p.val, q.val)
        while root is not None:
            if root.val < low:
                root = root.right
            elif root.val > high:
                root = root.left
            else:
                return root
