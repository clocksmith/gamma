"""2653. Sliding Subarray Beauty: count negative values in each fixed window and locate the xth smallest."""


def solve(nums: list[int], k: int, x: int) -> list[int]:
    """O(50 * n) time and O(n + 50) auxiliary space including the result; inputs are read-only."""
    counts = [0] * 50
    result = []
    for right, value in enumerate(nums):
        if value < 0:
            counts[value + 50] += 1
        if right >= k and nums[right - k] < 0:
            counts[nums[right - k] + 50] -= 1
        if right + 1 < k:
            continue
        needed = x
        beauty = 0
        for code, count in enumerate(counts):
            needed -= count
            if needed <= 0:
                beauty = code - 50
                break
        result.append(beauty)
    return result


class Solution:
    def getSubarrayBeauty(self, nums: list[int], k: int, x: int) -> list[int]:
        return solve(nums, k, x)
