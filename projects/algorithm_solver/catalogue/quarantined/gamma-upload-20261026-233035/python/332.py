"""332. Reconstruct Itinerary."""
import heapq
from collections import defaultdict

def solve(tickets: list[list[str]]) -> list[str]:
    graph = defaultdict(list)
    for origin, destination in tickets:
        heapq.heappush(graph[origin], destination)
    route = []
    def visit(airport: str) -> None:
        while graph[airport]:
            visit(heapq.heappop(graph[airport]))
        route.append(airport)
    visit('JFK')
    return route[::-1]

class Solution:
    def findItinerary(self, tickets: list[list[str]]) -> list[str]:
        return solve(tickets)
