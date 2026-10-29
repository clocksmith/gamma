"""Hack2Hire 697460b3a0697bac5fdca97e (Distinct Wall Crossing on Number Line) over an INFERRED spec; qualification unknown."""


def best_for(first, second, energy):
    # first side is crossed twice (there and back), second side once
    best = 0
    j = len(second) - 1
    for i in range(len(first)):
        if 2 * first[i] > energy:
            break
        while j > 0 and 2 * first[i] + second[j] > energy:
            j -= 1
        best = max(best, i + j)
    return best


def solve(energy, positions, costs):
    right = sorted((p, c) for p, c in zip(positions, costs) if p > 0)
    left = sorted(((-p, c) for p, c in zip(positions, costs) if p < 0))
    pr = [0]
    for _, c in right:
        pr.append(pr[-1] + c)
    pl = [0]
    for _, c in left:
        pl.append(pl[-1] + c)
    return max(best_for(pr, pl, energy), best_for(pl, pr, energy))


class Solution:
    def maxDistinctWalls(self, energy, positions, costs):
        return solve(energy, positions, costs)
