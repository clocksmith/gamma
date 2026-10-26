"""2023. Number of Pairs of Strings With Concatenation Equal to Target: count ordered prefix-suffix pairs and exclude pairing an index with itself."""


def solve(nums: list[str], target: str) -> int:
    """O(S + L^2) expected time and O(S + L) space for S input characters and target length L; inputs are read-only."""
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    answer = 0
    for split in range(1, len(target)):
        left, right = target[:split], target[split:]
        left_count, right_count = counts.get(left, 0), counts.get(right, 0)
        answer += left_count * right_count
        if left == right:
            answer -= left_count
    return answer


class Solution:
    def numOfPairs(self, nums: list[str], target: str) -> int:
        return solve(nums, target)
