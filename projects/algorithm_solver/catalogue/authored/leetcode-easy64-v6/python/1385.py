"""1385. Find the Distance Value Between Two Arrays (Easy).

Specification: https://leetcode.com/problems/find-the-distance-value-between-two-arrays/description/
"""


def solve(arr1: list[int], arr2: list[int], d: int) -> int:
    """O(m log m + n log m) time, O(m) space; n=len(arr1), m=len(arr2); preserve inputs."""
    values = sorted(arr2)
    result = 0
    for value in arr1:
        low, high = 0, len(values)
        while low < high:
            middle = (low + high) // 2
            if values[middle] < value - d:
                low = middle + 1
            else:
                high = middle
        if low == len(values) or values[low] > value + d:
            result += 1
    return result


class Solution:
    def findTheDistanceValue(self, arr1: list[int], arr2: list[int], d: int) -> int:
        return solve(arr1, arr2, d)
