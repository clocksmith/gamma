# External TreeNode shape: val: int, left: TreeNode | None, right: TreeNode | None.
class Solution:
    def increasingBST(self, root: "TreeNode | None") -> "TreeNode | None":
        stack = []
        current = root
        head = None
        tail = None
        while current is not None or stack:
            while current is not None:
                stack.append(current)
                current = current.left
            node = stack.pop()
            current = node.right
            node.left = None
            if tail is None:
                head = node
            else:
                tail.right = node
            tail = node
        if tail is not None:
            tail.right = None
        return head
