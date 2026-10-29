"""Hack2Hire 68d84fa6ae12841706c1fc81 (MinMax Queue) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class MinMaxQueue:
    def __init__(self):
        self.items, self.head = [], 0
        self.lows, self.low_head = [], 0  # non-decreasing candidates for the minimum
        self.highs, self.high_head = [], 0  # non-increasing candidates for the maximum

    def enqueue(self, val):
        self.items.append(val)
        while len(self.lows) > self.low_head and self.lows[-1] > val:
            self.lows.pop()
        self.lows.append(val)
        while len(self.highs) > self.high_head and self.highs[-1] < val:
            self.highs.pop()
        self.highs.append(val)

    def dequeue(self):
        val = self.items[self.head]
        self.head += 1
        if self.lows[self.low_head] == val:
            self.low_head += 1
        if self.highs[self.high_head] == val:
            self.high_head += 1
        return val

    def getMin(self):
        return self.lows[self.low_head]

    def getMax(self):
        return self.highs[self.high_head]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'MinMaxQueue' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = MinMaxQueue(*argument_lists[0])
    allowed = {'enqueue', 'dequeue', 'getMin', 'getMax'}
    voids = {'enqueue'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
