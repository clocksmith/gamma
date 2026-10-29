"""Original LeetCode 653 candidate; qualification unknown."""

def solve(root, k):
    seen, stack = set(), [root]
    while stack:
        node = stack.pop()
        if k - node.val in seen: return True
        seen.add(node.val)
        if node.left is not None: stack.append(node.left)
        if node.right is not None: stack.append(node.right)
    return False


class Solution:
    def findTarget(self, root, k):
        return solve(root, k)
