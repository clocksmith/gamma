# External TreeNode shape: val: int, left: TreeNode | None, right: TreeNode | None.
class Solution:
    def hasPathSum(self, root: "TreeNode | None", targetSum: int) -> bool:
        if root is None:
            return False

        stack = [(root, root.val)]
        while stack:
            node, total = stack.pop()
            if node.left is None and node.right is None:
                if total == targetSum:
                    return True
            if node.right is not None:
                stack.append((node.right, total + node.right.val))
            if node.left is not None:
                stack.append((node.left, total + node.left.val))
        return False
