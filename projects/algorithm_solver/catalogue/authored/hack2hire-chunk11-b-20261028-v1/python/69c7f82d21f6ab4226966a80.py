"""Hack2Hire 69c7f82d21f6ab4226966a80 (Fuel Station Queue Simulation) over an INFERRED spec; qualification unknown."""


def solve(demands, x, y, z):
    fuel = [x, y, z]
    free_at = [0, 0, 0]
    previous_start = 0
    worst = 0
    for demand in demands:
        start = -1
        for i in range(3):
            if fuel[i] >= demand:
                s = max(previous_start, free_at[i])
                if start < 0 or s < start:
                    start = s
        if start < 0:
            return -1  # fuel only decreases, so this car can never be served
        chosen = 0
        while fuel[chosen] < demand or free_at[chosen] > start:
            chosen += 1
        fuel[chosen] -= demand
        free_at[chosen] = start + demand
        previous_start = start
        if start > worst:
            worst = start
    return worst


class Solution:
    def maxWaitingTime(self, demands, x, y, z):
        return solve(demands, x, y, z)
