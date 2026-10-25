# External TreeNode shape: val: int, left: TreeNode | None, right: TreeNode | None.
class Solution:
    def minDepth(self, root: "TreeNode | None") -> int:
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
                if node.left is None and node.right is None:
                    return depth
                if node.left is not None:
                    queue.append(node.left)
                if node.right is not None:
                    queue.append(node.right)
        return depth
