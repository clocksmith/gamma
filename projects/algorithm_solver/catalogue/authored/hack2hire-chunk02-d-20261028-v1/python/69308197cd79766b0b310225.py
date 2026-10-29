"""Hack2Hire 69308197cd79766b0b310225 (Generate Function Profiling Events, level 1) over an INFERRED spec; qualification unknown."""


def _parse(samples):
    rows = []
    for sample in samples:
        time, _, stack = sample.partition(':')
        rows.append((int(time), stack.split('->') if stack else []))
    return rows


def solve(samples):
    events = []
    previous = []
    for time, stack in _parse(samples):
        common = 0
        while common < len(previous) and common < len(stack) and previous[common] == stack[common]:
            common += 1
        for depth in range(len(previous) - 1, common - 1, -1):
            events.append(['end', previous[depth], time])
        for depth in range(common, len(stack)):
            events.append(['start', stack[depth], time])
        previous = stack
    return events


class Solution:
    def generateEvents(self, samples):
        return solve(samples)
