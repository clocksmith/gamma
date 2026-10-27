"""179. Largest Number."""
from functools import cmp_to_key

def solve(nums: list[int]) -> str:
    values = list(map(str, nums))
    values.sort(key=cmp_to_key(lambda left, right: -1 if left + right > right + left else 1 if left + right < right + left else 0))
    result = ''.join(values)
    return '0' if result and result[0] == '0' else result

class Solution:
    def largestNumber(self, nums: list[int]) -> str:
        return solve(nums)
