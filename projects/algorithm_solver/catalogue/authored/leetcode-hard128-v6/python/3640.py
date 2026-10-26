"""3640. Trionic Array II.

Track nonempty increasing, decreasing-after-increasing, and final increasing phases; O(n) time and O(1) space. Each phase requires an edge. Inputs are preserved.
"""

def solve(nums: list[int]) -> int:
    increasing = decreasing = final = float('-inf')
    answer = float('-inf')
    for index in range(1, len(nums)):
        previous, value = nums[index - 1], nums[index]
        if value > previous:
            next_increasing = max(previous + value, increasing + value)
            next_final = max(decreasing, final) + value
            increasing, decreasing, final = next_increasing, float('-inf'), next_final
        elif value < previous:
            decreasing = max(increasing, decreasing) + value
            increasing = final = float('-inf')
        else:
            increasing = decreasing = final = float('-inf')
        answer = max(answer, final)
    return answer


class Solution:
    def maxSumTrionic(self, nums: list[int]) -> int:
        return solve(nums)
