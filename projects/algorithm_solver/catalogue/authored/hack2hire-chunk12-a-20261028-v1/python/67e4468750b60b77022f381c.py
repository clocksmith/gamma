"""Hack2Hire 67e4468750b60b77022f381c (Maximum Multiplier Path) over an INFERRED spec; qualification unknown."""


def solve(n, edges, start, end):
    out = [[] for _ in range(n)]
    for u, v, w in edges:
        out[u].append((v, w))
    best = [[-1] * n for _ in range(1 << n)]  # best[mask][v]: largest product of a simple path start..v visiting mask
    best[1 << start][start] = 1
    answer = -1
    for mask in range(1 << n):
        if not mask >> start & 1:
            continue
        row = best[mask]
        for v in range(n):
            p = row[v]
            if p < 0:
                continue
            if v == end and p > answer:
                answer = p
            for w, mult in out[v]:
                if not mask >> w & 1:
                    nxt = best[mask | 1 << w]
                    if p * mult > nxt[w]:
                        nxt[w] = p * mult
    return answer


class Solution:
    def maxMultiplierProduct(self, n, edges, start, end):
        return solve(n, edges, start, end)
