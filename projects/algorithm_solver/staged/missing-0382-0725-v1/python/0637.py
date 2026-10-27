"""637. Average of Levels in Binary Tree."""

def solve(root):
    answer = []
    level = [root] if root else []
    while level:
        answer.append(sum(node.val for node in level) / len(level))
        following = []
        for node in level:
            if node.left:
                following.append(node.left)
            if node.right:
                following.append(node.right)
        level = following
    return answer


class Solution:
    def averageOfLevels(self, root):
        return solve(root)
