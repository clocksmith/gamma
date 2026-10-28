"""565. Array Nesting (Medium).

Specification: https://leetcode.com/problems/array-nesting/description/
"""


def solve(nums: list[int]) -> int:
    visited = [False] * len(nums)
    best = 0
    for start in range(len(nums)):
        if visited[start]:
            continue
        length = 0
        current = start
        while not visited[current]:
            visited[current] = True
            current = nums[current]
            length += 1
        best = max(best, length)
    return best


class Solution:
    def arrayNesting(self, nums: list[int]) -> int:
        return solve(nums)
