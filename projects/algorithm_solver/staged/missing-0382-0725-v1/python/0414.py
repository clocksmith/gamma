"""414. Third Maximum Number. Keep only the three largest distinct values."""

def solve(nums: list[int]) -> int:
    top = []
    for value in nums:
        if value not in top:
            top.append(value)
            top.sort(reverse=True)
            if len(top) > 3:
                top.pop()
    return top[2] if len(top) == 3 else top[0]


class Solution:
    def thirdMax(self, nums: list[int]) -> int:
        return solve(nums)
