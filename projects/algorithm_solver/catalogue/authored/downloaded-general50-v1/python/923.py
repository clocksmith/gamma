"""923. 3Sum With Multiplicity (Medium).

Specification: https://leetcode.com/problems/3sum-with-multiplicity/description/
"""


def solve(arr: list[int], target: int) -> int:
    MOD = 1000000007
    count = [0] * 101
    for v in arr:
        count[v] += 1
    total = 0
    for i in range(101):
        for j in range(i, 101):
            k = target - i - j
            if k < j or k > 100:
                continue
            if count[i] == 0 or count[j] == 0 or count[k] == 0:
                continue
            if i == j == k:
                total = (total + count[i] * (count[i] - 1) * (count[i] - 2) // 6) % MOD
            elif i == j:
                total = (total + count[i] * (count[i] - 1) // 2 * count[k]) % MOD
            elif j == k:
                total = (total + count[i] * count[j] * (count[j] - 1) // 2) % MOD
            else:
                total = (total + count[i] * count[j] * count[k]) % MOD
    return total


class Solution:
    def threeSumMulti(self, arr: list[int], target: int) -> int:
        return solve(arr, target)
