# 450 — Delete Node in a BST. Original implementation; authored candidate, not independently qualified.
def solve(root, key):
    parent, current = None, root
    while current is not None and current.val != key:
        parent = current
        current = current.left if key < current.val else current.right
    if current is None:
        return root
    if current.left is not None and current.right is not None:
        parent, successor = current, current.right
        while successor.left is not None:
            parent, successor = successor, successor.left
        current.val = successor.val
        current = successor
    child = current.left if current.left is not None else current.right
    if parent is None:
        return child
    if parent.left is current:
        parent.left = child
    else:
        parent.right = child
    return root

deleteNode = solve

class Solution:
    deleteNode = staticmethod(solve)
