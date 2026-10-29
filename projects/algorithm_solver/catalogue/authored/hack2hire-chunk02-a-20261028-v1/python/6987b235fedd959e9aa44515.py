"""Hack2Hire 6987b235fedd959e9aa44515 (IPO Share Allocation); INFERRED spec; qualification unknown."""


def solve(bids, totalShares):
    order = sorted(range(len(bids)), key=lambda i: (-bids[i][2], bids[i][3], i))
    remaining, unallotted, pos = totalShares, [], 0
    while pos < len(order):
        end = pos
        while end < len(order) and bids[order[end]][2] == bids[order[pos]][2]: end += 1
        level = order[pos:end]
        need = sum(bids[i][1] for i in level)
        if need <= remaining: remaining -= need
        else:
            for rank, i in enumerate(level):
                if rank >= remaining: unallotted.append(bids[i][0])
            remaining = 0
        pos = end
    return sorted(unallotted)


class Solution:
    def getUnallottedUsers(self, bids, totalShares):
        return solve(bids, totalShares)
