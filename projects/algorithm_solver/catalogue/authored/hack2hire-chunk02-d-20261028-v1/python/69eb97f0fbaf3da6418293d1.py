"""Hack2Hire 69eb97f0fbaf3da6418293d1 (Implement Simplified Git Diff, level 3) over an INFERRED spec; qualification unknown."""


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
    output = []
    work = [('segment', 0, len(lines1), 0, len(lines2))]
    while work:
        item = work.pop()
        if item[0] == 'emit':
            output.append(item[1])
            continue
        _, lo1, hi1, lo2, hi2 = item
        prefix = []
        while lo1 < hi1 and lo2 < hi2 and lines1[lo1] == lines2[lo2]:
            prefix.append('  ' + lines1[lo1])
            lo1 += 1
            lo2 += 1
        suffix = []
        while lo1 < hi1 and lo2 < hi2 and lines1[hi1 - 1] == lines2[hi2 - 1]:
            hi1 -= 1
            hi2 -= 1
            suffix.append('  ' + lines1[hi1])
        output.extend(prefix)
        anchors = _chain(_unique_pairs(lines1, lo1, hi1, lines2, lo2, hi2))
        pending = []  # in output order, pushed reversed afterwards
        if not anchors:
            pending.extend(('emit', '- ' + lines1[i]) for i in range(lo1, hi1))
            pending.extend(('emit', '+ ' + lines2[j]) for j in range(lo2, hi2))
        else:
            a, b = lo1, lo2
            for i, j in anchors:
                pending.append(('segment', a, i, b, j))
                pending.append(('emit', '  ' + lines1[i]))
                a, b = i + 1, j + 1
            pending.append(('segment', a, hi1, b, hi2))
        pending.extend(('emit', line) for line in reversed(suffix))
        work.extend(reversed(pending))
    return output


class Solution:
    def patienceDiff(self, lines1, lines2):
        return solve(lines1, lines2)
