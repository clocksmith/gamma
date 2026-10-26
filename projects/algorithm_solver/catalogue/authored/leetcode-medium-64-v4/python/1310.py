"""1310. XOR Queries of a Subarray: cancel the prefix before each query interval."""


def solve(arr: list[int], queries: list[list[int]]) -> list[int]:
    """O(n + q) time and O(n) auxiliary space excluding the result; inputs are read-only."""
    prefix = [0]
    for value in arr:
        prefix.append(prefix[-1] ^ value)
    return [prefix[right + 1] ^ prefix[left] for left, right in queries]


class Solution:
    def xorQueries(self, arr: list[int], queries: list[list[int]]) -> list[int]:
        return solve(arr, queries)
