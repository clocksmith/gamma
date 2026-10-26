"""1224. Maximum Equal Frequency.

Track frequencies and the number of values at each frequency; O(n) time and O(n) space. Inputs are preserved.
"""

def solve(nums: list[int]) -> int:
    counts = {}
    frequencies = {}
    largest = answer = 0
    for length, value in enumerate(nums, 1):
        old = counts.get(value, 0)
        if old:
            frequencies[old] -= 1
        counts[value] = old + 1
        frequencies[old + 1] = frequencies.get(old + 1, 0) + 1
        largest = max(largest, old + 1)
        if (largest == 1 or
                largest * frequencies.get(largest, 0) + 1 == length and frequencies.get(1, 0) == 1 or
                (largest - 1) * (frequencies.get(largest - 1, 0) + 1) + 1 == length and frequencies[largest] == 1):
            answer = length
    return answer


class Solution:
    def maxEqualFreq(self, nums: list[int]) -> int:
        return solve(nums)
