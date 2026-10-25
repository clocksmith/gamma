class Solution:
    def assignBikes(self, workers, bikes):
        costs = [float("inf")] * (1 << len(bikes))
        costs[0] = 0
        best = float("inf")
        for mask in range(len(costs)):
            assigned = mask.bit_count()
            if assigned == len(workers):
                best = min(best, costs[mask])
                continue
            if assigned > len(workers) or costs[mask] == float("inf"):
                continue
            worker = workers[assigned]
            for index, bike in enumerate(bikes):
                bit = 1 << index
                if mask & bit == 0:
                    distance = abs(worker[0] - bike[0]) + abs(worker[1] - bike[1])
                    next_mask = mask | bit
                    costs[next_mask] = min(costs[next_mask], costs[mask] + distance)
        return best
