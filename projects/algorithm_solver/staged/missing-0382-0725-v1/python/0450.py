"""450. Delete Node in a BST. Update the supplied BST in place; copy a successor value only for a two-child deletion."""

def solve(root, key):
    parent = None
    node = root
    while node is not None and node.val != key:
        parent = node
        node = node.left if key < node.val else node.right
    if node is None:
        return root
    if node.left is not None and node.right is not None:
        successor_parent = node
        successor = node.right
        while successor.left is not None:
            successor_parent = successor
            successor = successor.left
        node.val = successor.val
        parent, node = successor_parent, successor
    child = node.left if node.left is not None else node.right
    if parent is None:
        return child
    if parent.left is node:
        parent.left = child
    else:
        parent.right = child
    return root


class Solution:
    def deleteNode(self, root, key):
        return solve(root, key)
