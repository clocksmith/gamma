"""Hack2Hire 6781dbee3cd890ccd3798fc0 (Find the Nearest City) over an INFERRED spec; qualification unknown."""


def solve(cities, xs, ys, queries):
    n = len(cities)
    by_x = sorted(range(n), key=lambda i: (xs[i], ys[i]))
    by_y = sorted(range(n), key=lambda i: (ys[i], xs[i]))
    near = [[] for _ in range(n)]
    for a, b in zip(by_x, by_x[1:]):
        if xs[a] == xs[b]:
            near[a].append(b)
            near[b].append(a)
    for a, b in zip(by_y, by_y[1:]):
        if ys[a] == ys[b]:
            near[a].append(b)
            near[b].append(a)
    position = {name: i for i, name in enumerate(cities)}
    answer = []
    for q in queries:
        i = position[q]
        best = None
        for j in near[i]:
            key = (abs(xs[i] - xs[j]) + abs(ys[i] - ys[j]), cities[j])
            if best is None or key < best:
                best = key
        answer.append('NONE' if best is None else best[1])
    return answer


class Solution:
    def nearestCities(self, cities, xs, ys, queries):
        return solve(cities, xs, ys, queries)
