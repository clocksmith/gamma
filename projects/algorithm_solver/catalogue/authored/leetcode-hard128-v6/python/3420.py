"""3420. Count Non-Decreasing Subarrays After K Operations.

A reverse sliding window maintains raised plateaus in a monotonic deque; O(n) time and O(n) space. Inputs are preserved.
"""

from collections import deque


def solve(nums: list[int], k: int) -> int:
    plateaus = deque()
    right = len(nums) - 1
    cost = answer = 0
    for left in range(len(nums) - 1, -1, -1):
        while plateaus and nums[plateaus[-1]] < nums[left]:
            index = plateaus.pop()
            boundary = plateaus[-1] if plateaus else right + 1
            cost += (boundary - index) * (nums[left] - nums[index])
        plateaus.append(left)
        while cost > k:
            cost -= nums[plateaus[0]] - nums[right]
            if plateaus[0] == right:
                plateaus.popleft()
            right -= 1
        answer += right - left + 1
    return answer


class Solution:
    def countNonDecreasingSubarrays(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
