class Solution:
    def maximumElementAfterDecrementingAndRearranging(self, arr: list[int]) -> int:
        ordered = sorted(arr)
        largest = 0
        for value in ordered:
            largest = min(value, largest + 1)
        return largest
