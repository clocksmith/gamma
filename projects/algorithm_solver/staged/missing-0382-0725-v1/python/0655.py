"""655. Print Binary Tree."""

def solve(root):
    if root is None:
        return []
    height = 0
    stack = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        height = max(height, depth)
        if node.left:
            stack.append((node.left, depth + 1))
        if node.right:
            stack.append((node.right, depth + 1))
    width = (1 << height) - 1
    answer = [[''] * width for _ in range(height)]
    stack = [(root, 0, 0, width - 1)]
    while stack:
        node, row, left, right = stack.pop()
        middle = (left + right) // 2
        answer[row][middle] = str(node.val)
        if node.right:
            stack.append((node.right, row + 1, middle + 1, right))
        if node.left:
            stack.append((node.left, row + 1, left, middle - 1))
    return answer


class Solution:
    def printTree(self, root):
        return solve(root)
