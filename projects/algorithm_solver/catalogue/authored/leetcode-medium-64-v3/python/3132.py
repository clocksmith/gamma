"""3132. Find the Integer Added to Array II: try the three possible retained minima and verify sorted subsequence matches."""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    first = sorted(nums1)
    second = sorted(nums2)
    best = float('inf')
    for start in range(3):
        difference = second[0] - first[start]
        matched = 0
        removed = 0
        for value in first:
            if matched < len(second) and value + difference == second[matched]:
                matched += 1
            else:
                removed += 1
                if removed > 2:
                    break
        if matched == len(second) and removed == 2:
            best = min(best, difference)
    return best


class Solution:
    def minimumAddedInteger(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
