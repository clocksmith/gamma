class TreeNode:
    def __init__(self, val: int, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def buildTree(self, inorder: list[int], postorder: list[int]) -> "TreeNode | None":
        if not postorder:
            return None
        root = TreeNode(postorder[-1])
        stack = [root]
        inorder_index = len(inorder) - 1
        for index in range(len(postorder) - 2, -1, -1):
            child = TreeNode(postorder[index])
            if stack[-1].val != inorder[inorder_index]:
                stack[-1].right = child
            else:
                parent = None
                while stack and stack[-1].val == inorder[inorder_index]:
                    parent = stack.pop()
                    inorder_index -= 1
                parent.left = child
            stack.append(child)
        return root
