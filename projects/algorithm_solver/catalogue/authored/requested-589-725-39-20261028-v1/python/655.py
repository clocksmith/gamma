"""Original LeetCode 655 candidate; qualification unknown."""

def solve(root):
    stack, height = [(root, 1)], 0
    while stack:
        node, depth = stack.pop(); height = max(height, depth)
        if node.left is not None: stack.append((node.left, depth + 1))
        if node.right is not None: stack.append((node.right, depth + 1))
    width = 2**height - 1
    out = [[''] * width for _ in range(height)]
    stack = [(root, 0, 0, width - 1)]
    while stack:
        node, depth, left, right = stack.pop(); middle = (left + right) // 2
        out[depth][middle] = str(node.val)
        if node.left is not None: stack.append((node.left, depth + 1, left, middle - 1))
        if node.right is not None: stack.append((node.right, depth + 1, middle + 1, right))
    return out


class Solution:
    def printTree(self, root):
        return solve(root)
