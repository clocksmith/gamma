# External TreeNode shape: val: int, left: TreeNode | None, right: TreeNode | None.
class Solution:
    def maxDepth(self, root) -> int:
        if root is None:
            return 0

        queue = [root]
        head = 0
        depth = 0
        while head < len(queue):
            level_end = len(queue)
            depth += 1
            while head < level_end:
                node = queue[head]
                head += 1
                if node.left is not None:
                    queue.append(node.left)
                if node.right is not None:
                    queue.append(node.right)
        return depth
