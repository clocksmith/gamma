# 404 — Sum of Left Leaves. Original implementation; authored candidate, not independently qualified.
def solve(root):
    total, stack = 0, [(root, False)]
    while stack:
        node, is_left = stack.pop()
        if node is None:
            continue
        if node.left is None and node.right is None and is_left:
            total += node.val
        stack.append((node.right, False))
        stack.append((node.left, True))
    return total

sumOfLeftLeaves = solve

class Solution:
    sumOfLeftLeaves = staticmethod(solve)
