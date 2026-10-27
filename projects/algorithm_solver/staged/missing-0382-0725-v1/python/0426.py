"""426. Convert Binary Search Tree to Sorted Doubly Linked List. Relink the original nodes in place into a circular list; no replacement nodes."""

def solve(root):
    if root is None:
        return None
    stack = []
    node = root
    first = previous = None
    while stack or node is not None:
        while node is not None:
            stack.append(node)
            node = node.left
        node = stack.pop()
        right = node.right
        node.left = previous
        if previous is None:
            first = node
        else:
            previous.right = node
        previous = node
        node = right
    first.left = previous
    previous.right = first
    return first


class Solution:
    def treeToDoublyList(self, root):
        return solve(root)
