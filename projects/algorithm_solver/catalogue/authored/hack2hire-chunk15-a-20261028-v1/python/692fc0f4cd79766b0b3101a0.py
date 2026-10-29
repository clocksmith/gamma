"""Hack2Hire 692fc0f4cd79766b0b3101a0 (Count Intervals Covering Point) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import bisect_left, bisect_right


class IntervalCounter:
    def __init__(self, intervals):
        self.starts = sorted(interval[0] for interval in intervals)
        self.ends = sorted(interval[1] for interval in intervals)

    def count(self, x):
        return bisect_right(self.starts, x) - bisect_left(self.ends, x)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'IntervalCounter' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = IntervalCounter(*argument_lists[0])
    allowed = {'count'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
