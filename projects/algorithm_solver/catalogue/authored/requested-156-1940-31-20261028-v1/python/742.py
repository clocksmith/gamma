"""Original frontend 742 variant; qualification unknown."""

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
        return None
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


def solve(root, k: int) -> int:
    head = _to_tree(root)
    adj = defaultdict(list)
    leaves = set()

    def dfs(node, par):
        if node is None:
            return
        u = node.val
        if par is not None:
            adj[u].append(par)
            adj[par].append(u)
        if node.left is None and node.right is None:
            leaves.add(u)
        dfs(node.left, u)
        dfs(node.right, u)

    dfs(head, None)
    q = deque([k])
    vis = {k}
    while q:
        u = q.popleft()
        if u in leaves:
            return u
        for v in adj[u]:
            if v not in vis:
                vis.add(v)
                q.append(v)
    return k


findClosestLeaf = solve


class Solution:
    def findClosestLeaf(self, root, k: int) -> int:
        return solve(root, k)
