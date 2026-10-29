# 354 — Russian Doll Envelopes. Original implementation; authored candidate, not independently qualified.
def solve(envelopes):
    from bisect import bisect_left
    tails = []
    # Equal widths must not be chained by the height LIS.
    for _, height in sorted(envelopes, key=lambda pair: (pair[0], -pair[1])):
        i = bisect_left(tails, height)
        if i == len(tails):
            tails.append(height)
        else:
            tails[i] = height
    return len(tails)

maxEnvelopes = solve

class Solution:
    maxEnvelopes = staticmethod(solve)
