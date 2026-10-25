# External TreeNode shape: val: int, left: TreeNode | None, right: TreeNode | None.
class Solution:
    def removeLeafNodes(self, root, target: int):
        if root is None:
            return None
        stack = [(root, False)]
        while stack:
            node, expanded = stack.pop()
            if not expanded:
                stack.append((node, True))
                if node.right is not None:
                    stack.append((node.right, False))
                if node.left is not None:
                    stack.append((node.left, False))
            else:
                left = node.left
                right = node.right
                if left is not None and left.val == target:
                    if left.left is None and left.right is None:
                        node.left = None
                if right is not None and right.val == target:
                    if right.left is None and right.right is None:
                        node.right = None
        if root.val == target and root.left is None and root.right is None:
            return None
        return root
