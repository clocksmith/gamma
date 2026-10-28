"""1053. Previous Permutation With One Swap (Medium).

Specification: https://leetcode.com/problems/previous-permutation-with-one-swap/description/
"""


def solve(arr: list[int]) -> list[int]:
    result = arr[:]
    index = -1
    for i in range(len(result) - 2, -1, -1):
        if result[i] > result[i + 1]:
            index = i
            break
    if index == -1:
        return result
    best_value = float('-inf')
    best_index = -1
    for j in range(index + 1, len(result)):
        if result[j] < result[index] and result[j] > best_value:
            best_value = result[j]
            best_index = j
    result[index], result[best_index] = result[best_index], result[index]
    return result


class Solution:
    def prevPermOpt1(self, arr: list[int]) -> list[int]:
        return solve(arr)
