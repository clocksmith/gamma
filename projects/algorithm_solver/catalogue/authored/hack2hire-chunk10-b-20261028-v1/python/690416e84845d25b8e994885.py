"""Hack2Hire 690416e84845d25b8e994885 (Find Complete Flight Path) over an INFERRED spec; qualification unknown."""


def solve(tickets):
    adj, balance = {}, {}
    for a, b in tickets:
        adj.setdefault(a, []).append(b)
        balance[a] = balance.get(a, 0) + 1
        balance[b] = balance.get(b, 0) - 1
    for a in adj:
        adj[a].sort(reverse=True)  # pop() then yields the smallest destination
    start = None
    for airport, d in balance.items():
        if d == 1:
            start = airport
    if start is None:
        start = min(adj)
    stack, route = [start], []
    while stack:
        nxt = adj.get(stack[-1])
        if nxt:
            stack.append(nxt.pop())
        else:
            route.append(stack.pop())
    return route[::-1]


class Solution:
    def findItinerary(self, tickets):
        return solve(tickets)
