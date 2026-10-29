# 501 — Find Mode in Binary Search Tree. Original implementation; authored candidate, not independently qualified.
def solve(root):
    stack, current = [], root
    previous, run, maximum, result = None, 0, 0, []
    while stack or current is not None:
        while current is not None:
            stack.append(current)
            current = current.left
        current = stack.pop()
        run = run + 1 if current.val == previous else 1
        previous = current.val
        if run > maximum:
            maximum, result = run, [current.val]
        elif run == maximum:
            result.append(current.val)
        current = current.right
    return result

findMode = solve

class Solution:
    findMode = staticmethod(solve)
