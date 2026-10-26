"""3171. Find Subarray With Bitwise OR Closest to K.

Maintain the distinct OR values of subarrays ending at each index; O(n*B) expected time and O(B) space. Inputs are preserved.
"""

def solve(nums: list[int], k: int) -> int:
    ending = set()
    answer = float('inf')
    for value in nums:
        ending = {value} | {previous | value for previous in ending}
        answer = min(answer, min(abs(current - k) for current in ending))
        if answer == 0:
            return 0
    return answer


class Solution:
    def minimumDifference(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
