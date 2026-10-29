"""Hack2Hire 69e939d0fbaf3da6418286b1 (Minimum Triggers to Absorb All Balls) over an INFERRED spec; qualification unknown."""


def solve(balls, d):
    n = len(balls)
    parent = list(range(n))
    size = [1] * n
    components = n

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for axis in (0, 1):
        other = 1 - axis
        order = sorted(range(n), key=lambda i: (balls[i][axis], balls[i][other]))
        for a, b in zip(order, order[1:]):
            if balls[a][axis] == balls[b][axis] and balls[b][other] - balls[a][other] <= d:
                ra, rb = find(a), find(b)
                if ra != rb:
                    if size[ra] < size[rb]: ra, rb = rb, ra
                    parent[rb] = ra
                    size[ra] += size[rb]
                    components -= 1
    return components


class Solution:
    def minTriggers(self, balls, d):
        return solve(balls, d)
