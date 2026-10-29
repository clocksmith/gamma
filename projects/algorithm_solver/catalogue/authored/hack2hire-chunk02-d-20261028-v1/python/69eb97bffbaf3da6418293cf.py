"""Hack2Hire 69eb97bffbaf3da6418293cf (Implement Simplified Git Diff, level 2) over an INFERRED spec; qualification unknown."""


def _unique_pairs(lines1, lo1, hi1, lines2, lo2, hi2):
    count1, count2, where = {}, {}, {}
    for i in range(lo1, hi1):
        count1[lines1[i]] = count1.get(lines1[i], 0) + 1
    for j in range(lo2, hi2):
        count2[lines2[j]] = count2.get(lines2[j], 0) + 1
        where[lines2[j]] = j
    return [(i, where[lines1[i]]) for i in range(lo1, hi1)
            if count1[lines1[i]] == 1 and count2.get(lines1[i]) == 1]


def _chain(pairs):
    """Longest chain increasing in both indices; lexicographically smallest lines1 indices among longest."""
    k = len(pairs)
    if not k:
        return []
    length = [0] * k
    tails = []  # tails[l] = largest j that starts a chain of length l+1 (scanning right to left)
    for index in range(k - 1, -1, -1):
        negated = -pairs[index][1]
        lo, hi = 0, len(tails)
        while lo < hi:
            mid = (lo + hi) // 2
            if tails[mid] < negated:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(tails):
            tails.append(negated)
        else:
            tails[lo] = negated
        length[index] = lo + 1
    best = len(tails)
    levels = [[] for _ in range(best + 1)]
    for index in range(k):
        levels[length[index]].append(index)
    chosen, last_index, last_j = [], -1, -1
    for need in range(best, 0, -1):
        group = levels[need]
        lo, hi = 0, len(group)
        while lo < hi:
            mid = (lo + hi) // 2
            if group[mid] <= last_index:
                lo = mid + 1
            else:
                hi = mid
        while pairs[group[lo]][1] <= last_j:
            lo += 1
        last_index = group[lo]
        last_j = pairs[last_index][1]
        chosen.append([pairs[last_index][0], last_j])
    return chosen


def solve(lines1, lines2):
    return _chain(_unique_pairs(lines1, 0, len(lines1), lines2, 0, len(lines2)))


class Solution:
    def uniqueCommonAnchors(self, lines1, lines2):
        return solve(lines1, lines2)
