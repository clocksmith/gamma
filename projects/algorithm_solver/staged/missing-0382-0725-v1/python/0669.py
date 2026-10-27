"""669. Trim a Binary Search Tree. Trim original links in place while preserving the surviving nodes and their relative structure."""

def solve(root, low, high):
    while root and (root.val < low or root.val > high):
        root = root.right if root.val < low else root.left
    if root is None:
        return None
    node = root
    while node:
        while node.left and node.left.val < low:
            node.left = node.left.right
        node = node.left
    node = root
    while node:
        while node.right and node.right.val > high:
            node.right = node.right.left
        node = node.right
    return root


class Solution:
    def trimBST(self, root, low, high):
        return solve(root, low, high)
