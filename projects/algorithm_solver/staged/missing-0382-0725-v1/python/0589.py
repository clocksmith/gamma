"""589. N-ary Tree Preorder Traversal."""

def solve(root):
    answer = []
    stack = [root] if root else []
    while stack:
        node = stack.pop()
        answer.append(node.val)
        stack.extend(reversed(node.children or []))
    return answer


class Solution:
    def preorder(self, root):
        return solve(root)
