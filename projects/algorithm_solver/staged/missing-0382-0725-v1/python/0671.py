"""671. Second Minimum Node In a Binary Tree."""

def solve(root):
    minimum = root.val
    answer = float('inf')
    stack = [root]
    while stack:
        node = stack.pop()
        if node.val > minimum:
            answer = min(answer, node.val)
        else:
            if node.left:
                stack.append(node.left)
            if node.right:
                stack.append(node.right)
    return -1 if answer == float('inf') else answer


class Solution:
    def findSecondMinimumValue(self, root):
        return solve(root)
