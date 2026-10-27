"""606. Construct String from Binary Tree. Iterative preorder emits the empty left pair only when needed to preserve structure."""

def solve(root):
    if root is None:
        return ''
    parts = []
    stack = [root]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            parts.append(item)
            continue
        parts.append(str(item.val))
        if item.right is not None:
            stack.extend([')', item.right, '('])
        if item.left is not None or item.right is not None:
            stack.append(')')
            if item.left is not None:
                stack.append(item.left)
            stack.append('(')
    return ''.join(parts)


class Solution:
    def tree2str(self, root):
        return solve(root)
