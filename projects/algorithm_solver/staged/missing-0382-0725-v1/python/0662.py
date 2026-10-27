"""662. Maximum Width of Binary Tree. Normalize complete-tree positions at each level to avoid depth-driven integer growth."""

def solve(root):
    answer = 0
    level = [(root, 0)] if root else []
    while level:
        answer = max(answer, level[-1][1] - level[0][1] + 1)
        offset = level[0][1]
        following = []
        for node, index in level:
            index -= offset
            if node.left:
                following.append((node.left, 2 * index))
            if node.right:
                following.append((node.right, 2 * index + 1))
        level = following
    return answer


class Solution:
    def widthOfBinaryTree(self, root):
        return solve(root)
