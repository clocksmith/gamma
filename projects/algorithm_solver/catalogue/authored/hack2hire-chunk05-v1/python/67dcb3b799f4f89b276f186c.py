"""Original hack2hire:67dcb3b799f4f89b276f186c; inferred public-preview contract; qualification unknown."""
from collections import deque

def referralLeaderboard(referrers, referrals):
    parent = dict(zip(referrals, referrers))
    nodes = set(referrers) | set(referrals)
    pending = {node: 0 for node in nodes}
    totals = {node: 0 for node in nodes}
    for source in referrers:
        pending[source] += 1
    queue = deque(node for node in nodes if pending[node] == 0)
    while queue:
        node = queue.popleft()
        if node not in parent:
            continue
        target = parent[node]
        totals[target] += 1 + totals[node]
        pending[target] -= 1
        if pending[target] == 0:
            queue.append(target)
    ranked = sorted(set(referrers), key=lambda name: (-totals[name], name))[:3]
    return [[name, totals[name]] for name in ranked]

solve = referralLeaderboard

class Solution:
    referralLeaderboard = staticmethod(referralLeaderboard)
