# External TreeNode shape: val: int, left: TreeNode | None, right: TreeNode | None.
class Solution:
    def zigzagLevelOrder(self, root) -> list[list[int]]:
        if root is None:
            return []

        queue = [root]
        head = 0
        levels = []
        reverse_level = False
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
            if reverse_level:
                level.reverse()
            levels.append(level)
            reverse_level = not reverse_level
        return levels
