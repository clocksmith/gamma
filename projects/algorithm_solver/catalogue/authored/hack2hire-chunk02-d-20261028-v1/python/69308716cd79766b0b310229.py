"""Hack2Hire 69308716cd79766b0b310229 (Generate Function Profiling Events, level 3) over an INFERRED spec; qualification unknown."""


def _parse(samples):
    rows = []
    for sample in samples:
        time, _, stack = sample.partition(':')
        rows.append((int(time), stack.split('->') if stack else []))
    return rows


def solve(samples):
    rows = _parse(samples)
    total = {}
    for index, (time, stack) in enumerate(rows):
        for name in stack:
            if name not in total:
                total[name] = 0
        if stack and index + 1 < len(rows):
            total[stack[-1]] += rows[index + 1][0] - time
    return [[name, total[name]] for name in sorted(total)]


class Solution:
    def exclusiveTimes(self, samples):
        return solve(samples)
