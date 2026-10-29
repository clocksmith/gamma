"""Original frontend 250 variant; qualification unknown."""


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
    cnt = 0

    def dfs(node) -> bool:
        nonlocal cnt
        if node is None:
            return True
        ok_l = dfs(node.left)
        ok_r = dfs(node.right)
        if not (ok_l and ok_r):
            return False
        if node.left is not None and node.left.val != node.val:
            return False
        if node.right is not None and node.right.val != node.val:
            return False
        cnt += 1
        return True

    dfs(head)
    return cnt


countUnivalSubtrees = solve


class Solution:
    def countUnivalSubtrees(self, root) -> int:
        return solve(root)
