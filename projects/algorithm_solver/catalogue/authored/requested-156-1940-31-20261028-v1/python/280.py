"""Original frontend 280 variant; qualification unknown."""


def solve(nums):
    arr = list(nums)
    for i in range(len(arr) - 1):
        if (i % 2 == 0 and arr[i] > arr[i + 1]) or (i % 2 == 1 and arr[i] < arr[i + 1]):
            arr[i], arr[i + 1] = arr[i + 1], arr[i]
    return arr


wiggleSort = solve


class Solution:
    def wiggleSort(self, nums):
        return solve(nums)
