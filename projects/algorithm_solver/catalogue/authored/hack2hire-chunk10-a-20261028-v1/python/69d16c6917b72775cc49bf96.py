"""Hack2Hire 69d16c6917b72775cc49bf96 (Design Ring Buffer) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class RingBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cells = [''] * capacity
        self.write_pos = 0
        self.read_pos = 0
        self.unread = 0

    def write(self, data):
        cap, m = self.capacity, len(data)
        start = self.write_pos
        if m > cap:  # only the last cap characters survive; they start at the shifted position
            start = (start + m - cap) % cap
            data = data[m - cap:]
        first = min(len(data), cap - start)
        self.cells[start:start + first] = data[:first]
        self.cells[0:len(data) - first] = data[first:]
        self.write_pos = (self.write_pos + m) % cap
        self.unread = min(cap, self.unread + m)  # the read pointer never moves on overwrite

    def read(self, n):
        m = min(n, self.unread)
        first = min(m, self.capacity - self.read_pos)
        out = ''.join(self.cells[self.read_pos:self.read_pos + first]) + ''.join(self.cells[0:m - first])
        self.read_pos = (self.read_pos + m) % self.capacity
        self.unread -= m
        return out


def solve(operation_names, argument_lists):
    if operation_names[0] != 'RingBuffer' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = RingBuffer(*argument_lists[0])
    allowed = {'write', 'read'}
    voids = {'write'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
