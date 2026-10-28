"""1196. How Many Apples Can You Put into the Basket (Easy).

Specification: https://leetcode.com/problems/how-many-apples-can-you-put-into-the-basket/description/
"""


def solve(weight: list[int]) -> int:
    ordered = sorted(weight)
    total = 0
    count = 0
    for value in ordered:
        if total + value > 5000:
            break
        total += value
        count += 1
    return count


class Solution:
    def maxNumberOfApples(self, weight: list[int]) -> int:
        return solve(weight)
