"""167. Two Sum II - Input Array Is Sorted."""
def solve(numbers: list[int], target: int) -> list[int]:
    left, right = 0, len(numbers) - 1
    while left < right:
        total = numbers[left] + numbers[right]
        if total == target:
            return [left + 1, right + 1]
        if total < target:
            left += 1
        else:
            right -= 1
    return []

class Solution:
    def twoSum(self, numbers: list[int], target: int) -> list[int]:
        return solve(numbers, target)
