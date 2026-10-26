"""1373. Maximum Sum BST in Binary Tree.

Iterative postorder stores validity, extrema and sum for each subtree; O(n) time and space. The input tree is preserved.
"""

def solve(root) -> int:
    if root is None:
        return 0
    info = {}
    empty = (True, float('inf'), float('-inf'), 0)
    stack = [(root, False)]
    answer = 0
    while stack:
        node, finished = stack.pop()
        if not finished:
            stack.append((node, True))
            if node.right is not None:
                stack.append((node.right, False))
            if node.left is not None:
                stack.append((node.left, False))
            continue
        left = info.pop(id(node.left), empty)
        right = info.pop(id(node.right), empty)
        if left[0] and right[0] and left[2] < node.val < right[1]:
            total = left[3] + right[3] + node.val
            answer = max(answer, total)
            info[id(node)] = (True, min(left[1], node.val), max(right[2], node.val), total)
        else:
            info[id(node)] = (False, 0, 0, 0)
    return answer


class Solution:
    def maxSumBST(self, root) -> int:
        return solve(root)
