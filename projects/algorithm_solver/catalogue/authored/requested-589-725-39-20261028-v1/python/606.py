"""Original LeetCode 606 candidate; qualification unknown."""

def solve(root):
    out, stack = [], [root]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            out.append(item)
            continue
        out.append(str(item.val))
        if item.right is not None:
            stack.extend([')', item.right, '('])
        if item.left is not None or item.right is not None:
            stack.append(')')
            if item.left is not None:
                stack.append(item.left)
            stack.append('(')
    return ''.join(out)


class Solution:
    def tree2str(self, root):
        return solve(root)
