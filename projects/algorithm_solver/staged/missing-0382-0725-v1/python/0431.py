"""431. Encode N-ary Tree to Binary Tree."""

class Node:
    def __init__(self, val=0, children=None):
        self.val = val
        self.children = [] if children is None else children


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Codec:
    def encode(self, root):
        if root is None:
            return None
        result = TreeNode(root.val)
        stack = [(root, result)]
        while stack:
            original, binary = stack.pop()
            previous = None
            for child in original.children or []:
                copy = TreeNode(child.val)
                if previous is None:
                    binary.left = copy
                else:
                    previous.right = copy
                previous = copy
                stack.append((child, copy))
        return result

    def decode(self, data):
        if data is None:
            return None
        result = Node(data.val, [])
        stack = [(data, result)]
        while stack:
            binary, original = stack.pop()
            child = binary.left
            while child is not None:
                copy = Node(child.val, [])
                original.children.append(copy)
                stack.append((child, copy))
                child = child.right
        return result


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = Codec(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = Codec
