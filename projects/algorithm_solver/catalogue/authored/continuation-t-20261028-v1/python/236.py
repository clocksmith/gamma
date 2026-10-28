class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None


class Solution:
    def lowestCommonAncestor(self, root, p, q):
        parent = {root: None}
        stack = [root]
        while p not in parent or q not in parent:
            node = stack.pop()
            for child in (node.left, node.right):
                if child is not None:
                    parent[child] = node
                    stack.append(child)
        ancestors = set()
        node = p
        while node is not None:
            ancestors.add(node)
            node = parent[node]
        node = q
        while node not in ancestors:
            node = parent[node]
        return node
