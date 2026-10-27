"""437. Path Sum III. Enter/leave DFS frames scope prefix sums to the current ancestor path."""

def solve(root, targetSum):
    counts = {0: 1}
    answer = 0
    stack = [(root, 0, False)] if root else []
    while stack:
        node, total, leaving = stack.pop()
        if leaving:
            counts[total] -= 1
            if counts[total] == 0:
                del counts[total]
            continue
        total += node.val
        answer += counts.get(total - targetSum, 0)
        counts[total] = counts.get(total, 0) + 1
        stack.append((node, total, True))
        if node.right:
            stack.append((node.right, total, False))
        if node.left:
            stack.append((node.left, total, False))
    return answer


class Solution:
    def pathSum(self, root, targetSum):
        return solve(root, targetSum)
