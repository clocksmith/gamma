"""3040. Maximum Number of Operations With the Same Score II: evaluate the three possible scores with rolling interval-DP diagonals."""


def solve(nums: list[int]) -> int:
    """O(n * n) time and O(n) auxiliary space; inputs are read-only."""
    size = len(nums)
    scores = {nums[0] + nums[1], nums[-2] + nums[-1], nums[0] + nums[-1]}
    best = 0
    for score in scores:
        previous = [0] * (size + 1)
        for length in range(2 + size % 2, size + 1, 2):
            current = [0] * (size - length + 1)
            for left in range(size - length + 1):
                right = left + length - 1
                count = 0
                if nums[left] + nums[left + 1] == score:
                    count = max(count, 1 + previous[left + 2])
                if nums[left] + nums[right] == score:
                    count = max(count, 1 + previous[left + 1])
                if nums[right - 1] + nums[right] == score:
                    count = max(count, 1 + previous[left])
                current[left] = count
            previous = current
        best = max(best, previous[0])
    return best


class Solution:
    def maxOperations(self, nums: list[int]) -> int:
        return solve(nums)
