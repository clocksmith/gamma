"""Chronological native score tracker with a separately declared trace adapter."""
from bisect import bisect_left, bisect_right


class ExamTracker:
    def __init__(self):
        self.times = []
        self.prefix = [0]

    def record(self, time, score):
        self.times.append(time)
        self.prefix.append(self.prefix[-1] + score)

    def totalScore(self, startTime, endTime):
        left = bisect_left(self.times, startTime)
        right = bisect_right(self.times, endTime)
        return self.prefix[right] - self.prefix[left]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ExamTracker' or argument_lists[0] != []:
        raise ValueError('exact initial constructor required')
    instance = ExamTracker()
    result = [None]
    methods = {'record': instance.record, 'totalScore': instance.totalScore}
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        result.append(methods[name](*arguments))
    return result
