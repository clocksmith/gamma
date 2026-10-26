"""3886. Sum of Sortable Integers."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n*tau(n) + sqrt(n)) time and O(tau(n)) space; each block must have at most one cyclic descent and ordered value ranges."""
    n = len(nums)
    divisors = []
    value = 1
    while value * value <= n:
        if n % value == 0:
            divisors.append(value)
            if value * value != n:
                divisors.append(n // value)
        value += 1
    answer = 0
    for width in divisors:
        previous_max = 0
        possible = True
        for start in range(0, n, width):
            end = start + width
            minimum = maximum = nums[start]
            descents = int(nums[end - 1] > nums[start])
            for index in range(start + 1, end):
                minimum = min(minimum, nums[index])
                maximum = max(maximum, nums[index])
                if nums[index - 1] > nums[index]:
                    descents += 1
            if descents > 1 or minimum < previous_max:
                possible = False
                break
            previous_max = maximum
        if possible:
            answer += width
    return answer


class Solution:
    def sumOfSortableIntegers(self, nums: list[int]) -> int:
        return solve(nums)
