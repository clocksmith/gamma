"""590. N-ary Tree Postorder Traversal."""

def solve(root):
    answer = []
    stack = [root] if root else []
    while stack:
        node = stack.pop()
        answer.append(node.val)
        stack.extend(node.children or [])
    answer.reverse()
    return answer


class Solution:
    def postorder(self, root):
        return solve(root)
