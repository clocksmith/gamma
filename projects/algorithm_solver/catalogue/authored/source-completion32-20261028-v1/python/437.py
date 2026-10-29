# 437 — Path Sum III. Original implementation; authored candidate, not independently qualified.
def solve(root, targetSum):
    counts, answer = {0: 1}, 0
    stack = [(root, 0, False)]
    while stack:
        node, current, leaving = stack.pop()
        if node is None:
            continue
        if leaving:
            counts[current] -= 1
            continue
        current += node.val
        answer += counts.get(current - targetSum, 0)
        counts[current] = counts.get(current, 0) + 1
        stack.append((node, current, True))
        stack.append((node.right, current, False))
        stack.append((node.left, current, False))
    return answer

pathSum = solve

class Solution:
    pathSum = staticmethod(solve)
