"""396. Rotate Function. Update weighted sums between rotations; O(n) time."""

def solve(nums: list[int]) -> int:
    total = sum(nums)
    current = sum(index * value for index, value in enumerate(nums))
    answer = current
    for index in range(len(nums) - 1, 0, -1):
        current += total - len(nums) * nums[index]
        answer = max(answer, current)
    return answer


class Solution:
    def maxRotateFunction(self, nums: list[int]) -> int:
        return solve(nums)
