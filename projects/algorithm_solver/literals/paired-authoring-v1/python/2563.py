def count_bounded_pairs(values: list[int], limit: int, inclusive: bool) -> int:
    left = 0
    right = len(values) - 1
    count = 0
    while left < right:
        total = values[left] + values[right]
        if total < limit or (inclusive and total == limit):
            count += right - left
            left += 1
        else:
            right -= 1
    return count


class Solution:
    def countFairPairs(self, nums: list[int], lower: int, upper: int) -> int:
        ordered = sorted(nums)
        at_most_upper = count_bounded_pairs(ordered, upper, True)
        below_lower = count_bounded_pairs(ordered, lower, False)
        return at_most_upper - below_lower
