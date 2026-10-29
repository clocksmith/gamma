"""Original LeetCode 589 candidate; qualification unknown."""

def solve(root):
    out, stack = [], [root] if root is not None else []
    while stack:
        node = stack.pop()
        out.append(node.val)
        stack.extend(reversed(node.children or []))
    return out


class Solution:
    def preorder(self, root):
        return solve(root)
