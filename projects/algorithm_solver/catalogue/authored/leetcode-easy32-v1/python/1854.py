"""1854. Maximum Population Year (Easy).

Specification: https://leetcode.com/problems/maximum-population-year/description/
"""


def solve(logs: list[list[int]]) -> int:
    """O(n + Y) time, O(Y) space; Y = 100, with exclusive death years."""
    first_year = 1950
    last_year = 2050
    changes = [0] * (last_year - first_year + 1)
    for birth, death in logs:
        changes[birth - first_year] += 1
        changes[death - first_year] -= 1
    population = 0
    best_population = 0
    best_year = first_year
    for year in range(first_year, last_year):
        population += changes[year - first_year]
        if population > best_population:
            best_population = population
            best_year = year
    return best_year


class Solution:
    def maximumPopulation(self, logs: list[list[int]]) -> int:
        return solve(logs)
