"""385. Mini Parser."""

class NestedInteger:
    """Standalone implementation of the judge's NestedInteger protocol."""
    def __init__(self, value=None):
        self.value = value
        self.items = [] if value is None else None

    def isInteger(self):
        return self.items is None

    def add(self, elem):
        if self.items is None:
            self.items = []
            self.value = None
        self.items.append(elem)

    def setInteger(self, value):
        self.value = value
        self.items = None

    def getInteger(self):
        return self.value if self.items is None else None

    def getList(self):
        return self.items


def solve(s: str, nested_integer_type=None):
    """Iterative parser. An optional factory supports a host-supplied NestedInteger class."""
    factory = NestedInteger if nested_integer_type is None else nested_integer_type
    if s[0] != '[':
        return factory(int(s))
    stack = []
    start = None
    result = None
    for i, char in enumerate(s):
        if char == '[':
            stack.append(factory())
        elif char in ',]':
            if start is not None:
                stack[-1].add(factory(int(s[start:i])))
                start = None
            if char == ']':
                node = stack.pop()
                if stack:
                    stack[-1].add(node)
                else:
                    result = node
        elif start is None:
            start = i
    return result


class Solution:
    def deserialize(self, s: str):
        return solve(s)
