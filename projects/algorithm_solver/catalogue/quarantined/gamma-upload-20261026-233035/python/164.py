"""164. Maximum Gap."""
def solve(nums: list[int]) -> int:
    if len(nums) < 2:
        return 0
    minimum, maximum = min(nums), max(nums)
    if minimum == maximum:
        return 0
    size = max(1, (maximum - minimum) // (len(nums) - 1))
    count = (maximum - minimum) // size + 1
    lows = [None] * count
    highs = [None] * count
    for value in nums:
        index = (value - minimum) // size
        lows[index] = value if lows[index] is None else min(lows[index], value)
        highs[index] = value if highs[index] is None else max(highs[index], value)
    best = 0
    previous = minimum
    for low, high in zip(lows, highs):
        if low is not None:
            best = max(best, low - previous)
            previous = high
    return best

class Solution:
    def maximumGap(self, nums: list[int]) -> int:
        return solve(nums)
