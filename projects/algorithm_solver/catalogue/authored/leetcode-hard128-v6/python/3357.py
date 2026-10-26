"""3357. Minimize the Maximum Adjacent Element Difference.

Binary-search the difference using extremal replacement values and missing-run feasibility; O(n log V) time and O(1) auxiliary space. Inputs are preserved.
"""

def solve(nums: list[int]) -> int:
    lower = 0
    minimum, maximum = float('inf'), float('-inf')
    for index in range(1, len(nums)):
        first, second = nums[index - 1], nums[index]
        if first != -1 and second != -1:
            lower = max(lower, abs(first - second))
        elif (first == -1) != (second == -1):
            value = max(first, second)
            minimum, maximum = min(minimum, value), max(maximum, value)
    if minimum == float('inf'):
        return lower

    def possible(difference):
        if maximum - minimum <= 2 * difference:
            return True
        first, second = minimum + difference, maximum - difference
        index = 0
        while index < len(nums):
            if nums[index] != -1:
                index += 1
                continue
            start = index
            while index < len(nums) and nums[index] == -1:
                index += 1
            endpoints = []
            if start:
                endpoints.append(nums[start - 1])
            if index < len(nums):
                endpoints.append(nums[index])
            if all(abs(value - first) <= difference for value in endpoints):
                continue
            if all(abs(value - second) <= difference for value in endpoints):
                continue
            if index - start < 2 or second - first > difference:
                return False
            if any(min(abs(value - first), abs(value - second)) > difference for value in endpoints):
                return False
        return True

    upper = max(lower, maximum - minimum)
    while lower < upper:
        middle = (lower + upper) // 2
        if possible(middle):
            upper = middle
        else:
            lower = middle + 1
    return lower


class Solution:
    def minDifference(self, nums: list[int]) -> int:
        return solve(nums)
