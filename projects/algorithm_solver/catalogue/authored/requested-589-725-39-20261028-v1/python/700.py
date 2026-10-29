"""Original LeetCode 700 candidate; qualification unknown."""

def solve(root, val):
    node = root
    while node is not None and node.val != val:
        node = node.left if val < node.val else node.right
    return node


class Solution:
    def searchBST(self, root, val):
        return solve(root, val)
