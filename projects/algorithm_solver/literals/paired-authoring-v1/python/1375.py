class Solution:
    def numTimesAllBlue(self, flips: list[int]) -> int:
        largest = 0
        count = 0
        for step, position in enumerate(flips, 1):
            largest = max(largest, position)
            if largest == step:
                count += 1
        return count
