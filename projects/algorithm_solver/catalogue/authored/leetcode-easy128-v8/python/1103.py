"""1103. Distribute Candies to People (Easy).

Specification: https://leetcode.com/problems/distribute-candies-to-people/description/
"""


def solve(candies: int, num_people: int) -> list[int]:
    """O(num_people + sqrt(candies)) time, O(num_people) space; circulate increasing gifts."""
    result = [0] * num_people
    remaining = candies
    gift = 1
    while remaining > 0:
        given = min(gift, remaining)
        result[(gift - 1) % num_people] += given
        remaining -= given
        gift += 1
    return result


class Solution:
    def distributeCandies(self, candies: int, num_people: int) -> list[int]:
        return solve(candies, num_people)
