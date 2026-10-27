"""404. Sum of Left Leaves. Iterative traversal; preserves node identities and links."""

def solve(root):
    answer = 0
    stack = [(root, False)] if root else []
    while stack:
        node, is_left = stack.pop()
        if node.left is None and node.right is None and is_left:
            answer += node.val
        if node.right:
            stack.append((node.right, False))
        if node.left:
            stack.append((node.left, True))
    return answer


class Solution:
    def sumOfLeftLeaves(self, root):
        return solve(root)
