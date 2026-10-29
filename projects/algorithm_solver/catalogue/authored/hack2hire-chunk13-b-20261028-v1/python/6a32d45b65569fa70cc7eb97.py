"""Hack2Hire 6a32d45b65569fa70cc7eb97 (Shift Units Protection) over an INFERRED spec; qualification unknown."""


def solve(population, unit):
    n = len(unit)
    total = 0
    i = 0
    while i < n:
        if unit[i] != '1':
            i += 1
            continue
        j = i
        run_sum = 0
        run_min = None
        while j < n and unit[j] == '1':
            run_sum += population[j]
            run_min = population[j] if run_min is None else min(run_min, population[j])
            j += 1
        if i > 0:
            total += run_sum + population[i - 1] - min(run_min, population[i - 1])
        else:
            total += run_sum
        i = j
    return total


class Solution:
    def maxProtectedPopulation(self, population, unit):
        return solve(population, unit)
