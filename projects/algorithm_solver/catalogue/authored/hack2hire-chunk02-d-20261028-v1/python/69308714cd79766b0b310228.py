"""Hack2Hire 69308714cd79766b0b310228 (Generate Function Profiling Events, level 2) over an INFERRED spec; qualification unknown."""


def _parse(samples):
    rows = []
    for sample in samples:
        time, _, stack = sample.partition(':')
        rows.append((int(time), stack.split('->') if stack else []))
    return rows


def solve(samples, minSamples):
    keyed = []
    open_frames = []  # (name, first sample index, first time)
    previous = []
    rows = _parse(samples)
    for index, (time, stack) in enumerate(rows):
        common = 0
        while common < len(previous) and common < len(stack) and previous[common] == stack[common]:
            common += 1
        for depth in range(len(previous) - 1, common - 1, -1):
            name, first, started = open_frames.pop()
            if index - first >= minSamples:
                keyed.append((started, 1, depth, ['start', name, started]))
                keyed.append((time, 0, -depth, ['end', name, time]))
        for depth in range(common, len(stack)):
            open_frames.append((stack[depth], index, time))
        previous = stack
    for depth, (name, first, started) in enumerate(open_frames):
        if len(rows) - first >= minSamples:
            keyed.append((started, 1, depth, ['start', name, started]))
    keyed.sort(key=lambda item: item[:3])
    return [item[3] for item in keyed]


class Solution:
    def generateEvents(self, samples, minSamples):
        return solve(samples, minSamples)
