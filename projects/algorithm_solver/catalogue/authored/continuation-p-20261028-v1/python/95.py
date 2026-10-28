from functools import lru_cache


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def generateTrees(self, n):
        @lru_cache(None)
        def shapes(lo, hi):
            if lo > hi:
                return (None,)
            result = []
            for value in range(lo, hi + 1):
                for left in shapes(lo, value - 1):
                    for right in shapes(value + 1, hi):
                        result.append((value, left, right))
            return tuple(result)
        def materialize(shape):
            if shape is None:
                return None
            value, left, right = shape
            return TreeNode(value, materialize(left), materialize(right))
        return [materialize(shape) for shape in shapes(1, n)]
