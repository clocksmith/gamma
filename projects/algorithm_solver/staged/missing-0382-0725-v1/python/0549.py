"""549. Binary Tree Longest Consecutive Sequence II. Combine increasing and decreasing child paths in iterative postorder."""

def solve(root):
    answer = 0
    lengths = {}
    stack = [(root, False)] if root else []
    while stack:
        node, ready = stack.pop()
        if not ready:
            stack.append((node, True))
            if node.right:
                stack.append((node.right, False))
            if node.left:
                stack.append((node.left, False))
            continue
        increasing = decreasing = 1
        for child in (node.left, node.right):
            if child:
                inc, dec = lengths[id(child)]
                if child.val == node.val + 1:
                    increasing = max(increasing, inc + 1)
                if child.val == node.val - 1:
                    decreasing = max(decreasing, dec + 1)
        lengths[id(node)] = (increasing, decreasing)
        answer = max(answer, increasing + decreasing - 1)
    return answer


class Solution:
    def longestConsecutive(self, root):
        return solve(root)
