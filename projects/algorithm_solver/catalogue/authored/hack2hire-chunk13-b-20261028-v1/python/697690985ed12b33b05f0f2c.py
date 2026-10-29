"""Hack2Hire 697690985ed12b33b05f0f2c (Shipping Route Cost Paths, variant 2 of 3) over an INFERRED spec; qualification unknown."""


def solve(routes, source, target):
    out_routes = {}
    for route in routes:
        a, b, method, cost = route.split(':')
        out_routes.setdefault(a, []).append((b, method, int(cost)))
    paths = []
    for middle, method, cost in out_routes.get(source, []):
        if middle == target:
            paths.append((cost, source + ':' + method + ':' + target))
            continue
        for end, method2, cost2 in out_routes.get(middle, []):
            if end == target:
                paths.append((cost + cost2, source + ':' + method + ':' + middle + ':' + method2 + ':' + target))
    paths.sort()
    return [[path, cost] for cost, path in paths]


class Solution:
    def pathsWithOneTransfer(self, routes, source, target):
        return solve(routes, source, target)
