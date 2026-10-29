"""Original frontend 1740 variant; qualification unknown."""


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


def solve(root, p: int, q: int) -> int:
    if p == q:
        return 0
    head = _to_tree(root)

    def lca(node):
        if node is None or node.val == p or node.val == q:
            return node
        l = lca(node.left)
        r = lca(node.right)
        if l is not None and r is not None:
            return node
        return l if l is not None else r

    def dist(node, target, d) -> int:
        if node is None:
            return -1
        if node.val == target:
            return d
        dl = dist(node.left, target, d + 1)
        return dl if dl != -1 else dist(node.right, target, d + 1)

    anc = lca(head)
    return dist(anc, p, 0) + dist(anc, q, 0)


findDistance = solve


class Solution:
    def findDistance(self, root, p: int, q: int) -> int:
        return solve(root, p, q)
