# External TreeNode shape: val: int, left: TreeNode | None, right: TreeNode | None.
class Solution:
    def maxPathSum(self, root: "TreeNode | None") -> int:
        if root is None:
            return 0

        best = root.val
        stack = [(root, False)]
        gains = []
        while stack:
            node, expanded = stack.pop()
            if not expanded:
                stack.append((node, True))
                if node.right is not None:
                    stack.append((node.right, False))
                if node.left is not None:
                    stack.append((node.left, False))
                continue

            right_gain = gains.pop() if node.right is not None else 0
            left_gain = gains.pop() if node.left is not None else 0
            best = max(best, node.val + left_gain + right_gain)
            gains.append(max(0, node.val + max(left_gain, right_gain)))
        return best
