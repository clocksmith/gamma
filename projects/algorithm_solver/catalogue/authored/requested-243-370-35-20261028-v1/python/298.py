"""Original frontend 298 variant; qualification unknown."""


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
    if head is None:
        return 0
    best = 0

    def dfs(node, parent_val, cur_len):
        nonlocal best
        if node is None:
            return
        ln = cur_len + 1 if parent_val is not None and node.val == parent_val + 1 else 1
        if ln > best:
            best = ln
        dfs(node.left, node.val, ln)
        dfs(node.right, node.val, ln)

    dfs(head, None, 0)
    return best


longestConsecutive = solve


class Solution:
    def longestConsecutive(self, root) -> int:
        return solve(root)
