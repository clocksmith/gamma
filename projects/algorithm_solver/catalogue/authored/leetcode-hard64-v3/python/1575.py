"""1575. Count All Possible Routes: bottom-up remaining-fuel DP on distinct locations; O(fuel*n^2) time and O(fuel*n) space."""


def solve(locations: list[int], start: int, finish: int, fuel: int) -> int:
    modulus = 1_000_000_007
    size = len(locations)
    ways = [[0] * size for _ in range(fuel + 1)]
    for remaining in range(fuel + 1):
        for city in range(size):
            count = int(city == finish)
            for neighbor in range(size):
                if neighbor == city:
                    continue
                cost = abs(locations[city] - locations[neighbor])
                if cost <= remaining:
                    count = (count + ways[remaining - cost][neighbor]) % modulus
            ways[remaining][city] = count
    return ways[fuel][start]


class Solution:
    def countRoutes(self, locations: list[int], start: int, finish: int, fuel: int) -> int:
        return solve(locations, start, finish, fuel)
