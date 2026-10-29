"""Original hack2hire:68fd2b2247bea664c0bba304; inferred public-preview contract; qualification unknown."""
def distinctGoodnessValues(arr):
    tails = {0: -1}
    for value in arr:
        for mask, last in list(tails.items()):
            if last < value:
                combined = mask | value
                if combined not in tails or value < tails[combined]:
                    tails[combined] = value
    return sorted(tails)

solve = distinctGoodnessValues

class Solution:
    distinctGoodnessValues = staticmethod(distinctGoodnessValues)
