"""Original frontend 729 native class variant with a separately declared trace adapter; qualification unknown."""
from bisect import bisect_right


class MyCalendar:
    def __init__(self):
        self.starts = []
        self.ends = []

    def book(self, startTime, endTime):
        index = bisect_right(self.starts, startTime)
        if index < len(self.starts) and self.starts[index] < endTime:
            return False
        if index > 0 and self.ends[index - 1] > startTime:
            return False
        self.starts.insert(index, startTime)
        self.ends.insert(index, endTime)
        return True


def solve(operation_names, argument_lists):
    if operation_names[0] != 'MyCalendar' or argument_lists[0] != []:
        raise ValueError('exact initial constructor required')
    instance = MyCalendar()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name != 'book':
            raise ValueError('unknown method')
        result.append(instance.book(*arguments))
    return result
