"""510. Inorder Successor in BST II. Use original parent links and return an existing node, not a copy."""

def solve(node):
    if node.right:
        node = node.right
        while node.left:
            node = node.left
        return node
    while node.parent and node.parent.right is node:
        node = node.parent
    return node.parent


class Solution:
    def inorderSuccessor(self, node):
        return solve(node)
