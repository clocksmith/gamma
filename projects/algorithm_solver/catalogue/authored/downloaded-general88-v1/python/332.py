"""332. Reconstruct Itinerary (Hard).

Specification: https://leetcode.com/problems/reconstruct-itinerary/description/
"""


def solve(tickets: list[list[str]]) -> list[str]:
    graph = {}
    for frm, to in tickets:
        graph.setdefault(frm, []).append(to)
    for frm in graph:
        graph[frm].sort(reverse=True)
    result = []

    def visit(airport):
        while graph.get(airport):
            visit(graph[airport].pop())
        result.append(airport)

    visit('JFK')
    return result[::-1]


class Solution:
    def findItinerary(self, tickets: list[list[str]]) -> list[str]:
        return solve(tickets)
