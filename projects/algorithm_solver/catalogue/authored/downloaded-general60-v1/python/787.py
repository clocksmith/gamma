"""787. Cheapest Flights Within K Stops (Medium).

Specification: https://leetcode.com/problems/cheapest-flights-within-k-stops/description/
"""


def solve(n: int, flights: list[list[int]], src: int, dst: int, k: int) -> int:
    dist = [float('inf')] * n
    dist[src] = 0
    for _step in range(k + 1):
        nxt = dist[:]
        for frm, to, price in flights:
            if dist[frm] != float('inf'):
                nxt[to] = min(nxt[to], dist[frm] + price)
        dist = nxt
    return -1 if dist[dst] == float('inf') else dist[dst]


class Solution:
    def findCheapestPrice(self, n: int, flights: list[list[int]], src: int, dst: int, k: int) -> int:
        return solve(n, flights, src, dst, k)
