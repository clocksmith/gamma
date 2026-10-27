"""429. N-ary Tree Level Order Traversal. Breadth-first traversal; preserves the input tree."""

def solve(root):
    answer = []
    level = [root] if root else []
    while level:
        answer.append([node.val for node in level])
        level = [child for node in level for child in (node.children or [])]
    return answer


class Solution:
    def levelOrder(self, root):
        return solve(root)
