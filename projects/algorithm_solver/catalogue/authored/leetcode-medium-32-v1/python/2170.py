"""2170. Minimum Operations to Make the Array Alternating: keep the best distinct values for the two index parities."""


def solve(nums: list[int]) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    counts = [{}, {}]
    for index, value in enumerate(nums):
        group = counts[index % 2]
        group[value] = group.get(value, 0) + 1

    def top_two(group: dict[int, int]) -> tuple[tuple[int | None, int], tuple[int | None, int]]:
        first = (None, 0)
        second = (None, 0)
        for value, count in group.items():
            if count > first[1]:
                first, second = (value, count), first
            elif count > second[1]:
                second = (value, count)
        return first, second

    even_first, even_second = top_two(counts[0])
    odd_first, odd_second = top_two(counts[1])
    if even_first[0] != odd_first[0]:
        kept = even_first[1] + odd_first[1]
    else:
        kept = max(even_first[1] + odd_second[1], even_second[1] + odd_first[1])
    return len(nums) - kept


class Solution:
    def minimumOperations(self, nums: list[int]) -> int:
        return solve(nums)
