# 530 — Minimum Absolute Difference in BST. Original implementation; authored candidate, not independently qualified.
def solve(root):
    stack, current, previous, answer = [], root, None, float('inf')
    while stack or current is not None:
        while current is not None:
            stack.append(current)
            current = current.left
        current = stack.pop()
        if previous is not None:
            answer = min(answer, current.val - previous)
        previous, current = current.val, current.right
    return answer

getMinimumDifference = solve

class Solution:
    getMinimumDifference = staticmethod(solve)
