class Solution:
    def minElements(self, nums: list[int], limit: int, goal: int) -> int:
        total = sum(nums)
        gap = abs(goal - total)
        quotient = gap // limit
        remainder = gap % limit
        return quotient + (1 if remainder else 0)
