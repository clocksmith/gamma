"""Hack2Hire 696bebd76b040fa4d120bb7a (Design Squirrel Nut Tracker) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import bisect_left

# PREFIX[L] = total capacity of levels 0..L, with level capacities 1, 2, 3, 5, 8, ...
PREFIX = []
_a, _b, _total = 1, 2, 0
while _total <= 2 * 10**14:
    _total += _a
    PREFIX.append(_total)
    _a, _b = _b, _a + _b


class SquirrelResearch:
    def __init__(self):
        self.totals = {}  # bottom-up filling and top-down removal keep the occupied levels a prefix

    def _top(self, total):
        return -1 if total == 0 else bisect_left(PREFIX, total)

    def hideNuts(self, locationId, count):
        total = self.totals.get(locationId, 0) + count
        self.totals[locationId] = total
        return self._top(total)

    def retrieveNuts(self, locationId, count):
        total = self.totals.get(locationId, 0)
        take = min(count, total)
        self.totals[locationId] = total - take
        return take

    def getHighestLevel(self, locationId):
        return self._top(self.totals.get(locationId, 0))


def solve(operation_names, argument_lists):
    if operation_names[0] != 'SquirrelResearch' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = SquirrelResearch(*argument_lists[0])
    allowed = {'hideNuts', 'retrieveNuts', 'getHighestLevel'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
