"""2809. Minimum Time to Make Array Sum At Most x. Order resets by growth and maximize saved value for each reset count."""


def solve(nums1: list[int], nums2: list[int], x: int) -> int:
    """O(n^2) time and O(n) space. Inputs are preserved."""
    size = len(nums1)
    ordered = sorted(zip(nums2, nums1))
    saved = [0] + [float("-inf")] * size
    for index, (growth, initial) in enumerate(ordered):
        for resets in range(index + 1, 0, -1):
            saved[resets] = max(saved[resets], saved[resets - 1] + initial + growth * resets)
    initial_sum = sum(nums1)
    growth_sum = sum(nums2)
    for elapsed in range(size + 1):
        if initial_sum + elapsed * growth_sum - saved[elapsed] <= x:
            return elapsed
    return -1


class Solution:
    def minimumTime(self, nums1: list[int], nums2: list[int], x: int) -> int:
        return solve(nums1, nums2, x)
