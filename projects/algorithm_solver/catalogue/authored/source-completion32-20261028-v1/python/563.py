# 563 — Binary Tree Tilt. Original implementation; authored candidate, not independently qualified.
def solve(root):
    sums, answer, stack = {}, 0, [(root, False)]
    while stack:
        node, visited = stack.pop()
        if node is None:
            continue
        if not visited:
            stack.extend(((node, True), (node.right, False), (node.left, False)))
        else:
            left, right = sums.get(id(node.left), 0), sums.get(id(node.right), 0)
            answer += abs(left - right)
            sums[id(node)] = node.val + left + right
    return answer

findTilt = solve

class Solution:
    findTilt = staticmethod(solve)
