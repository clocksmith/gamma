"""Hack2Hire 6a32d62c65569fa70cc7eba3 (Minimum Operations to Sort by Rotate and Flip) over an INFERRED spec; qualification unknown."""
from collections import deque


def solve(arr):
    n = len(arr)
    if n == 1: return 0
    m = min(range(n), key=arr.__getitem__)
    goals = set()
    # state (r, f): f == 0 reads arr[(r + j) % n], f == 1 reads arr[(r - j) % n]
    if all(arr[(m + j) % n] < arr[(m + j + 1) % n] for j in range(n - 1)): goals.add(2 * m)
    if all(arr[(m - j) % n] < arr[(m - j - 1) % n] for j in range(n - 1)): goals.add(2 * m + 1)
    if not goals: return -1
    dist = [-1] * (2 * n)
    dist[0] = 0
    queue = deque([0])
    while queue:
        state = queue.popleft()
        if state in goals: return dist[state]
        r, f = state >> 1, state & 1
        if f == 0: moves = (2 * ((r + 1) % n), 2 * ((r + n - 1) % n) + 1)
        else: moves = (2 * ((r - 1) % n) + 1, 2 * ((r + 1) % n))
        for nxt in moves:
            if dist[nxt] < 0:
                dist[nxt] = dist[state] + 1
                queue.append(nxt)
    return -1


class Solution:
    def minOperations(self, arr):
        return solve(arr)
