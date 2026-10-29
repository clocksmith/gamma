"""Hack2Hire 6976850c5ed12b33b05f0f0f (Shipping Route Cost Paths, variant 1 of 3) over an INFERRED spec; qualification unknown."""


def solve(routes, source, target):
    found = []
    for route in routes:
        a, b, method, cost = route.split(':')
        if a == source and b == target:
            found.append((int(cost), method))
    found.sort()
    return [[method, cost] for cost, method in found]


class Solution:
    def directRoutes(self, routes, source, target):
        return solve(routes, source, target)
