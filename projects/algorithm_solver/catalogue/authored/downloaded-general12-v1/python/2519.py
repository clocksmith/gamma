"""2519. Count the Number of K-Big Indices (Hard).

Specification: https://leetcode.com/problems/count-the-number-of-k-big-indices/description/
"""


def solve(nums, k):
    class BIT:
        def __init__(self, n):
            self.n = n
            self.c = [0] * (n + 1)

        def update(self, x, delta):
            while x <= self.n:
                self.c[x] += delta
                x += x & -x

        def query(self, x):
            s = 0
            while x > 0:
                s += self.c[x]
                x -= x & -x
            return s

    vals = sorted(set(nums))
    rank = {v: i + 1 for i, v in enumerate(vals)}
    left = BIT(len(vals))
    right = BIT(len(vals))
    for v in nums:
        right.update(rank[v], 1)
    ans = 0
    for v in nums:
        r = rank[v]
        right.update(r, -1)
        if left.query(r - 1) >= k and right.query(r - 1) >= k:
            ans += 1
        left.update(r, 1)
    return ans


class Solution:
    def kBigIndices(self, nums, k):
        return solve(nums, k)
