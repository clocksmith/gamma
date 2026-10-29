"""Hack2Hire 67ce4e968f73eb6319edd1f0 (Design Rate Limiter, variant 1 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from collections import deque


class RateLimiter:
    def __init__(self, limit, ttl):
        self.limit = limit
        self.ttl = ttl
        self.window = deque()  # accepted timestamps inside the window

    def allowRequest(self, timestamp):
        window = self.window
        while window and window[0] <= timestamp - self.ttl:
            window.popleft()
        if len(window) < self.limit:
            window.append(timestamp)
            return True
        return False


def solve(operation_names, argument_lists):
    if operation_names[0] != 'RateLimiter' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = RateLimiter(*argument_lists[0])
    allowed = {'allowRequest'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
