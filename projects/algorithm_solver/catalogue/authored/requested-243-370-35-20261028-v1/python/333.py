"""Original frontend 333 variant; qualification unknown."""


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


def solve(root) -> int:
    head = _to_tree(root)
    INF = 10**18

    def dfs(node):
        if node is None:
            return True, INF, -INF, 0
        ok_l, mn_l, mx_l, sz_l = dfs(node.left)
        ok_r, mn_r, mx_r, sz_r = dfs(node.right)
        if ok_l and ok_r and mx_l < node.val < mn_r:
            return True, min(mn_l, node.val), max(mx_r, node.val), sz_l + sz_r + 1
        return False, -INF, INF, max(sz_l, sz_r)

    return dfs(head)[3]


largestBSTSubtree = solve


class Solution:
    def largestBSTSubtree(self, root) -> int:
        return solve(root)
