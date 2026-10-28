"""Original frontend 3741 development candidate; qualification unknown."""

def solve(nums):
    recent = {}
    best = len(nums) * 2 + 1
    for index, value in enumerate(nums):
        pair = recent.get(value, [])
        if len(pair) == 2:
            best = min(best, 2 * (index - pair[0]))
        recent[value] = (pair + [index])[-2:]
    return best if best <= len(nums) * 2 else -1


class Solution:
    def minimumDistance(self, nums):
        return solve(nums)
