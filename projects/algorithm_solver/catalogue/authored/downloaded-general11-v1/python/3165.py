"""3165. Maximum Sum of Subsequence With Nonadjacent Elements (Hard).

Specification: https://leetcode.com/problems/maximum-sum-of-subsequence-with-non-adjacent-elements/description/
"""


def solve(nums: list[int], queries: list[list[int]]) -> int:
    NEG = -10 ** 18
    n = len(nums)
    tree = [None] * (4 * n)

    def leaf(v):
        return ((0, NEG), (NEG, v))

    def merge(a, b):
        c = [[NEG, NEG], [NEG, NEG]]
        for i in range(2):
            for j in range(2):
                for x in range(2):
                    for y in range(2):
                        if x == 1 and y == 1:
                            continue
                        if a[i][x] == NEG or b[y][j] == NEG:
                            continue
                        c[i][j] = max(c[i][j], a[i][x] + b[y][j])
        return ((c[0][0], c[0][1]), (c[1][0], c[1][1]))

    def build(node, l, r):
        if l == r:
            tree[node] = leaf(nums[l])
            return
        mid = (l + r) // 2
        build(node * 2, l, mid)
        build(node * 2 + 1, mid + 1, r)
        tree[node] = merge(tree[node * 2], tree[node * 2 + 1])

    def update(node, l, r, pos, v):
        if l == r:
            tree[node] = leaf(v)
            return
        mid = (l + r) // 2
        if pos <= mid:
            update(node * 2, l, mid, pos, v)
        else:
            update(node * 2 + 1, mid + 1, r, pos, v)
        tree[node] = merge(tree[node * 2], tree[node * 2 + 1])

    build(1, 0, n - 1)
    MOD = 10 ** 9 + 7
    total = 0
    for pos, val in queries:
        nums[pos] = val
        update(1, 0, n - 1, pos, val)
        root = tree[1]
        best = max(root[0][0], root[0][1], root[1][0], root[1][1])
        total = (total + best) % MOD
    return total


class Solution:
    def maximumSumSubsequence(self, nums, queries):
        return solve(nums, queries)
