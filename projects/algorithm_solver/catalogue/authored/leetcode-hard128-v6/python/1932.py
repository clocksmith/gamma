"""1932. Merge BSTs to Create Single BST.

Graft matching root values during iterative bounded BST traversal; O(n) time and space. Return fresh nodes and preserve all input trees.
"""

class _TreeNode:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None


def solve(trees: list) -> object:
    roots = {tree.val: tree for tree in trees}
    leaves = set()
    for tree in trees:
        if tree.left is not None:
            leaves.add(tree.left.val)
        if tree.right is not None:
            leaves.add(tree.right.val)
    candidates = [value for value in roots if value not in leaves]
    if len(candidates) != 1:
        return None
    source = roots.pop(candidates[0])
    result = _TreeNode(source.val)
    stack = [(source, result, float('-inf'), float('inf'))]
    while stack:
        source, target, lower, upper = stack.pop()
        if not lower < source.val < upper:
            return None
        if source.left is None and source.right is None and source.val in roots:
            source = roots.pop(source.val)
        if source.right is not None:
            target.right = _TreeNode(source.right.val)
            stack.append((source.right, target.right, source.val, upper))
        if source.left is not None:
            target.left = _TreeNode(source.left.val)
            stack.append((source.left, target.left, lower, source.val))
    return result if not roots else None


class Solution:
    def canMerge(self, trees: list) -> object:
        return solve(trees)
