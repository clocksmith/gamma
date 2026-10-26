"""1497. Check If Array Pairs Are Divisible by k: match complementary normalized remainder counts."""


def solve(arr: list[int], k: int) -> bool:
    """O(n + k) time and O(k) auxiliary space; inputs are read-only."""
    counts = [0] * k
    for value in arr:
        counts[value % k] += 1
    if counts[0] % 2:
        return False
    for remainder in range(1, (k + 1) // 2):
        if counts[remainder] != counts[k - remainder]:
            return False
    return k % 2 == 1 or counts[k // 2] % 2 == 0


class Solution:
    def canArrange(self, arr: list[int], k: int) -> bool:
        return solve(arr, k)
