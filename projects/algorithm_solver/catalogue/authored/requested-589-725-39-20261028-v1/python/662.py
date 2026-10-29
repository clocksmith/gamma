"""Original LeetCode 662 candidate; qualification unknown."""

def solve(root):
    level, answer = [(root, 0)], 0
    while level:
        base = level[0][1]
        answer = max(answer, level[-1][1] - base + 1)
        next_level = []
        for node, position in level:
            position -= base
            if node.left is not None: next_level.append((node.left, 2 * position))
            if node.right is not None: next_level.append((node.right, 2 * position + 1))
        level = next_level
    return answer


class Solution:
    def widthOfBinaryTree(self, root):
        return solve(root)
