"""515. Find Largest Value in Each Tree Row."""

def solve(root):
    answer = []
    level = [root] if root else []
    while level:
        answer.append(max(node.val for node in level))
        following = []
        for node in level:
            if node.left:
                following.append(node.left)
            if node.right:
                following.append(node.right)
        level = following
    return answer


class Solution:
    def largestValues(self, root):
        return solve(root)
