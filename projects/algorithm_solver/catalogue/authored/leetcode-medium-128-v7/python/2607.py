"""2607. Make K-Subarray Sums Equal: equalize each modular index cycle to its median."""
from math import gcd


def solve(arr: list[int], k: int) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    groups = gcd(len(arr), k)
    operations = 0
    for start in range(groups):
        values = sorted(arr[start::groups])
        median = values[len(values) // 2]
        operations += sum(abs(value - median) for value in values)
    return operations


class Solution:
    def makeSubKSumEqual(self, arr: list[int], k: int) -> int:
        return solve(arr, k)
