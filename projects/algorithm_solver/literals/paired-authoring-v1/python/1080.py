# External TreeNode fields: val, left, right; absent children are None.
class Solution:
    def sufficientSubset(self, root: "TreeNode | None", limit: int) -> "TreeNode | None":
        if root is None:
            return None
        stack = [(root, None, False, root.val, False, False)]
        while stack:
            node, parent, is_left, total, expanded, original_leaf = stack.pop()
            if not expanded:
                original_leaf = node.left is None and node.right is None
                stack.append((node, parent, is_left, total, True, original_leaf))
                if node.right is not None:
                    stack.append((node.right, node, False, total + node.right.val, False, False))
                if node.left is not None:
                    stack.append((node.left, node, True, total + node.left.val, False, False))
            else:
                insufficient = total < limit if original_leaf else node.left is None and node.right is None
                if insufficient:
                    if parent is None:
                        root = None
                    elif is_left:
                        parent.left = None
                    else:
                        parent.right = None
        return root
