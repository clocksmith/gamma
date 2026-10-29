"""Hack2Hire 6a222b9c981072682a6f1e5a (Build Transition Graph) over an INFERRED spec; qualification unknown."""


def solve(logs):
    by_user = {}
    for ts, user, resource in logs:
        by_user.setdefault(user, []).append((int(ts), resource))
    counts = {}
    for entries in by_user.values():
        entries.sort()
        prev = 'START'
        for _, resource in entries:
            key = (prev, resource)
            counts[key] = counts.get(key, 0) + 1
            prev = resource
        key = (prev, 'END')
        counts[key] = counts.get(key, 0) + 1
    return [[a, b, counts[(a, b)]] for a, b in sorted(counts)]


class Solution:
    def buildTransitionGraph(self, logs):
        return solve(logs)
