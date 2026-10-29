"""Hack2Hire 69dd59d595e80ae213e5b7fc (Design A Temporal Key-Value Store, variant 2 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import bisect_right


class TemporalKVStore:
    def __init__(self):
        self.times = {}   # key -> increasing version times
        self.values = {}  # key -> values parallel to times; None marks a deletion

    def _write(self, key, value, timestamp):
        times = self.times.get(key)
        if times is None:
            self.times[key] = [timestamp]
            self.values[key] = [value]
        elif times[-1] == timestamp:
            self.values[key][-1] = value
        else:
            times.append(timestamp)
            self.values[key].append(value)

    def set(self, key, value, timestamp):
        self._write(key, value, timestamp)

    def get(self, key, timestamp):
        times = self.times.get(key)
        if times is None:
            return ''
        i = bisect_right(times, timestamp)
        if i == 0:
            return ''
        value = self.values[key][i - 1]
        return '' if value is None else value

    def remove(self, key, timestamp):
        visible = self.get(key, timestamp) != ''
        self._write(key, None, timestamp)
        return visible


def solve(operation_names, argument_lists):
    if operation_names[0] != 'TemporalKVStore' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = TemporalKVStore(*argument_lists[0])
    allowed = {'set', 'get', 'remove'}
    voids = {'set'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
