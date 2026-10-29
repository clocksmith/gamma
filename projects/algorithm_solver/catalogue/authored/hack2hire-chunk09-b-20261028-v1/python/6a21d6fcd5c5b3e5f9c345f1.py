"""Hack2Hire 6a21d6fcd5c5b3e5f9c345f1 (Count Singler Role Co-occurrences) over an INFERRED spec; qualification unknown."""


def solve(performances, period):
    by_singer = {}
    for singer, role, year in performances:
        by_singer.setdefault(singer, {}).setdefault(role, set()).add(int(year))
    counts = {}
    for roles in by_singer.values():
        names = sorted(roles)
        years = [sorted(roles[name]) for name in names]
        for x in range(len(names)):
            xs = years[x]
            for y in range(x + 1, len(names)):
                ys = years[y]
                i = j = 0
                while i < len(xs) and j < len(ys):
                    if abs(xs[i] - ys[j]) <= period:
                        for key in ((names[x], names[y]), (names[y], names[x])):
                            counts[key] = counts.get(key, 0) + 1
                        break
                    if xs[i] < ys[j]:
                        i += 1
                    else:
                        j += 1
    return [[a, b, str(counts[(a, b)])] for a, b in sorted(counts)]


class Solution:
    def roleCooccurrences(self, performances, period):
        return solve(performances, period)
