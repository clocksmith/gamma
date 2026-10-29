"""Original frontend 805 variant; qualification not qualified."""

def solve(nums):
    n = len(nums)
    if n < 2:
        return False
    total = sum(nums)
    scaled = [x * n - total for x in nums]
    half = n // 2
    left, right = scaled[:half], scaled[half:]

    def subset_sums(values):
        sums = [0]
        for x in values:
            sums += [s + x for s in sums]
        return sums

    left_sums = subset_sums(left)
    right_sums = subset_sums(right)
    # Index 0 is the empty subset; the last index is the full half.
    if 0 in left_sums[1:] or 0 in right_sums[1:]:
        return True
    left_proper = set(left_sums[1:-1])
    for s in right_sums[1:]:
        if -s in left_proper:
            return True
    return False


class Solution:
    def splitArraySameAverage(self, nums):
        return solve(nums)
