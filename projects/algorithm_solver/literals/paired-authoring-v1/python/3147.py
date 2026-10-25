class Solution:
    def maximumEnergy(self, energy: list[int], k: int) -> int:
        totals = energy.copy()
        best = energy[-1]
        for index in range(len(energy) - 1, -1, -1):
            if index + k < len(energy):
                totals[index] += totals[index + k]
            best = max(best, totals[index])
        return best
