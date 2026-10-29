"""Hack2Hire 68c301d01f64f4312b0a3e0a (Maximum Ski Score) over an INFERRED spec; qualification unknown."""


def solve(routes, checkpoints):
    reward = {}
    for name, value in checkpoints:
        reward[name] = value
    out = {}
    for start, cost, end in routes:
        out.setdefault(start, []).append((cost, end))
    seen = {'lodge'}
    order = []
    stack = ['lodge']
    while stack:
        v = stack.pop()
        order.append(v)
        for _, w in out.get(v, ()):
            if w not in seen:
                seen.add(w)
                stack.append(w)
    indegree = {v: 0 for v in order}
    for v in order:
        for _, w in out.get(v, ()):
            indegree[w] += 1
    topo = []
    ready = ['lodge']
    while ready:
        v = ready.pop()
        topo.append(v)
        for _, w in out.get(v, ()):
            indegree[w] -= 1
            if indegree[w] == 0:
                ready.append(w)
    best = {}
    for v in reversed(topo):
        nxt = out.get(v)
        if not nxt:
            best[v] = 0
            continue
        value = None
        for cost, w in nxt:
            candidate = reward.get(w, 0) - cost + best[w]
            if value is None or candidate > value:
                value = candidate
        best[v] = value
    return best['lodge']


class Solution:
    def maxSkiScore(self, routes, checkpoints):
        return solve(routes, checkpoints)
