"""Hack2Hire 69753e2817272b5c868d5eb3 (Compute Server Load Scores) over an INFERRED spec; qualification unknown."""
RULE_COST = {'LIGHT': 0, 'STANDARD': 2, 'HEAVY': 5}


def solve(servers, requests):
    scores = {}
    times = {}
    for server_id, base in servers:
        scores[server_id] = base
        times[server_id] = []
    for t, server_id, rule in requests:
        if server_id in scores:
            scores[server_id] += 1 + RULE_COST[rule]
            times[server_id].append(t)
    for server_id, ts in times.items():
        ts.sort()
        bursts = 0
        for j, t in enumerate(ts):
            if (j > 0 and t - ts[j - 1] <= 60) or (j + 1 < len(ts) and ts[j + 1] == t):
                bursts += 1
        scores[server_id] += 3 * bursts
    return [[server_id, scores[server_id]] for server_id, _ in servers]


class Solution:
    def computeLoadScores(self, servers, requests):
        return solve(servers, requests)
