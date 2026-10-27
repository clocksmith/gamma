"""428. Serialize and Deserialize N-ary Tree."""

class Node:
    def __init__(self, val=0, children=None):
        self.val = val
        self.children = [] if children is None else children


class Codec:
    def serialize(self, root):
        if root is None:
            return '#'
        tokens = []
        stack = [root]
        while stack:
            node = stack.pop()
            children = node.children or []
            tokens.append(f'{node.val}:{len(children)}')
            stack.extend(reversed(children))
        return ','.join(tokens)

    def deserialize(self, data):
        if data == '#' or data == '':
            return None
        tokens = data.split(',')
        value, count = map(int, tokens[0].split(':'))
        root = Node(value, [])
        stack = [[root, count]]
        for token in tokens[1:]:
            while stack and stack[-1][1] == 0:
                stack.pop()
            value, count = map(int, token.split(':'))
            child = Node(value, [])
            stack[-1][0].children.append(child)
            stack[-1][1] -= 1
            stack.append([child, count])
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
