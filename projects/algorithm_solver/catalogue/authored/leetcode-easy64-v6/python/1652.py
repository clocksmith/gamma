"""1652. Defuse the Bomb (Easy).

Specification: https://leetcode.com/problems/defuse-the-bomb/description/
"""


def solve(code: list[int], k: int) -> list[int]:
    """O(n) time, O(1) auxiliary space besides the fresh result; preserve code."""
    size = len(code)
    result = [0] * size
    if k == 0:
        return result
    left = 1 if k > 0 else size + k
    right = k if k > 0 else size - 1
    window_sum = 0
    for index in range(left, right + 1):
        window_sum += code[index % size]
    for index in range(size):
        result[index] = window_sum
        if index + 1 < size:
            window_sum -= code[left % size]
            left += 1
            right += 1
            window_sum += code[right % size]
    return result


class Solution:
    def decrypt(self, code: list[int], k: int) -> list[int]:
        return solve(code, k)
