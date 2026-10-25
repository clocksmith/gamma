"""2602. Minimum Operations to Make All Array Elements Equal: answer absolute-distance sums with sorted prefixes."""
from bisect import bisect_left


def solve(nums: list[int], queries: list[int]) -> list[int]:
    """O(n log n + q log n) time and O(n) auxiliary space excluding the result; inputs are read-only."""
    values = sorted(nums)
    prefix = [0]
    for value in values:
        prefix.append(prefix[-1] + value)
    answer = []
    for query in queries:
        split = bisect_left(values, query)
        left_cost = query * split - prefix[split]
        right_cost = prefix[-1] - prefix[split] - query * (len(values) - split)
        answer.append(left_cost + right_cost)
    return answer


class Solution:
    def minOperations(self, nums: list[int], queries: list[int]) -> list[int]:
        return solve(nums, queries)
