"""1089. Duplicate Zeros (Easy).

Specification: https://leetcode.com/problems/duplicate-zeros/description/
"""


def solve(arr: list[int]) -> list[int]:
    result = []
    for value in arr:
        if len(result) >= len(arr):
            break
        result.append(value)
        if value == 0 and len(result) < len(arr):
            result.append(0)
    return result


class Solution:
    def duplicateZeros(self, arr: list[int]) -> None:
        # Backward virtual positions preserve unread input; constant auxiliary space.
        zeros = arr.count(0)
        size = len(arr)
        for read in range(size - 1, -1, -1):
            value = arr[read]
            write = read + zeros
            if write < size:
                arr[write] = value
            if value == 0:
                zeros -= 1
                if read + zeros < size:
                    arr[read + zeros] = 0
