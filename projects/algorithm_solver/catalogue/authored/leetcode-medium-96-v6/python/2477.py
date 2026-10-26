"""2477. Minimum Fuel Cost to Report to the Capital: aggregate representatives in iterative postorder and charge full cars across each edge."""


def solve(roads: list[list[int]], seats: int) -> int:
    """O(n) time and O(n) auxiliary space for n tree vertices; inputs are read-only."""
    size = len(roads) + 1
    graph = [[] for _ in range(size)]
    for left, right in roads:
        graph[left].append(right)
        graph[right].append(left)
    parent = [-1] * size
    order = [0]
    for node in order:
        for neighbor in graph[node]:
            if neighbor != parent[node]:
                parent[neighbor] = node
                order.append(neighbor)
    people = [1] * size
    fuel = 0
    for index in range(len(order) - 1, 0, -1):
        node = order[index]
        fuel += (people[node] + seats - 1) // seats
        people[parent[node]] += people[node]
    return fuel


class Solution:
    def minimumFuelCost(self, roads: list[list[int]], seats: int) -> int:
        return solve(roads, seats)
