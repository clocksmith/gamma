"""2499. Minimum Total Cost to Make Arrays Unequal. Balance the dominant equal-position value using the cheapest eligible indices."""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n) time and O(n) space. Inputs are preserved."""
    counts = {}
    selected = 0
    dominant = None
    maximum = 0
    answer = 0
    for index, (first, second) in enumerate(zip(nums1, nums2)):
        if first != second:
            continue
        selected += 1
        answer += index
        counts[first] = counts.get(first, 0) + 1
        if counts[first] > maximum:
            maximum = counts[first]
            dominant = first
    for index, (first, second) in enumerate(zip(nums1, nums2)):
        if selected >= 2 * maximum:
            return answer
        if first != second and first != dominant and second != dominant:
            selected += 1
            answer += index
    return answer if selected >= 2 * maximum else -1


class Solution:
    def minimumTotalCost(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
