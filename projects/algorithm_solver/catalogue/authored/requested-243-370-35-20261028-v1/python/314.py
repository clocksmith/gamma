"""Original frontend 314 variant; qualification unknown."""

from collections import defaultdict, deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def _to_tree(root):
    if root is None or isinstance(root, TreeNode) or hasattr(root, "left"):
        return root
    if not root or root[0] is None:
        return []
    nodes = [None if v is None else TreeNode(v) for v in root]
    kids = nodes[::-1]
    head = kids.pop()
    for node in nodes:
        if node is not None:
            if kids:
                node.left = kids.pop()
            if kids:
                node.right = kids.pop()
    return head


def solve(root):
    head = _to_tree(root)
    if not head:
        return []
    cols = defaultdict(list)
    q = deque([(head, 0)])
    min_c = max_c = 0
    while q:
        node, c = q.popleft()
        cols[c].append(node.val)
        if c < min_c:
            min_c = c
        if c > max_c:
            max_c = c
        if node.left is not None:
            q.append((node.left, c - 1))
        if node.right is not None:
            q.append((node.right, c + 1))
    return [cols[c] for c in range(min_c, max_c + 1)]


verticalOrder = solve


class Solution:
    def verticalOrder(self, root):
        return solve(root)
