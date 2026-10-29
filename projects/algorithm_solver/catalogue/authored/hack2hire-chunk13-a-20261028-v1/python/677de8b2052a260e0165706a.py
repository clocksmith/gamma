"""Hack2Hire 677de8b2052a260e0165706a (Organize Books to Shelves) over an INFERRED spec; qualification unknown."""


def solve(numShelves, limit):
    # Counts stay non-increasing by shelf index, so the target for a prefix is the first shelf holding count[limit - 1].
    count = [0] * numShelves
    first = {0: 0}  # count value -> smallest shelf index holding it
    out = []
    for lim in limit:
        v = count[lim - 1]
        j = first[v]
        out.append(j)
        count[j] = v + 1
        if j + 1 < numShelves and count[j + 1] == v:
            first[v] = j + 1
        else:
            del first[v]
        if v + 1 not in first:
            first[v + 1] = j
    return out


class Solution:
    def organizeBooks(self, numShelves, limit):
        return solve(numShelves, limit)
