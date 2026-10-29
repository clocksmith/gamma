"""Original frontend 755 variant; qualification unknown."""


def solve(heights, volume: int, k: int):
    h = list(heights)
    n = len(h)
    for _ in range(volume):
        pos = k
        for i in range(k - 1, -1, -1):
            if h[i] > h[pos]:
                break
            if h[i] < h[pos]:
                pos = i
        if pos == k:
            for i in range(k + 1, n):
                if h[i] > h[pos]:
                    break
                if h[i] < h[pos]:
                    pos = i
        h[pos] += 1
    return h


pourWater = solve


class Solution:
    def pourWater(self, heights, volume: int, k: int):
        return solve(heights, volume, k)
