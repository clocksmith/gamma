"""3265. Count Almost Equal Pairs I (Medium).

Specification: https://leetcode.com/problems/count-almost-equal-pairs-i/description/
"""


def solve(nums: list[int]) -> int:
    max_len = max(len(str(x)) for x in nums)
    count = {}
    ans = 0
    for num in nums:
        digits = list(str(num).rjust(max_len, '0'))
        variants = {num}
        for i in range(len(digits)):
            for j in range(i + 1, len(digits)):
                copy = digits[:]
                copy[i], copy[j] = copy[j], copy[i]
                variants.add(int(''.join(copy)))
        for v in variants:
            ans += count.get(v, 0)
        count[num] = count.get(num, 0) + 1
    return ans


class Solution:
    def countPairs(self, nums: list[int]) -> int:
        return solve(nums)
