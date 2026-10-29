"""Hack2Hire 67709b6d366afdc1233e4ffc (Largest Common BST Value) over an INFERRED spec; qualification unknown."""


def _decode(a):
    values, left, right = [a[0]], [-1], [-1]
    queue, head, i = [0], 0, 1
    while i < len(a):
        parent = queue[head]
        head += 1
        for side in (left, right):
            if i < len(a):
                if a[i] is not None:
                    values.append(a[i]); left.append(-1); right.append(-1)
                    side[parent] = len(values) - 1
                    queue.append(len(values) - 1)
                i += 1
    return values, left, right


class _Descending:
    """Reverse in-order walk of a decoded tree with an explicit stack."""
    def __init__(self, tree):
        self.values, self.left, self.right = tree
        self.stack = []
        self._push(0)

    def _push(self, node):
        while node != -1:
            self.stack.append(node)
            node = self.right[node]

    def next(self):
        if not self.stack:
            return None
        node = self.stack.pop()
        self._push(self.left[node])
        return self.values[node]


def solve(root1, root2):
    a, b = _Descending(_decode(root1)), _Descending(_decode(root2))
    x, y = a.next(), b.next()
    while x is not None and y is not None:
        if x == y:
            return x
        if x > y:
            x = a.next()
        else:
            y = b.next()
    return -1


class Solution:
    def largestCommonValue(self, root1, root2):
        return solve(root1, root2)
