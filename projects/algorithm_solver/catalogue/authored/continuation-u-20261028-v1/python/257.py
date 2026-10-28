class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def binaryTreePaths(self, root):
        if root is None:
            return []
        stack = [(root, False)]
        path = []
        result = []
        while stack:
            node, leaving = stack.pop()
            if leaving:
                path.pop()
                continue
            path.append(str(node.val))
            stack.append((node, True))
            if node.left is None and node.right is None:
                result.append('->'.join(path))
            else:
                if node.right is not None:
                    stack.append((node.right, False))
                if node.left is not None:
                    stack.append((node.left, False))
        return result
