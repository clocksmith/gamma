"""Original LeetCode 590 candidate; qualification unknown."""

def solve(root):
    out, stack = [], [root] if root is not None else []
    while stack:
        node = stack.pop()
        out.append(node.val)
        stack.extend(node.children or [])
    out.reverse()
    return out


class Solution:
    def postorder(self, root):
        return solve(root)
