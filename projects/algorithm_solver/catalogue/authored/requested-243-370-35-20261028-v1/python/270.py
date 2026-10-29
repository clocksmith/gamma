"""Original frontend 270 variant; qualification unknown."""


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


def solve(root, target: float) -> int:
    cur = _to_tree(root)
    best = cur.val
    while cur is not None:
        v = cur.val
        if abs(v - target) < abs(best - target) or (abs(v - target) == abs(best - target) and v < best):
            best = v
        cur = cur.left if target < v else cur.right
    return best


closestValue = solve


class Solution:
    def closestValue(self, root, target: float) -> int:
        return solve(root, target)
