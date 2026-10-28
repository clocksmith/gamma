def solve(points):
    parent = list(range(len(points)))
    size = [1] * len(points)
    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def merge(a, b):
        a, b = root(a), root(b)
        if a == b:
            return
        if size[a] < size[b]:
            a, b = b, a
        parent[b] = a
        size[a] += size[b]
    xs, ys = {}, {}
    for i, (x, y) in enumerate(points):
        if x in xs:
            merge(i, xs[x])
        if y in ys:
            merge(i, ys[y])
        xs[x] = ys[y] = i
    first = second = 0
    for i in range(len(points)):
        if root(i) == i:
            value = size[i]
            if value >= first:
                first, second = value, first
            elif value > second:
                second = value
    return first + second + 1


class Solution:
    def maxActivated(self, points):
        return solve(points)
