"""3505. Minimum Operations to Make Elements Within K Subarrays Equal.

Fenwick order statistics give sliding median costs; a second dynamic program selects disjoint windows; O(n log n+n*k) time and O(n) space. Inputs are preserved.
"""

def solve(nums: list[int], x: int, k: int) -> int:
    values = sorted(set(nums))
    rank = {value: index + 1 for index, value in enumerate(values)}
    size = len(values)
    counts, sums = [0] * (size + 1), [0] * (size + 1)

    def change(value, difference):
        index = rank[value]
        while index <= size:
            counts[index] += difference
            sums[index] += difference * value
            index += index & -index

    def median_prefix(amount):
        index = count = total = 0
        step = 1 << (size.bit_length() - 1)
        while step:
            following = index + step
            if following <= size and count + counts[following] < amount:
                index = following
                count += counts[following]
                total += sums[following]
            step >>= 1
        return values[index], count, total

    window_cost = [0] * (len(nums) - x + 1)
    total = 0
    for index, value in enumerate(nums):
        change(value, 1)
        total += value
        if index >= x:
            change(nums[index - x], -1)
            total -= nums[index - x]
        if index + 1 >= x:
            median, below, below_sum = median_prefix((x + 1) // 2)
            window_cost[index - x + 1] = median * below - below_sum + total - below_sum - median * (x - below)
    previous = [0] * (len(nums) + 1)
    for selected in range(1, k + 1):
        current = [float('inf')] * (len(nums) + 1)
        for end in range(selected * x, len(nums) + 1):
            current[end] = min(current[end - 1], previous[end - x] + window_cost[end - x])
        previous = current
    return previous[-1]


class Solution:
    def minOperations(self, nums: list[int], x: int, k: int) -> int:
        return solve(nums, x, k)
