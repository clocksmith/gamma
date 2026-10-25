"""2792. Count Nodes That Are Great Enough."""

from bisect import bisect_left


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(root: TreeNode | None, k: int) -> int:
    """Iterative postorder with sorted k-smallest summaries: O(n*k) time, O(n+k) space."""
    if root is None:
        return 0
    stack = [(root, False)]
    smallest = {}
    answer = 0
    while stack:
        node, ready = stack.pop()
        if not ready:
            stack.append((node, True))
            if node.right is not None:
                stack.append((node.right, False))
            if node.left is not None:
                stack.append((node.left, False))
            continue
        left = smallest.pop(id(node.left), [])
        right = smallest.pop(id(node.right), [])
        merged = []
        first = second = 0
        while len(merged) < k and (first < len(left) or second < len(right)):
            if second == len(right) or first < len(left) and left[first] <= right[second]:
                merged.append(left[first])
                first += 1
            else:
                merged.append(right[second])
                second += 1
        if len(merged) == k and merged[-1] < node.val:
            answer += 1
        slot = bisect_left(merged, node.val)
        if slot < k:
            merged.insert(slot, node.val)
            if len(merged) > k:
                merged.pop()
        smallest[id(node)] = merged
    return answer


class Solution:
    def countGreatEnoughNodes(self, root: TreeNode | None, k: int) -> int:
        return solve(root, k)
