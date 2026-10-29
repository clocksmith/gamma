"""Hack2Hire 67e0bdefa59c3d249d3625fe (Design Rate Limiter, variant 2 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from collections import deque


class RateLimiter:
    def __init__(self, limit, ttl):
        self.limit = limit
        self.ttl = ttl
        self.windows = {}  # client -> deque of accepted timestamps

    def allowRequest(self, clientId, timestamp):
        window = self.windows.get(clientId)
        if window is None:
            window = self.windows[clientId] = deque()
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
