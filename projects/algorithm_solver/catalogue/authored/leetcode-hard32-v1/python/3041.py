"""3041. Maximize Consecutive Elements in an Array After Modification."""

def solve(nums: list[int]) -> int:
    """O(n log n) time, O(n) space; both transitions read the state before this element."""
    longest = {}
    answer = 0
    for value in sorted(nums):
        unchanged = longest.get(value - 1, 0) + 1
        increased = longest.get(value, 0) + 1
        longest[value + 1] = max(longest.get(value + 1, 0), increased)
        longest[value] = max(longest.get(value, 0), unchanged)
        answer = max(answer, longest[value], longest[value + 1])
    return answer


class Solution:
    def maxSelectedElements(self, nums: list[int]) -> int:
        return solve(nums)
