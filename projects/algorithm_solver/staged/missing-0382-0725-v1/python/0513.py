"""513. Find Bottom Left Tree Value."""

def solve(root):
    level = [root]
    answer = root.val
    while level:
        answer = level[0].val
        following = []
        for node in level:
            if node.left:
                following.append(node.left)
            if node.right:
                following.append(node.right)
        level = following
    return answer


class Solution:
    def findBottomLeftValue(self, root):
        return solve(root)
