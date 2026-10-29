"""Hack2Hire 681d10c6cc14e2629f006012 (Top K Pins) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import insort


class PinManager:
    def __init__(self):
        self.by_type = {}

    def addPin(self, pinId, score, pinType):
        insort(self.by_type.setdefault(pinType, []), (-score, pinId))

    def getTopK(self, pinType, k):
        return [pinId for _, pinId in self.by_type.get(pinType, [])[:k]]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'PinManager' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = PinManager(*argument_lists[0])
    allowed = {'addPin', 'getTopK'}
    voids = {'addPin'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
