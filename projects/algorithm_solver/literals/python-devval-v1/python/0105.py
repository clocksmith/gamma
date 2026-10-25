class TreeNode:
    def __init__(self, value, left=None, right=None):
        self.val = value
        self.left = left
        self.right = right


def solve(preorder, inorder):
    if not preorder:
        return None
    root = TreeNode(preorder[0])
    stack = [root]
    inorder_index = 0
    for value in preorder[1:]:
        node = TreeNode(value)
        if stack[-1].val != inorder[inorder_index]:
            stack[-1].left = node
        else:
            previous = None
            while stack and stack[-1].val == inorder[inorder_index]:
                previous = stack.pop()
                inorder_index += 1
            previous.right = node
        stack.append(node)
    return root
