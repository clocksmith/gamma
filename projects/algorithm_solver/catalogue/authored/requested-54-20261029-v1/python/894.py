"""Original development candidate; independent qualification pending."""
from functools import lru_cache

def solve(n):
    @lru_cache(None)
    def shapes(size):
        if size == 1:
            return (None,)
        return tuple((a,b) for left in range(1,size,2) for a in shapes(left) for b in shapes(size-1-left))
    def build(shape):
        node = TreeNode(0)
        if shape is not None:
            node.left = build(shape[0])
            node.right = build(shape[1])
        return node
    return [build(shape) for shape in shapes(n)] if n % 2 else []


class Solution:
    def allPossibleFBT(self, n):
        return solve(n)
