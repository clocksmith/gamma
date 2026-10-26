"""3762. Minimum Operations to Equalize Subarrays."""
from __future__ import annotations
from array import array


def solve(nums: list[int], k: int, queries: list[list[int]]) -> list[int]:
    """O((n + q) log n) time and O(n log n) space; persistent frequency/sum trees answer range medians."""
    scaled = [value // k for value in nums]
    values = sorted(set(scaled))
    rank = {value: index for index, value in enumerate(values)}
    left_child = array('I', [0])
    right_child = array('I', [0])
    count = array('I', [0])
    sums = array('q', [0])
    def insert(previous, low, high, position, value):
        node = len(count)
        left_child.append(left_child[previous])
        right_child.append(right_child[previous])
        count.append(count[previous] + 1)
        sums.append(sums[previous] + value)
        if low < high:
            middle = (low + high) // 2
            if position <= middle:
                left_child[node] = insert(left_child[previous], low, middle, position, value)
            else:
                right_child[node] = insert(right_child[previous], middle + 1, high, position, value)
        return node
    roots = [0]
    breaks = [0] * len(nums)
    for index, value in enumerate(scaled):
        roots.append(insert(roots[-1], 0, len(values) - 1, rank[value], value))
        if index:
            breaks[index] = breaks[index - 1] + (nums[index] % k != nums[index - 1] % k)
    answer = []
    for start, end in queries:
        if breaks[end] != breaks[start]:
            answer.append(-1)
            continue
        old, new = roots[start], roots[end + 1]
        total = sums[new] - sums[old]
        length = end - start + 1
        order = (length + 1) // 2
        low, high = 0, len(values) - 1
        below_count = below_sum = 0
        while low < high:
            middle = (low + high) // 2
            old_left, new_left = left_child[old], left_child[new]
            amount = count[new_left] - count[old_left]
            if order <= amount:
                old, new, high = old_left, new_left, middle
            else:
                order -= amount
                below_count += amount
                below_sum += sums[new_left] - sums[old_left]
                old, new, low = right_child[old], right_child[new], middle + 1
        median = values[low]
        answer.append(total - 2 * below_sum + median * (2 * below_count - length))
    return answer


class Solution:
    def minOperations(self, nums: list[int], k: int, queries: list[list[int]]) -> list[int]:
        return solve(nums, k, queries)
