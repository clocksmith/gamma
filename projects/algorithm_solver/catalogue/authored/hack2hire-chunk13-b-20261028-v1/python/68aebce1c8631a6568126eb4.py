"""Hack2Hire 68aebce1c8631a6568126eb4 (Same Word of HTML Labels) over an INFERRED spec; qualification unknown."""


def _next_leaf(tree, stack):
    while stack:
        text, children = tree[stack.pop()]
        if children:
            stack.extend(reversed(children))
        else:
            return text
    return None


def solve(tree1, tree2):
    stack1, stack2 = [0], [0]
    a, b = _next_leaf(tree1, stack1), _next_leaf(tree2, stack2)
    i = j = 0
    while a is not None and b is not None:
        if a[i] != b[j]:
            return False
        i += 1
        j += 1
        if i == len(a):
            a, i = _next_leaf(tree1, stack1), 0
        if j == len(b):
            b, j = _next_leaf(tree2, stack2), 0
    return a is None and b is None


class Solution:
    def sameWord(self, tree1, tree2):
        return solve(tree1, tree2)
