"""Hack2Hire 677df76b052a260e0165706c (Design Infinite Queue with GetRandom O(1)) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class InfiniteQueue:
    def __init__(self):
        self.items = []
        self.head = 0

    def add(self, value):
        self.items.append(value)

    def poll(self):
        if self.head == len(self.items):
            return -1
        value = self.items[self.head]
        self.head += 1
        if self.head * 2 >= len(self.items) and self.head >= 1024:
            self.items = self.items[self.head:]
            self.head = 0
        return value

    def getRandom(self, r):
        size = len(self.items) - self.head
        if size == 0:
            return -1
        return self.items[self.head + r % size]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'InfiniteQueue' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = InfiniteQueue(*argument_lists[0])
    allowed = {'add', 'poll', 'getRandom'}
    voids = {'add'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
