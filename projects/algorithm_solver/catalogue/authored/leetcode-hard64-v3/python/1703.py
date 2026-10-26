"""1703. Minimum Adjacent Swaps for K Consecutive Ones: normalized one-positions and sliding medians; O(n) time and O(n) space."""


def solve(nums: list[int], k: int) -> int:
    positions = []
    for index, value in enumerate(nums):
        if value == 1:
            positions.append(index - len(positions))
    prefix = [0]
    for value in positions:
        prefix.append(prefix[-1] + value)
    answer = float('inf')
    for left in range(len(positions) - k + 1):
        right = left + k
        middle = left + k // 2
        median = positions[middle]
        cost = median * (middle - left) - (prefix[middle] - prefix[left])
        cost += prefix[right] - prefix[middle + 1] - median * (right - middle - 1)
        answer = min(answer, cost)
    return answer


class Solution:
    def minMoves(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
