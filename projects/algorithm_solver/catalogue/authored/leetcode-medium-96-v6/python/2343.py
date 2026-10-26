"""2343. Query Kth Smallest Trimmed Number: answer queries during stable least-significant-digit sorting."""


def solve(nums: list[str], queries: list[list[int]]) -> list[int]:
    """O((n + 10) T + q) time and O(n + q + T) space for maximum requested trim T; inputs are read-only."""
    maximum_trim = max(trim for _, trim in queries)
    by_trim = [[] for _ in range(maximum_trim + 1)]
    for index, (rank, trim) in enumerate(queries):
        by_trim[trim].append((rank, index))
    order = list(range(len(nums)))
    result = [0] * len(queries)
    width = len(nums[0])
    for trim in range(1, maximum_trim + 1):
        buckets = [[] for _ in range(10)]
        column = width - trim
        for index in order:
            buckets[ord(nums[index][column]) - ord('0')].append(index)
        order = [index for bucket in buckets for index in bucket]
        for rank, query_index in by_trim[trim]:
            result[query_index] = order[rank - 1]
    return result


class Solution:
    def smallestTrimmedNumbers(self, nums: list[str], queries: list[list[int]]) -> list[int]:
        return solve(nums, queries)
