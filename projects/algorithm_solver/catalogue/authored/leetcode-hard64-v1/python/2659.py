"""2659. Make Array Empty: sorted removal order and remaining-length charges at wraps."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; the problem requires distinct values. Inputs are preserved."""
    length = len(nums)
    order = sorted(range(length), key=nums.__getitem__)
    answer = length
    for position in range(1, length):
        if order[position] < order[position - 1]:
            answer += length - position
    return answer


class Solution:
    def countOperationsToEmptyArray(self, nums: list[int]) -> int:
        return solve(nums)
