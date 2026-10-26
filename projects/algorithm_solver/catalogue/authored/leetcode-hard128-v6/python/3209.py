"""3209. Number of Subarrays With AND Value of K.

Merge the distinct AND values of suffixes ending at each index; O(n*B) time and O(B) space for B value bits. Inputs are preserved.
"""

def solve(nums: list[int], k: int) -> int:
    suffixes = {}
    answer = 0
    for value in nums:
        current = {value: 1}
        for previous, count in suffixes.items():
            combined = previous & value
            current[combined] = current.get(combined, 0) + count
        answer += current.get(k, 0)
        suffixes = current
    return answer


class Solution:
    def countSubarrays(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
