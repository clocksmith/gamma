"""327. Count of Range Sum."""
def solve(nums: list[int], lower: int, upper: int) -> int:
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)

    def count(values):
        if len(values) <= 1:
            return 0
        middle = len(values) // 2
        left = values[:middle]
        right = values[middle:]
        total = count(left) + count(right)
        low = high = 0
        for value in left:
            while low < len(right) and right[low] - value < lower:
                low += 1
            while high < len(right) and right[high] - value <= upper:
                high += 1
            total += high - low
        values[:] = sorted(left + right)
        return total

    return count(prefix)

class Solution:
    def countRangeSum(self, nums, lower, upper):
        return solve(nums, lower, upper)
