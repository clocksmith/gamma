"""2968. Apply Operations to Maximize Frequency Score.

Sorted sliding windows with exact median conversion costs; O(n log n) time, O(n) space. Inputs are preserved.
"""

def solve(nums: list[int], k: int) -> int:
    values = sorted(nums)
    prefix = [0]
    for value in values:
        prefix.append(prefix[-1] + value)

    def cost(left, right):
        middle = (left + right) // 2
        return (values[middle] * (middle - left) - prefix[middle] + prefix[left]
                + prefix[right + 1] - prefix[middle + 1] - values[middle] * (right - middle))

    left = answer = 0
    for right in range(len(values)):
        while cost(left, right) > k:
            left += 1
        answer = max(answer, right - left + 1)
    return answer


class Solution:
    def maxFrequencyScore(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
