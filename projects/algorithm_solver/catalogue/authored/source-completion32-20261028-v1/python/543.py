# 543 — Diameter of Binary Tree. Original implementation; authored candidate, not independently qualified.
def solve(root):
    heights, answer, stack = {}, 0, [(root, False)]
    while stack:
        node, visited = stack.pop()
        if node is None:
            continue
        if not visited:
            stack.extend(((node, True), (node.right, False), (node.left, False)))
        else:
            left, right = heights.get(id(node.left), 0), heights.get(id(node.right), 0)
            answer = max(answer, left + right)
            heights[id(node)] = 1 + max(left, right)
    return answer

diameterOfBinaryTree = solve

class Solution:
    diameterOfBinaryTree = staticmethod(solve)
