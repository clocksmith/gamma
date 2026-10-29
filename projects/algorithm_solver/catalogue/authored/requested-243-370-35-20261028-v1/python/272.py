"""Original frontend 272 variant; qualification unknown."""


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


def solve(root, target: float, k: int):
    head = _to_tree(root)
    vals = []

    def inorder(node):
        if node is None:
            return
        inorder(node.left)
        vals.append(node.val)
        inorder(node.right)

    inorder(head)
    lo = 0
    for i in range(k, len(vals)):
        if abs(vals[i] - target) < abs(vals[lo] - target):
            lo += 1
        else:
            break
    return vals[lo : lo + k]


closestKValues = solve


class Solution:
    def closestKValues(self, root, target: float, k: int):
        return solve(root, target, k)
