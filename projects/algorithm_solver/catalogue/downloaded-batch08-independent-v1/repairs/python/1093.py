"""1093. Statistics from a Large Sample (Medium).

Specification: https://leetcode.com/problems/statistics-from-a-large-sample/description/
"""


def solve(count: list[int]) -> list[float]:
    total = 0
    total_sum = 0
    minimum = -1
    maximum = -1
    mode = -1
    mode_count = -1
    for i, value in enumerate(count):
        if value > 0:
            if minimum == -1:
                minimum = i
            maximum = i
            if value > mode_count:
                mode_count = value
                mode = i
        total += value
        total_sum += value * i
    mean = total_sum / total
    first_middle = (total + 1) // 2
    second_middle = total // 2 + 1
    cumulative = 0
    first_value = -1
    second_value = -1
    for i, value in enumerate(count):
        cumulative += value
        if first_value == -1 and cumulative >= first_middle:
            first_value = i
        if second_value == -1 and cumulative >= second_middle:
            second_value = i
    median = (first_value + second_value) / 2
    return [minimum, maximum, mean, median, mode]


class Solution:
    def sampleStats(self, count: list[int]) -> list[float]:
        return solve(count)
