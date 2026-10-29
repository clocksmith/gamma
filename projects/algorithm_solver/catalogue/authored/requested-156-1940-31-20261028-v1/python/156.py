"""Original frontend 156 variant; qualification unknown."""

from collections import deque


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


def _to_level(root):
    if root is None:
        return []
    out = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            out.append(None)
        else:
            out.append(node.val)
            q.append(node.left)
            q.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


def solve(root):
    is_list = isinstance(root, list)
    cur = _to_tree(root)
    prev = None
    prev_right = None
    while cur is not None:
        nxt = cur.left
        cur.left = prev_right
        prev_right = cur.right
        cur.right = prev
        prev = cur
        cur = nxt
    return _to_level(prev) if is_list else prev


upsideDownBinaryTree = solve


class Solution:
    def upsideDownBinaryTree(self, root):
        return solve(root)
