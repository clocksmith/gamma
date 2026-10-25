# External TreeNode fields: val, left, right; absent children are None.
class Solution:
    def btreeGameWinningMove(self, root, n: int, x: int) -> bool:
        sizes = {}
        stack = [(root, False)]
        left_size = 0
        right_size = 0
        while stack:
            node, expanded = stack.pop()
            if not expanded:
                stack.append((node, True))
                if node.right is not None:
                    stack.append((node.right, False))
                if node.left is not None:
                    stack.append((node.left, False))
            else:
                left = 0 if node.left is None else sizes[id(node.left)]
                right = 0 if node.right is None else sizes[id(node.right)]
                sizes[id(node)] = left + right + 1
                if node.val == x:
                    left_size = left
                    right_size = right
        parent_size = n - left_size - right_size - 1
        return max(left_size, right_size, parent_size) * 2 > n
