"""Hack2Hire 6778936c775a4a31045ead0e (Windowed Key-Value Store, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from collections import OrderedDict


class WindowedKeyValueStore:
    def __init__(self, capacity, windowSize):
        self._capacity = capacity
        self._window = windowSize
        self._entries = OrderedDict()  # key -> (value, time); order = least to most recently used

    def put(self, key, val, time):
        if key in self._entries:
            del self._entries[key]
        self._entries[key] = (val, time)
        if len(self._entries) > self._capacity:
            self._entries.popitem(last=False)

    def get(self, key, time):
        entry = self._entries.get(key)
        if entry is None or time - entry[1] >= self._window:
            return -1
        self._entries.move_to_end(key)
        return entry[0]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'WindowedKeyValueStore':
        raise ValueError('exact initial constructor required')
    instance = WindowedKeyValueStore(*argument_lists[0])
    allowed = ['put', 'get']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
