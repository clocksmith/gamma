"""3224. Minimum Array Changes to Make Differences Equal: sweep the zero-change and one-change difference ranges of mirrored pairs."""


def solve(nums: list[int], k: int) -> int:
    """O(n + k) time and O(k) auxiliary space; inputs are read-only."""
    changes = [0] * (k + 2)
    pairs = len(nums) // 2
    for index in range(pairs):
        left = nums[index]
        right = nums[-1 - index]
        difference = abs(left - right)
        one_change_limit = max(left, right, k - left, k - right)
        changes[0] -= 1
        changes[one_change_limit + 1] += 1
        changes[difference] -= 1
        changes[difference + 1] += 1
    running = best = 2 * pairs
    for difference in range(k + 1):
        running += changes[difference]
        best = min(best, running)
    return best


class Solution:
    def minChanges(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
