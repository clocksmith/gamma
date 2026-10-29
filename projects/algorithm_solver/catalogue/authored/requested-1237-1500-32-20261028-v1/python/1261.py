"""Original frontend 1261 variant; qualification unknown."""
from collections import deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def _from_level(arr):
    if not arr or arr[0] is None:
        return None
    root = TreeNode(arr[0])
    q = deque([root])
    i = 1
    while q and i < len(arr):
        n = q.popleft()
        if i < len(arr):
            v = arr[i]; i += 1
            if v is not None:
                n.left = TreeNode(v); q.append(n.left)
        if i < len(arr):
            v = arr[i]; i += 1
            if v is not None:
                n.right = TreeNode(v); q.append(n.right)
    return root


class FindElements:
    def __init__(self, root):
        if isinstance(root, list):
            root = _from_level(root)
        seen = set()
        if root is not None:
            stack = [(root, 0)]
            while stack:
                node, v = stack.pop()
                seen.add(v)
                if node.left is not None:
                    stack.append((node.left, 2 * v + 1))
                if node.right is not None:
                    stack.append((node.right, 2 * v + 2))
        self.seen = seen

    def find(self, target: int) -> bool:
        return target in self.seen


def solve(operation_names, argument_lists):
    inst = FindElements(argument_lists[0][0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        out.append(inst.find(args[0]))
    return out
