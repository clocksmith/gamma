"""Hack2Hire 68dc36c49736cfa4e9062419 (Partition Array by Equivalence Function) over an INFERRED spec; qualification unknown."""


def solve(nums, equivalentPairs):
    parent = {}
    size = {}

    def find(x):
        if x not in parent:
            parent[x] = x
            size[x] = 1
            return x
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in equivalentPairs:
        ra = find(a)
        rb = find(b)
        if ra != rb:
            if size[ra] < size[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            size[ra] += size[rb]
    groups = []
    where = {}
    for x in nums:
        root = find(x)
        group = where.get(root)
        if group is None:
            group = []
            where[root] = group
            groups.append(group)
        group.append(x)
    return groups


class Solution:
    def partitionByEquivalence(self, nums, equivalentPairs):
        return solve(nums, equivalentPairs)
