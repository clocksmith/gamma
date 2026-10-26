"""3229. Minimum Operations to Make Array Equal to Target.

Charge each new signed layer of the difference array; O(n) time and O(1) auxiliary space. Inputs are preserved.
"""

def solve(nums: list[int], target: list[int]) -> int:
    previous = 0
    answer = 0
    for before, after in zip(nums, target):
        current = after - before
        if current * previous > 0:
            answer += max(0, abs(current) - abs(previous))
        else:
            answer += abs(current)
        previous = current
    return answer


class Solution:
    def minimumOperations(self, nums: list[int], target: list[int]) -> int:
        return solve(nums, target)
