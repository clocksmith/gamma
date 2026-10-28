"""1013. Partition Array Into Three Parts With Equal Sum (Easy).

Specification: https://leetcode.com/problems/partition-array-into-three-parts-with-equal-sum/description/
"""


def solve(arr: list[int]) -> bool:
    total = sum(arr)
    if total % 3 != 0:
        return False
    part = total // 3
    current = 0
    found = 0
    for i in range(len(arr) - 1):
        current += arr[i]
        if current == part:
            found += 1
            current = 0
            if found == 2:
                return True
    return False


class Solution:
    def canThreePartsEqualSum(self, arr: list[int]) -> bool:
        return solve(arr)
