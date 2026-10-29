"""Original LeetCode 637 candidate; qualification unknown."""

def solve(root):
    level, out = [root], []
    while level:
        out.append(sum(node.val for node in level) / len(level))
        level = [child for node in level for child in (node.left, node.right) if child is not None]
    return out


class Solution:
    def averageOfLevels(self, root):
        return solve(root)
