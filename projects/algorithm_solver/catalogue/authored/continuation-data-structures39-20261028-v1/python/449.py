"""Original frontend 449 variant; qualification unknown."""
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
    def serialize(self, root) -> str:
        if root is None:
            return ""
        vals = []
        stack = [root]
        while stack:
            node = stack.pop()
            vals.append(str(node.val))
            if node.right is not None:
                stack.append(node.right)
            if node.left is not None:
                stack.append(node.left)
        return ",".join(vals)

    def deserialize(self, data: str):
        if not data:
            return None
        nums = [int(x) for x in data.split(",")]
        root = TreeNode(nums[0])
        stack = [root]
        for val in nums[1:]:
            node = TreeNode(val)
            if val < stack[-1].val:
                stack[-1].left = node
            else:
                parent = None
                while stack and stack[-1].val < val:
                    parent = stack.pop()
                parent.right = node
            stack.append(node)
        return root


def solve(root):
    codec = Codec()
    if isinstance(root, list):
        tree = _from_level_list(root)
        rebuilt = codec.deserialize(codec.serialize(tree))
        return _to_level_list(rebuilt)
    return codec.deserialize(codec.serialize(root))
