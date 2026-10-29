# 513 — Find Bottom Left Tree Value. Original implementation; authored candidate, not independently qualified.
def solve(root):
    from collections import deque
    queue = deque([root])
    answer = root.val
    while queue:
        answer = queue[0].val
        for _ in range(len(queue)):
            node = queue.popleft()
            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)
    return answer

findBottomLeftValue = solve

class Solution:
    findBottomLeftValue = staticmethod(solve)
