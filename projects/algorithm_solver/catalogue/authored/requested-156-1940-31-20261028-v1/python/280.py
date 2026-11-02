"""Original frontend 280 variant; qualification unknown."""


def solve(nums):
    arr = list(nums)
    for i in range(len(arr) - 1):
        if (i % 2 == 0 and arr[i] > arr[i + 1]) or (i % 2 == 1 and arr[i] < arr[i + 1]):
            arr[i], arr[i + 1] = arr[i + 1], arr[i]
    return arr


def wiggleSort(nums):
    """Official LeetCode ABI (in_place_arg 0): rewrites nums in place, returns None.

    The slice assignment of the pure result is charged as O(n) time and O(n)
    auxiliary space (the intermediate list from solve).
    """
    nums[:] = solve(nums)


class Solution:
    def wiggleSort(self, nums):
        wiggleSort(nums)
