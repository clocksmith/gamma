"""700. Search in a Binary Search Tree. Return the original matching subtree without copying or mutation."""

def solve(root, val):
    while root and root.val != val:
        root = root.left if val < root.val else root.right
    return root


class Solution:
    def searchBST(self, root, val):
        return solve(root, val)
