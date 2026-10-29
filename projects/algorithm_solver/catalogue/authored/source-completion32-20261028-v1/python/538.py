# 538 — Convert BST to Greater Tree. Original implementation; authored candidate, not independently qualified.
def solve(root):
    stack, current, total = [], root, 0
    while stack or current is not None:
        while current is not None:
            stack.append(current)
            current = current.right
        current = stack.pop()
        total += current.val
        current.val = total
        current = current.left
    return root

convertBST = solve

class Solution:
    convertBST = staticmethod(solve)
