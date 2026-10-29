"""Original frontend 297 variant; qualification unknown."""
from collections import deque


class TreeNode:
    def __init__(self, x, left=None, right=None):
        self.val = x
        self.left = left
        self.right = right


def _from_level_list(arr):
    if not arr or arr[0] is None:
        return None
    root = TreeNode(arr[0])
    q = deque([root])
    i = 1
    while q and i < len(arr):
        node = q.popleft()
        if i < len(arr):
            v = arr[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                q.append(node.left)
        if i < len(arr):
            v = arr[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                q.append(node.right)
    return root


def _to_level_list(root):
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


class Codec:
    def serialize(self, root):
        if root is None:
            return ""
        tokens = []
        q = deque([root])
        while q:
            node = q.popleft()
            if node is None:
                tokens.append("#")
            else:
                tokens.append(str(node.val))
                q.append(node.left)
                q.append(node.right)
        while tokens and tokens[-1] == "#":
            tokens.pop()
        return ",".join(tokens)

    def deserialize(self, data):
        if not data:
            return None
        parts = [None if tok == "#" else int(tok) for tok in data.split(",")]
        return _from_level_list(parts)


def solve(root):
    codec = Codec()
    if isinstance(root, list):
        tree = _from_level_list(root)
        rebuilt = codec.deserialize(codec.serialize(tree))
        return _to_level_list(rebuilt)
    return codec.deserialize(codec.serialize(root))
