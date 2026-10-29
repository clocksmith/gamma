"""Hack2Hire 6779c17edcf91f8e3c1c310f (Monsters Battle, level 1) over an INFERRED spec; qualification unknown."""

LEVEL = 1


def solve(monsters, root):
    kids, hostile, cost = {}, {}, {}
    for row in monsters:
        label = row[0]
        name = label[:-1] if label.endswith('*') else label
        kids[name] = row[-1]
        hostile[name] = label.endswith('*')
        cost[name] = row[1] if LEVEL == 2 else 0
    order, stack = [], [root]
    while stack:
        u = stack.pop()
        order.append(u)
        stack.extend(kids[u])
    below = {}
    for u in reversed(order):
        below[u] = sum(below[c] + hostile[c] for c in kids[u])
    if LEVEL == 1:
        total = below[root] + hostile[root]
        return sorted(u for u in order if not hostile[u] and below[u] == total)
    if hostile[root]:
        return -1
    need = {}  # None: impossible inside the subtree
    for u in reversed(order):
        if below[u] == 0:
            need[u] = 0
            continue
        split = 0
        for c in kids[u]:
            if hostile[c] or need[c] is None:
                split = None
                break
            split += need[c]
        options = [x for x in (None if hostile[u] else cost[u], split) if x is not None]
        need[u] = min(options) if options else None
    return -1 if need[root] is None else need[root]


class Solution:
    def canDefeatAll(self, monsters, root):
        return solve(monsters, root)
