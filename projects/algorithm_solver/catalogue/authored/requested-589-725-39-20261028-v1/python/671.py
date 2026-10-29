"""Original LeetCode 671 candidate; qualification unknown."""

def solve(root):
    minimum, second, stack = root.val, None, [root]
    while stack:
        node = stack.pop()
        if node.val > minimum and (second is None or node.val < second): second = node.val
        if node.left is not None: stack.append(node.left)
        if node.right is not None: stack.append(node.right)
    return -1 if second is None else second


class Solution:
    def findSecondMinimumValue(self, root):
        return solve(root)
