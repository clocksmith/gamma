class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def removeLeafNodes(self, root, target: int):
        if root is None:
            return None
        stack = [(root, False)]
        built = {None: None}
        while stack:
            node, expanded = stack.pop()
            if not expanded:
                stack.append((node, True))
                if node.right is not None:
                    stack.append((node.right, False))
                if node.left is not None:
                    stack.append((node.left, False))
            else:
                left = built[node.left]
                right = built[node.right]
                if left is None and right is None and node.val == target:
                    built[node] = None
                else:
                    built[node] = TreeNode(node.val, left, right)
        return built[root]
