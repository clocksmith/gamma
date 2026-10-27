"""3636. Threshold Majority Queries.

Specification: https://leetcode.com/problems/threshold-majority-queries/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(q log q + (n + q) sqrt(n) log n) time, O(n + q) space; exact Mo ordering and frequency-winner segment tree.
Inputs are not modified.
Returns the smallest value among the highest-frequency elements only when its count reaches the threshold. No randomized majority assumption. Runtime bounds remain unmeasured.
"""

from math import isqrt

def solve(nums, queries):
    values = sorted(set(nums))
    ranks = {value: index for index, value in enumerate(values)}
    encoded = [ranks[value] for value in nums]
    frequencies = [0] * len(values)
    capacity = 1
    while capacity < len(values):
        capacity *= 2
    winners = [-1] * (2 * capacity)
    for index in range(len(values)):
        winners[capacity + index] = index

    def better(first, second):
        if first < 0:
            return second
        if second < 0:
            return first
        if frequencies[first] != frequencies[second]:
            return first if frequencies[first] > frequencies[second] else second
        return min(first, second)

    for node in range(capacity - 1, 0, -1):
        winners[node] = better(winners[2 * node], winners[2 * node + 1])

    def change(position, delta):
        rank = encoded[position]
        frequencies[rank] += delta
        node = (capacity + rank) // 2
        while node:
            winners[node] = better(winners[2 * node], winners[2 * node + 1])
            node //= 2

    block_size = max(1, isqrt(len(nums)))
    order = list(range(len(queries)))
    order.sort(key=lambda index: (queries[index][0] // block_size,
                                  queries[index][1] if (queries[index][0] // block_size) % 2 == 0 else -queries[index][1]))
    answers = [-1] * len(queries)
    left, right = 0, -1
    for index in order:
        start, end, threshold = queries[index]
        while left > start:
            left -= 1
            change(left, 1)
        while right < end:
            right += 1
            change(right, 1)
        while left < start:
            change(left, -1)
            left += 1
        while right > end:
            change(right, -1)
            right -= 1
        winner = winners[1]
        if frequencies[winner] >= threshold:
            answers[index] = values[winner]
    return answers


class Solution:
    def subarrayMajority(self, nums, queries):
        return solve(nums, queries)
