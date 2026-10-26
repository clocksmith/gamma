"""1524. Number of Sub-arrays With Odd Sum: count earlier prefix sums whose parity differs from the current prefix."""


def solve(arr: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    counts = [1, 0]
    parity = total = 0
    for value in arr:
        parity = (parity + value) % 2
        total = (total + counts[1 - parity]) % modulus
        counts[parity] += 1
    return total


class Solution:
    def numOfSubarrays(self, arr: list[int]) -> int:
        return solve(arr)
