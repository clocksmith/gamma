"""2070. Most Beautiful Item for Each Query: index prefix-maximum beauty by sorted price and binary search each budget."""
from bisect import bisect_right


def solve(items: list[list[int]], queries: list[int]) -> list[int]:
    """O(n log n + q log n) time and O(n + q) auxiliary and result space; inputs are read-only."""
    ordered = sorted(items, key=lambda item: item[0])
    prices = []
    beauty = []
    best = 0
    for price, value in ordered:
        prices.append(price)
        best = max(best, value)
        beauty.append(best)
    result = []
    for query in queries:
        index = bisect_right(prices, query) - 1
        result.append(beauty[index] if index >= 0 else 0)
    return result


class Solution:
    def maximumBeauty(self, items: list[list[int]], queries: list[int]) -> list[int]:
        return solve(items, queries)
