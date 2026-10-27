"""559. Maximum Depth of N-ary Tree."""

def solve(root):
    answer = 0
    stack = [(root, 1)] if root else []
    while stack:
        node, depth = stack.pop()
        answer = max(answer, depth)
        for child in node.children or []:
            stack.append((child, depth + 1))
    return answer


class Solution:
    def maxDepth(self, root):
        return solve(root)
