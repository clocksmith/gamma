# 515 — Find Largest Value in Each Tree Row. Original implementation; authored candidate, not independently qualified.
def solve(root):
    if root is None:
        return []
    level, result = [root], []
    while level:
        result.append(max(node.val for node in level))
        level = [child for node in level for child in (node.left, node.right) if child is not None]
    return result

largestValues = solve

class Solution:
    largestValues = staticmethod(solve)
