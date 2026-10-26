"""3875. Construct Uniform Parity Array I (Easy).

Specification: https://leetcode.com/problems/construct-uniform-parity-array-i/description/
"""


def solve(nums1: list[int]) -> bool:
    """O(1) time and space; existence follows from parity; preserve nums1."""
    # If all values are even, keep them. Otherwise keep every odd value and
    # subtract one original odd value from each even value, making all values odd.
    # The chosen odd index differs from every even index, as required.
    return True


class Solution:
    def uniformArray(self, nums1: list[int]) -> bool:
        return solve(nums1)
