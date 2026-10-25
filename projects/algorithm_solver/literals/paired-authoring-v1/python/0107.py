# External TreeNode shape: val: int, left: TreeNode | None, right: TreeNode | None.
class Solution:
    def levelOrderBottom(self, root) -> list[list[int]]:
        if root is None:
            return []

        queue = [root]
        head = 0
        levels = []
        while head < len(queue):
            level_end = len(queue)
            level = []
            while head < level_end:
                node = queue[head]
                head += 1
                level.append(node.val)
                if node.left is not None:
                    queue.append(node.left)
                if node.right is not None:
                    queue.append(node.right)
            levels.append(level)
        levels.reverse()
        return levels
