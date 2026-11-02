"""Original frontend 156 variant; qualification unknown."""

from collections import deque
import copy


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


def _clone_tree(root):
    """Deep-copy a caller's node graph; reject a node reached twice (cycle or shared child).

    Iterative, so degenerate spines have no recursion limit. copy.copy keeps the
    caller's node class; children are then replaced by their copies.
    """
    if root is None:
        return None
    seen = {}

    def copy_of(node):
        if node is None:
            return None
        if id(node) in seen:
            raise ValueError("upsideDownBinaryTree: input is not a tree (node reached twice)")
        dup = copy.copy(node)
        dup.left = None
        dup.right = None
        seen[id(node)] = (node, dup)  # keep node alive so its id cannot be reused
        return dup

    head = copy_of(root)
    stack = [root]
    while stack:
        node = stack.pop()
        dup = seen[id(node)][1]
        dup.left = copy_of(node.left)
        dup.right = copy_of(node.right)
        if node.left is not None:
            stack.append(node.left)
        if node.right is not None:
            stack.append(node.right)
    return head


def _rotate(root):
    """In-place left-spine pointer rotation on nodes the caller of _rotate owns."""
    cur = root
    prev = None
    prev_right = None
    while cur is not None:
        nxt = cur.left
        cur.left = prev_right
        prev_right = cur.right
        cur.right = prev
        prev = cur
        cur = nxt
    return prev


def solve(root):
    """Pure value-domain entrypoint: never mutates the input and shares no node with it.

    A native node input is deep-copied first; that copy is charged as O(n) time and
    O(n) auxiliary space.
    """
    if isinstance(root, list):
        return _to_level(_rotate(_to_tree(root)))
    return _rotate(_clone_tree(root))


def upsideDownBinaryTree(root):
    """Official LeetCode ABI: rotates the caller's tree in place and returns the new root.

    native_effects.mutates_inputs = true. A level-order list is converted to fresh
    nodes first, so list callers see no mutation.
    """
    if isinstance(root, list):
        return _to_level(_rotate(_to_tree(root)))
    return _rotate(root)


class Solution:
    def upsideDownBinaryTree(self, root):
        return upsideDownBinaryTree(root)
