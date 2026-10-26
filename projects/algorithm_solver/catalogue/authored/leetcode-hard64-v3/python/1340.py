"""1340. Jump Game V: height-ordered dynamic programming; O(n log n + n*d) time and O(n) space."""


def solve(arr: list[int], d: int) -> int:
    best = [1] * len(arr)
    for index in sorted(range(len(arr)), key=arr.__getitem__):
        for direction in (-1, 1):
            for distance in range(1, d + 1):
                neighbor = index + direction * distance
                if not 0 <= neighbor < len(arr) or arr[neighbor] >= arr[index]:
                    break
                best[index] = max(best[index], 1 + best[neighbor])
    return max(best)


class Solution:
    def maxJumps(self, arr: list[int], d: int) -> int:
        return solve(arr, d)
