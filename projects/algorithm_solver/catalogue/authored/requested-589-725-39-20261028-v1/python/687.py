"""Original LeetCode 687 candidate; qualification unknown."""

def solve(root):
    if root is None: return 0
    down, answer, stack = {}, 0, [(root, False)]
    while stack:
        node, visited = stack.pop()
        if node is None: continue
        if not visited:
            stack.extend([(node, True), (node.right, False), (node.left, False)])
            continue
        left = down[id(node.left)] + 1 if node.left is not None and node.left.val == node.val else 0
        right = down[id(node.right)] + 1 if node.right is not None and node.right.val == node.val else 0
        answer = max(answer, left + right)
        down[id(node)] = max(left, right)
    return answer


class Solution:
    def longestUnivaluePath(self, root):
        return solve(root)
