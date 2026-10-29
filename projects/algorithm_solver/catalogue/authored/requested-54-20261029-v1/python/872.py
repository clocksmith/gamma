"""Original development candidate; independent qualification pending."""
def solve(root1, root2):
    def leaves(root):
        stack = [root]
        result = []
        while stack:
            node = stack.pop()
            if node.left is None and node.right is None:
                result.append(node.val)
            else:
                if node.right is not None:
                    stack.append(node.right)
                if node.left is not None:
                    stack.append(node.left)
        return result
    return leaves(root1) == leaves(root2)


class Solution:
    def leafSimilar(self, root1, root2):
        return solve(root1, root2)
