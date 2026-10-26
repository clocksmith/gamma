"""1966. Binary Searchable Numbers in an Unsorted Array: require every earlier value to be smaller and every later value larger."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    suffix_min = [float('inf')] * (len(nums) + 1)
    for index in range(len(nums) - 1, -1, -1):
        suffix_min[index] = min(nums[index], suffix_min[index + 1])
    prefix_max = float('-inf')
    answer = 0
    for index, value in enumerate(nums):
        if prefix_max < value < suffix_min[index + 1]:
            answer += 1
        prefix_max = max(prefix_max, value)
    return answer


class Solution:
    def binarySearchableNumbers(self, nums: list[int]) -> int:
        return solve(nums)
