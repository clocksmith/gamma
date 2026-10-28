def solve(arrivals, w, m):
    counts = {}
    kept = [False]*len(arrivals)
    discarded = 0
    for i, value in enumerate(arrivals):
        if i >= w and kept[i-w]:
            expired = arrivals[i-w]
            counts[expired] -= 1
        if counts.get(value, 0) == m:
            discarded += 1
        else:
            kept[i] = True
            counts[value] = counts.get(value, 0)+1
    return discarded

class Solution:
    def minArrivalsToDiscard(self, arrivals, w, m):
        return solve(arrivals, w, m)
