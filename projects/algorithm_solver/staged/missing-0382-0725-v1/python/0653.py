"""653. Two Sum IV - Input is a BST."""

def solve(root, k):
    seen = set()
    stack = [root] if root else []
    while stack:
        node = stack.pop()
        if k - node.val in seen:
            return True
        seen.add(node.val)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return False


class Solution:
    def findTarget(self, root, k):
        return solve(root, k)
