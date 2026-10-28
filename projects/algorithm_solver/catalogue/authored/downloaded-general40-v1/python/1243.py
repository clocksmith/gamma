"""1243. Array Transformation (Easy).

Specification: https://leetcode.com/problems/array-transformation/description/
"""


def solve(arr: list[int]) -> list[int]:
    current = arr[:]
    while True:
        nxt = current[:]
        for i in range(1, len(current) - 1):
            if current[i] < current[i - 1] and current[i] < current[i + 1]:
                nxt[i] = current[i] + 1
            elif current[i] > current[i - 1] and current[i] > current[i + 1]:
                nxt[i] = current[i] - 1
        changed = any(nxt[i] != current[i] for i in range(len(current)))
        current = nxt
        if not changed:
            break
    return current


class Solution:
    def transformArray(self, arr: list[int]) -> list[int]:
        return solve(arr)
