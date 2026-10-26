"""2646. Minimize the Total Price of the Trips. Count path visits, then choose a minimum-cost independent set of discounts."""


def solve(n: int, edges: list[list[int]], price: list[int], trips: list[list[int]]) -> int:
    """O(n*(t+1)) time and O(n) space. Inputs are preserved."""
    graph = [[] for _ in range(n)]
    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
    parent = [-1] * n
    depth = [0] * n
    order = [0]
    for node in order:
        for neighbor in graph[node]:
            if neighbor == parent[node]:
                continue
            parent[neighbor] = node
            depth[neighbor] = depth[node] + 1
            order.append(neighbor)
    visits = [0] * n
    for first, second in trips:
        while first != second:
            if depth[first] >= depth[second]:
                visits[first] += 1
                first = parent[first]
            else:
                visits[second] += 1
                second = parent[second]
        visits[first] += 1
    full = [visits[node] * price[node] for node in range(n)]
    half = [visits[node] * (price[node] // 2) for node in range(n)]
    for node in reversed(order[1:]):
        previous = parent[node]
        full[previous] += min(full[node], half[node])
        half[previous] += full[node]
    return min(full[0], half[0])


class Solution:
    def minimumTotalPrice(self, n: int, edges: list[list[int]], price: list[int], trips: list[list[int]]) -> int:
        return solve(n, edges, price, trips)
