"""Original frontend 3319 variant; qualification unknown."""


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
    sizes = []

    def dfs(node):
        if node is None:
            return True, 0
        ok_l, hl = dfs(node.left)
        ok_r, hr = dfs(node.right)
        if ok_l and ok_r and hl == hr:
            h = hl + 1
            sizes.append((1 << h) - 1)
            return True, h
        return False, 0

    dfs(head)
    sizes.sort(reverse=True)
    return sizes[k - 1] if len(sizes) >= k else -1


kthLargestPerfectSubtree = solve


class Solution:
    def kthLargestPerfectSubtree(self, root, k: int) -> int:
        return solve(root, k)
