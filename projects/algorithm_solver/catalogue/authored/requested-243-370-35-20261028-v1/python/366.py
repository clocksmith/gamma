"""Original frontend 366 variant; qualification unknown."""


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


def solve(root):
    head = _to_tree(root)
    res = []

    def dfs(node) -> int:
        if node is None:
            return -1
        h = 1 + max(dfs(node.left), dfs(node.right))
        if h == len(res):
            res.append([])
        res[h].append(node.val)
        return h

    dfs(head)
    return res


findLeaves = solve


class Solution:
    def findLeaves(self, root):
        return solve(root)
