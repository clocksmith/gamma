"""449. Serialize and Deserialize BST."""

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Codec:
    def serialize(self, root):
        values = []
        stack = [root] if root else []
        while stack:
            node = stack.pop()
            values.append(str(node.val))
            if node.right:
                stack.append(node.right)
            if node.left:
                stack.append(node.left)
        return ','.join(values)

    def deserialize(self, data):
        if not data:
            return None
        values = list(map(int, data.split(',')))
        root = TreeNode(values[0])
        stack = [root]
        for value in values[1:]:
            node = TreeNode(value)
            if value < stack[-1].val:
                stack[-1].left = node
            else:
                parent = stack[-1]
                while stack and stack[-1].val < value:
                    parent = stack.pop()
                parent.right = node
            stack.append(node)
        return root


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
