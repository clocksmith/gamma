import heapq


def solve(sticks):
    heapq.heapify(sticks)
    cost = 0
    while len(sticks) > 1:
        joined = heapq.heappop(sticks) + heapq.heappop(sticks)
        cost += joined
        heapq.heappush(sticks, joined)
    return cost
