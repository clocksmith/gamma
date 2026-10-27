"""687. Longest Univalue Path. Postorder chain lengths are measured in edges, not nodes."""

def solve(root):
    chains = {}
    answer = 0
    stack = [(root, False)] if root else []
    while stack:
        node, ready = stack.pop()
        if not ready:
            stack.append((node, True))
            if node.right:
                stack.append((node.right, False))
            if node.left:
                stack.append((node.left, False))
        else:
            left = chains[id(node.left)] + 1 if node.left and node.left.val == node.val else 0
            right = chains[id(node.right)] + 1 if node.right and node.right.val == node.val else 0
            chains[id(node)] = max(left, right)
            answer = max(answer, left + right)
    return answer


class Solution:
    def longestUnivaluePath(self, root):
        return solve(root)
