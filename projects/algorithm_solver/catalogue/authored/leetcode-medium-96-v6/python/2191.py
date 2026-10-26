"""2191. Sort the Jumbled Numbers: sort by mapped digit values and retain original indices for stable ties."""


def solve(mapping: list[int], nums: list[int]) -> list[int]:
    """O(n d + n log n) time and O(n) auxiliary and result space for at most d digits; inputs are read-only."""
    def mapped(value: int) -> int:
        if value == 0:
            return mapping[0]
        place = 1
        result = 0
        while value:
            value, digit = divmod(value, 10)
            result += mapping[digit] * place
            place *= 10
        return result

    ordered = sorted(range(len(nums)), key=lambda index: (mapped(nums[index]), index))
    return [nums[index] for index in ordered]


class Solution:
    def sortJumbled(self, mapping: list[int], nums: list[int]) -> list[int]:
        return solve(mapping, nums)
