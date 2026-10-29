"""Original frontend 731 native class variant with a separately declared trace adapter; qualification unknown."""


class MyCalendarTwo:
    def __init__(self):
        self.bookings = []
        self.overlaps = []

    def book(self, startTime, endTime):
        for start, end in self.overlaps:
            if start < endTime and startTime < end:
                return False
        for start, end in self.bookings:
            if start < endTime and startTime < end:
                self.overlaps.append((max(start, startTime), min(end, endTime)))
        self.bookings.append((startTime, endTime))
        return True


def solve(operation_names, argument_lists):
    if operation_names[0] != 'MyCalendarTwo' or argument_lists[0] != []:
        raise ValueError('exact initial constructor required')
    instance = MyCalendarTwo()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name != 'book':
            raise ValueError('unknown method')
        result.append(instance.book(*arguments))
    return result
