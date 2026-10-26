"""1744. Can You Eat Your Favorite Candy on Your Favorite Day?: intersect the possible consumption range with each candy-type interval."""


def solve(candiesCount: list[int], queries: list[list[int]]) -> list[bool]:
    """O(n + q) time and O(n + q) space, with n candy types and q queries; inputs are read-only."""
    prefix = [0]
    for count in candiesCount:
        prefix.append(prefix[-1] + count)
    result = []
    for kind, day, cap in queries:
        # Division avoids forming a potentially much larger day * cap product.
        result.append(day < prefix[kind + 1] and prefix[kind] // cap <= day)
    return result


class Solution:
    def canEat(self, candiesCount: list[int], queries: list[list[int]]) -> list[bool]:
        return solve(candiesCount, queries)
