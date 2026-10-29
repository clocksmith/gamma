"""Hack2Hire 67a2d68216a8465483dca727 (Process Queue) over an INFERRED spec; qualification unknown."""


def solve(wait):
    n = len(wait)
    sizes = [n]
    bucket = [0] * (n + 2)  # unprocessed processes per wait value (only waits <= n can expire in time)
    for w in wait:
        if w <= n:
            bucket[w] += 1
    processed = bytearray(n)
    alive, front, t = n, 0, 0
    while alive:
        t += 1
        while processed[front] or wait[front] <= t - 1:
            front += 1
        processed[front] = 1
        alive -= 1
        if wait[front] <= n:
            bucket[wait[front]] -= 1
        front += 1
        alive -= bucket[t]
        sizes.append(alive)
    return sizes


class Solution:
    def processQueue(self, wait):
        return solve(wait)
